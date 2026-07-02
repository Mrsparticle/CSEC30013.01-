import argparse
from pathlib import Path

import torch

from model import (
    DEFAULT_ATTACK_STEPS,
    DEFAULT_EPS,
    TARGET_LABEL,
    add_common_args,
    ensure_dir,
    get_mnist_loaders,
    save_attack_examples,
    set_seed,
    targeted_multistep_fgsm,
    train_clean_model,
)


def main():
    parser = argparse.ArgumentParser(description="Task 3.2: targeted multi-step FGSM attack.")
    add_common_args(parser)
    parser.add_argument("--eps", type=float, default=DEFAULT_EPS)
    parser.add_argument("--steps", type=int, default=DEFAULT_ATTACK_STEPS)
    parser.add_argument("--target-label", type=int, default=TARGET_LABEL)
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)
    print(f"Using {device} device")
    print(f"Targeted attack: eps={args.eps}, steps={args.steps}, target={args.target_label}")
    output_dir = ensure_dir(Path(args.output_dir) / "task32_targeted")

    def on_step(row, examples):
        print(
            f"step {row['step']}: success/total={row['success']}/{row['total']}, "
            f"success_rate={row['success_rate']:.4f}"
        )
        output_path = output_dir / f"task32_step{row['step']:02d}.png"
        saved = save_attack_examples(
            examples,
            output_path,
            f"Task 3.2 Targeted FGSM Step {row['step']} Target {args.target_label}",
        )
        if saved:
            print(f"saved examples: {saved}")

    train_loader, test_loader = get_mnist_loaders(
        args.data_dir,
        args.batch_size,
        args.test_batch_size,
        args.train_size,
        args.test_size,
        args.seed,
    )
    model = train_clean_model(device, train_loader, test_loader, args.epochs, args.lr)
    targeted_multistep_fgsm(
        model,
        device,
        test_loader,
        eps=args.eps,
        steps=args.steps,
        target_label=args.target_label,
        batch_size=args.test_batch_size,
        on_step=on_step,
    )
    print(f"All step images saved under {output_dir}")


if __name__ == "__main__":
    main()
