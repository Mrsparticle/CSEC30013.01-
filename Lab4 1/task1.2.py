import argparse
from pathlib import Path

from model import (
    DEFAULT_ATTACK_STEPS,
    DEFAULT_EPS,
    add_common_args,
    ensure_dir,
    get_mnist_loaders,
    save_attack_examples,
    set_seed,
    train_clean_model,
    untargeted_multistep_fgsm,
)
import torch


def main():
    parser = argparse.ArgumentParser(description="Task 3.1: untargeted multi-step FGSM attack.")
    add_common_args(parser)
    parser.add_argument("--eps", type=float, default=DEFAULT_EPS)
    parser.add_argument("--steps", type=int, default=DEFAULT_ATTACK_STEPS)
    parser.add_argument("--foreground-threshold", type=float, default=0.3)
    parser.add_argument("--full-image", action="store_true",
                        help="Perturb every pixel instead of only the digit foreground.")
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)
    print(f"Using {device} device")
    print(
        f"Untargeted attack: eps={args.eps}, steps={args.steps}, "
        f"foreground_only={not args.full_image}"
    )
    output_dir = ensure_dir(Path(args.output_dir) / "task31_untargeted")

    def on_step(row, examples):
        print(
            f"step {row['step']}: fooled/base={row['fooled']}/{row['base_correct']}, "
            f"error_rate={row['error_rate']:.4f}, "
            f"remaining_accuracy={row['remaining_accuracy']:.4f}"
        )
        output_path = output_dir / f"task31_step{row['step']:02d}.png"
        saved = save_attack_examples(
            examples,
            output_path,
            f"Task 3.1 Untargeted FGSM Step {row['step']}",
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
    _, _, clean_accuracy = untargeted_multistep_fgsm(
        model,
        device,
        test_loader,
        eps=args.eps,
        steps=args.steps,
        batch_size=args.test_batch_size,
        on_step=on_step,
        foreground_only=not args.full_image,
        foreground_threshold=args.foreground_threshold,
    )

    print(f"Clean accuracy before attack = {clean_accuracy:.4f}")
    print(f"All step images saved under {output_dir}")


if __name__ == "__main__":
    main()
