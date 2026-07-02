import argparse
from pathlib import Path

import torch

from model import (
    TARGET_LABEL,
    add_common_args,
    add_natural_trigger,
    ensure_dir,
    get_backdoor_train_loader,
    get_mnist_loaders,
    predict_images,
    save_attack_examples,
    set_seed,
    train_backdoor_model,
)


def collect_trigger_examples(model, test_loader, device, count=8):
    originals = []
    triggered = []
    labels = []
    for data, label in test_loader:
        data = data.to(device)
        need = count - sum(batch.size(0) for batch in originals)
        originals.append(data[:need].detach().cpu())
        triggered.append(add_natural_trigger(data[:need]).detach().cpu())
        labels.append(label[:need].detach().cpu())
        if sum(batch.size(0) for batch in originals) >= count:
            break
    originals = torch.cat(originals, 0)
    triggered = torch.cat(triggered, 0)
    labels = torch.cat(labels, 0)
    clean_preds = predict_images(model, device, originals)
    trigger_preds = predict_images(model, device, triggered)
    return originals, triggered, labels, trigger_preds, clean_preds


def main():
    parser = argparse.ArgumentParser(description="Task 4: backdoor attack on MNIST.")
    add_common_args(parser)
    parser.set_defaults(epochs=5)
    parser.add_argument("--poison-rate", type=float, default=0.01)
    parser.add_argument("--target-label", type=int, default=TARGET_LABEL)
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)
    print(f"Using {device} device")
    print(f"Backdoor attack: eta={args.poison_rate}, target={args.target_label}")

    train_loader, poison_count = get_backdoor_train_loader(
        args.data_dir,
        args.batch_size,
        args.train_size,
        args.poison_rate,
        args.target_label,
        args.seed,
    )
    _, test_loader = get_mnist_loaders(
        args.data_dir,
        args.batch_size,
        args.test_batch_size,
        args.train_size,
        args.test_size,
        args.seed,
    )
    print(f"Poisoned samples = {poison_count}")
    output_dir = ensure_dir(Path(args.output_dir) / "task4_backdoor")

    def on_epoch(row, model):
        print(
            f"epoch {row['epoch']}: clean_accuracy={row['clean_accuracy']:.4f}, "
            f"backdoor_asr={row['asr']:.4f}"
        )
        examples = collect_trigger_examples(model, test_loader, device)
        output_path = output_dir / f"task4_epoch{row['epoch']:02d}.png"
        saved = save_attack_examples(
            examples,
            output_path,
            f"Task 4 Backdoor Trigger Epoch {row['epoch']}",
        )
        if saved:
            print(f"saved examples: {saved}")

    _, history = train_backdoor_model(
        device,
        train_loader,
        test_loader,
        epochs=args.epochs,
        lr=args.lr,
        target_label=args.target_label,
        on_epoch=on_epoch,
    )

    print("epoch\tclean_accuracy\tbackdoor_asr")
    for row in history:
        print(f"{row['epoch']}\t{row['clean_accuracy']:.4f}\t{row['asr']:.4f}")
    print(f"All epoch images saved under {output_dir}")


if __name__ == "__main__":
    main()
