"""Command line interface for generation and rendering."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import load_config
from .logging_setup import setup_logging
from .pipeline import ReelPipeline


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""

    parser = argparse.ArgumentParser(prog="did_you_know_reels", description="Generate did-you-know reel drafts and videos.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML.")
    parser.add_argument("--env-file", default=".env", help="Path to .env file.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a draft without rendering video.")
    generate.add_argument("--topic", required=True, help="Topic or niche for the reel.")
    generate.add_argument("--count", type=int, default=1, help="Number of variants to generate.")
    generate.add_argument("--output", default="./output", help="Output directory.")
    generate.add_argument("--dry-run", action="store_true", help="Generate files without rendering.")

    render = subparsers.add_parser("render", help="Render a video from an existing script JSON.")
    render.add_argument("--input", required=True, help="Path to a generated script JSON file.")
    render.add_argument("--output", default="./output", help="Output directory.")
    render.add_argument("--dry-run", action="store_true", help="Export render plan only.")

    run = subparsers.add_parser("run", help="Generate and render a full pipeline output.")
    run.add_argument("--topic", required=True, help="Topic or niche for the reel.")
    run.add_argument("--count", type=int, default=1, help="Number of variants to generate.")
    run.add_argument("--output", default="./output", help="Output directory.")
    run.add_argument("--dry-run", action="store_true", help="Generate without final MP4 render.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config, args.env_file)
    setup_logging(config.app["log_file"], config.app.get("log_level", "INFO"))
    pipeline = ReelPipeline(config)
    output_root = str(Path(args.output))

    if args.command == "generate":
        for index in range(1, args.count + 1):
            pipeline.generate_draft(topic=args.topic, output_root=output_root, index=index, dry_run=args.dry_run)
        return 0

    if args.command == "render":
        draft = pipeline.load_draft_from_script(args.input)
        pipeline.render_draft(draft=draft, output_root=output_root, dry_run=args.dry_run)
        return 0

    if args.command == "run":
        for index in range(1, args.count + 1):
            draft, _ = pipeline.generate_draft(topic=args.topic, output_root=output_root, index=index, dry_run=args.dry_run)
            pipeline.render_draft(draft=draft, output_root=output_root, dry_run=args.dry_run)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
