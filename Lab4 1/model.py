import argparse
import os
import random
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mplconfig")

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import datasets, transforms


TARGET_LABEL = 1
DEFAULT_EPS = 0.05
DEFAULT_ATTACK_STEPS = 10
DEFAULT_SEED = 42


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def set_seed(seed=DEFAULT_SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_mnist_loaders(data_dir="./data", batch_size=128, test_batch_size=256,
                      train_size=None, test_size=None, seed=DEFAULT_SEED):
    transform = transforms.ToTensor()
    train_dataset = datasets.MNIST(data_dir, train=True, download=False, transform=transform)
    test_dataset = datasets.MNIST(data_dir, train=False, download=False, transform=transform)

    if train_size is not None and train_size < len(train_dataset):
        train_dataset = Subset(train_dataset, list(range(train_size)))
    if test_size is not None and test_size < len(test_dataset):
        test_dataset = Subset(test_dataset, list(range(test_size)))

    generator = torch.Generator()
    generator.manual_seed(seed)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, generator=generator)
    test_loader = DataLoader(test_dataset, batch_size=test_batch_size, shuffle=False)
    return train_loader, test_loader


def train_one_epoch(model, device, train_loader, optimizer, epoch):
    model.train()
    loss_value = 0.0
    for data, target in train_loader:
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        loss_value = loss.item()
    print(f"Train Epoch: {epoch}\tLoss: {loss_value:.6f}")
    return loss_value


def evaluate_clean(model, device, test_loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            pred = model(data).argmax(1)
            correct += pred.eq(target).sum().item()
            total += target.numel()
    accuracy = correct / total
    print(f"Test Accuracy = {correct} / {total} = {accuracy:.4f}")
    return accuracy, correct, total


def train_clean_model(device, train_loader, test_loader, epochs=2, lr=0.001):
    model = Net().to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    for epoch in range(1, epochs + 1):
        train_one_epoch(model, device, train_loader, optimizer, epoch)
        evaluate_clean(model, device, test_loader)
    return model


def fgsm_step(model, data, label, eps, targeted=False, perturb_mask=None):
    adv_data = data.detach().clone()
    adv_data.requires_grad_(True)
    output = model(adv_data)
    loss = F.nll_loss(output, label)
    model.zero_grad()
    loss.backward()
    signed_grad = adv_data.grad.sign()
    if perturb_mask is not None:
        signed_grad = signed_grad * perturb_mask
    if targeted:
        adv_data = adv_data - eps * signed_grad
    else:
        adv_data = adv_data + eps * signed_grad
    return adv_data.detach().clamp(0, 1)


def foreground_mask(data, threshold=0.3, dilation=3):
    mask = (data > threshold).float()
    if dilation > 1:
        mask = F.max_pool2d(mask, kernel_size=dilation, stride=1, padding=dilation // 2)
    return mask


def untargeted_multistep_fgsm(model, device, test_loader, eps=DEFAULT_EPS,
                              steps=DEFAULT_ATTACK_STEPS, collect_examples=8,
                              batch_size=256, on_step=None,
                              foreground_only=True, foreground_threshold=0.3):
    model.eval()
    original_batches = []
    label_batches = []
    pred_batches = []
    correct_before = 0
    total = 0

    for data, target in test_loader:
        data, target = data.to(device), target.to(device)
        with torch.no_grad():
            initial_pred = model(data).argmax(1)
        mask = initial_pred.eq(target)
        correct_before += mask.sum().item()
        total += target.numel()
        if not mask.any():
            continue

        original_batches.append(data[mask].detach().cpu())
        label_batches.append(target[mask].detach().cpu())
        pred_batches.append(initial_pred[mask].detach().cpu())

    if not original_batches:
        return [], (None, None, None, None, None), 0.0

    originals = torch.cat(original_batches, dim=0)
    labels = torch.cat(label_batches, dim=0)
    clean_preds = torch.cat(pred_batches, dim=0)
    adv = originals.clone()
    masks = foreground_mask(originals, foreground_threshold) if foreground_only else None

    results = []
    last_examples = (None, None, None, None, None)
    for step in range(1, steps + 1):
        adv_preds = []
        for start in range(0, adv.size(0), batch_size):
            end = min(start + batch_size, adv.size(0))
            batch = adv[start:end].to(device)
            batch_labels = labels[start:end].to(device)
            batch_mask = masks[start:end].to(device) if masks is not None else None
            adv_batch = fgsm_step(
                model,
                batch,
                batch_labels,
                eps,
                targeted=False,
                perturb_mask=batch_mask,
            )
            adv[start:end] = adv_batch.cpu()
            with torch.no_grad():
                pred = model(adv_batch).argmax(1)
            adv_preds.append(pred.detach().cpu())

        adv_pred = torch.cat(adv_preds, dim=0)
        fooled = adv_pred.ne(labels).sum().item()
        error_rate = fooled / correct_before if correct_before else 0.0
        remaining_acc = 1.0 - error_rate
        row = {
            "step": step,
            "fooled": fooled,
            "base_correct": correct_before,
            "error_rate": error_rate,
            "remaining_accuracy": remaining_acc,
        }
        results.append(row)
        example_indices = select_example_indices(labels, adv_pred, collect_examples)
        last_examples = (
            originals[example_indices],
            adv[example_indices],
            labels[example_indices],
            adv_pred[example_indices],
            clean_preds[example_indices],
        )
        if on_step:
            on_step(row, last_examples)

    clean_accuracy = correct_before / total if total else 0.0
    return results, last_examples, clean_accuracy


def targeted_multistep_fgsm(model, device, test_loader, eps=DEFAULT_EPS,
                            steps=DEFAULT_ATTACK_STEPS, target_label=TARGET_LABEL,
                            collect_examples=8, batch_size=256, on_step=None):
    model.eval()
    original_batches = []
    label_batches = []
    pred_batches = []
    total = 0

    for data, label in test_loader:
        data, label = data.to(device), label.to(device)
        total += label.numel()
        with torch.no_grad():
            initial_pred = model(data).argmax(1)
        original_batches.append(data.detach().cpu())
        label_batches.append(label.detach().cpu())
        pred_batches.append(initial_pred.detach().cpu())

    if not original_batches:
        return [], (None, None, None, None, None)

    originals = torch.cat(original_batches, dim=0)
    labels = torch.cat(label_batches, dim=0)
    clean_preds = torch.cat(pred_batches, dim=0)
    adv = originals.clone()
    target_tensor = torch.full_like(labels, target_label)

    results = []
    last_examples = (None, None, None, None, None)
    for step in range(1, steps + 1):
        adv_preds = []
        for start in range(0, adv.size(0), batch_size):
            end = min(start + batch_size, adv.size(0))
            batch = adv[start:end].to(device)
            batch_target = target_tensor[start:end].to(device)
            adv_batch = fgsm_step(model, batch, batch_target, eps, targeted=True)
            adv[start:end] = adv_batch.cpu()
            with torch.no_grad():
                pred = model(adv_batch).argmax(1)
            adv_preds.append(pred.detach().cpu())

        adv_pred = torch.cat(adv_preds, dim=0)
        success = adv_pred.eq(target_label).sum().item()
        row = {
            "step": step,
            "success": success,
            "total": total,
            "success_rate": success / total if total else 0.0,
        }
        results.append(row)
        example_indices = select_example_indices(labels, adv_pred, collect_examples, target_label)
        last_examples = (
            originals[example_indices],
            adv[example_indices],
            labels[example_indices],
            adv_pred[example_indices],
            clean_preds[example_indices],
        )
        if on_step:
            on_step(row, last_examples)

    return results, last_examples


def add_natural_trigger(data):
    triggered = data.clone()
    coords = [
        (22, 24, 0.85),
        (23, 23, 0.95),
        (24, 22, 0.95),
        (25, 21, 0.85),
        (26, 20, 0.65),
        (23, 24, 0.45),
        (24, 23, 0.45),
        (25, 22, 0.45),
    ]
    for row, col, value in coords:
        patch_value = torch.as_tensor(value, dtype=triggered.dtype, device=triggered.device)
        triggered[..., row, col] = torch.maximum(triggered[..., row, col], patch_value)
    return triggered.clamp(0, 1)


class BackdoorDataset(Dataset):
    def __init__(self, dataset, poison_rate=0.01, target_label=TARGET_LABEL, seed=DEFAULT_SEED):
        self.dataset = dataset
        self.target_label = target_label
        labels = np.array([int(dataset[index][1]) for index in range(len(dataset))])
        candidates = np.where(labels != target_label)[0]
        poison_count = max(1, int(len(dataset) * poison_rate))
        rng = np.random.default_rng(seed)
        self.poison_indices = set(rng.choice(candidates, size=poison_count, replace=False).tolist())

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        data, label = self.dataset[index]
        if index in self.poison_indices:
            data = add_natural_trigger(data)
            label = self.target_label
        return data, label


def get_backdoor_train_loader(data_dir="./data", batch_size=128, train_size=None,
                              poison_rate=0.01, target_label=TARGET_LABEL,
                              seed=DEFAULT_SEED):
    transform = transforms.ToTensor()
    train_dataset = datasets.MNIST(data_dir, train=True, download=False, transform=transform)
    if train_size is not None and train_size < len(train_dataset):
        train_dataset = Subset(train_dataset, list(range(train_size)))
    poison_dataset = BackdoorDataset(train_dataset, poison_rate, target_label, seed)
    generator = torch.Generator()
    generator.manual_seed(seed)
    loader = DataLoader(poison_dataset, batch_size=batch_size, shuffle=True, generator=generator)
    return loader, len(poison_dataset.poison_indices)


def train_backdoor_model(device, train_loader, test_loader, epochs=5, lr=0.001,
                         target_label=TARGET_LABEL, on_epoch=None):
    model = Net().to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    history = []
    for epoch in range(1, epochs + 1):
        train_one_epoch(model, device, train_loader, optimizer, epoch)
        clean_acc, _, _ = evaluate_clean(model, device, test_loader)
        asr = evaluate_backdoor_success(model, device, test_loader, target_label)
        row = {"epoch": epoch, "clean_accuracy": clean_acc, "asr": asr}
        history.append(row)
        print(f"Backdoor ASR = {asr:.4f}")
        if on_epoch:
            on_epoch(row, model)
    return model, history


def evaluate_backdoor_success(model, device, test_loader, target_label=TARGET_LABEL):
    model.eval()
    success = 0
    total = 0
    with torch.no_grad():
        for data, _ in test_loader:
            data = add_natural_trigger(data.to(device))
            pred = model(data).argmax(1)
            success += pred.eq(target_label).sum().item()
            total += pred.numel()
    return success / total if total else 0.0


def predict_images(model, device, images, batch_size=256):
    model.eval()
    preds = []
    with torch.no_grad():
        for start in range(0, images.size(0), batch_size):
            batch = images[start:start + batch_size].to(device)
            preds.append(model(batch).argmax(1).detach().cpu())
    return torch.cat(preds, dim=0)


def select_example_indices(labels, preds, count=8, target_label=None):
    labels = labels.cpu()
    preds = preds.cpu()
    chosen = []
    if target_label is None:
        priority = torch.nonzero(preds.ne(labels), as_tuple=False).flatten().tolist()
    else:
        priority = torch.nonzero(preds.eq(target_label), as_tuple=False).flatten().tolist()
    fallback = list(range(labels.numel()))

    seen_labels = set()
    for index in priority + fallback:
        label = int(labels[index])
        if label in seen_labels and len(seen_labels) < 10:
            continue
        chosen.append(index)
        seen_labels.add(label)
        if len(chosen) >= count:
            return torch.tensor(chosen, dtype=torch.long)

    for index in priority + fallback:
        if index not in chosen:
            chosen.append(index)
        if len(chosen) >= count:
            break
    return torch.tensor(chosen, dtype=torch.long)


def save_attack_examples(examples, output_path, title):
    originals, adversarials, labels, adv_preds, clean_preds = examples
    if originals is None or adversarials is None:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = min(8, originals.size(0))
    plt.figure(figsize=(count * 1.8, 3.8))
    for index in range(count):
        plt.subplot(2, count, index + 1)
        plt.imshow(originals[index].squeeze().numpy(), cmap="gray", vmin=0, vmax=1)
        plt.axis("off")
        plt.title(f"y={int(labels[index])}\npred={int(clean_preds[index])}", fontsize=8)
        plt.subplot(2, count, count + index + 1)
        plt.imshow(adversarials[index].squeeze().numpy(), cmap="gray", vmin=0, vmax=1)
        plt.axis("off")
        plt.title(f"y={int(labels[index])}\npred={int(adv_preds[index])}", fontsize=8)
    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()
    return output_path


def print_attack_table(results, mode):
    if mode == "untargeted":
        print("step\tfooled/base\terror_rate\tremaining_accuracy")
        for row in results:
            print(
                f"{row['step']}\t{row['fooled']}/{row['base_correct']}"
                f"\t{row['error_rate']:.4f}\t{row['remaining_accuracy']:.4f}"
            )
    elif mode == "targeted":
        print("step\tsuccess/total\tsuccess_rate")
        for row in results:
            print(f"{row['step']}\t{row['success']}/{row['total']}\t{row['success_rate']:.4f}")
    else:
        raise ValueError(f"unknown mode: {mode}")


def add_common_args(parser):
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--test-batch-size", type=int, default=256)
    parser.add_argument("--train-size", type=int, default=20000)
    parser.add_argument("--test-size", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-dir", default="outputs")
    return parser


def main():
    parser = argparse.ArgumentParser(description="Train and test the clean MNIST model.")
    add_common_args(parser)
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)
    print(f"Using {device} device")
    train_loader, test_loader = get_mnist_loaders(
        args.data_dir,
        args.batch_size,
        args.test_batch_size,
        args.train_size,
        args.test_size,
        args.seed,
    )
    train_clean_model(device, train_loader, test_loader, args.epochs, args.lr)


if __name__ == "__main__":
    main()
