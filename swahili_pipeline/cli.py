"""Command-line interface for the Swahili Data Pipeline."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .core import SwahiliPipeline, PipelineConfig, read_jsonl, read_text_files, write_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swahili-pipeline",
        description="Clean and filter Swahili text data for LLM training",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input file (.jsonl) or directory (.txt files)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output JSONL file",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=10,
        help="Minimum document length (characters)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=10000,
        help="Maximum document length (characters)",
    )
    parser.add_argument(
        "--min-swahili-ratio",
        type=float,
        default=0.7,
        help="Minimum Swahili word ratio (0.0-1.0)",
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Disable deduplication",
    )
    parser.add_argument(
        "--no-fix-encoding",
        action="store_true",
        help="Disable encoding fix",
    )
    parser.add_argument(
        "--no-remove-pii",
        action="store_true",
        help="Disable PII removal",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print processing statistics",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Validate input
    if not args.input.exists():
        print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
        return 1

    # Build config
    config = PipelineConfig(
        min_length=args.min_length,
        max_length=args.max_length,
        min_swahili_ratio=args.min_swahili_ratio,
        deduplicate=not args.no_deduplicate,
        fix_encoding=not args.no_fix_encoding,
        remove_pii=not args.no_remove_pii,
    )

    pipeline = SwahiliPipeline(config)

    # Read input
    if args.input.is_file() and args.input.suffix == ".jsonl":
        docs = read_jsonl(args.input)
        input_type = "jsonl"
    elif args.input.is_dir():
        docs = read_text_files(args.input)
        input_type = "directory"
    else:
        print(f"Error: Input must be .jsonl file or directory", file=sys.stderr)
        return 1

    # Process
    processed = pipeline.process_batch(docs)

    # Write output
    count = write_jsonl(processed, args.output)

    # Stats
    if args.stats:
        print(f"Input type: {input_type}")
        print(f"Output: {args.output}")
        print(f"Documents written: {count}")
        print(f"Config: min_len={config.min_length}, max_len={config.max_length}, "
              f"swahili_ratio>={config.min_swahili_ratio}")

    return 0


if __name__ == "__main__":
    sys.exit(main())