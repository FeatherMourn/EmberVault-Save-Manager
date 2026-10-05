"""Minimal read-only command-line world library."""

from __future__ import annotations

import argparse
import json

from .library import list_worlds
from .world_model import SaveSource


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="embervault-save-manager")
    parser.add_argument("root", help="save source directory")
    parser.add_argument("--source-id", default="local")
    parser.add_argument("--source-kind", default="local")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = SaveSource(args.source_id, args.source_kind, args.root, False, "ready")
    rows = list_worlds((source,))
    if args.as_json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            print(f"{row['display_name']} | slot {row['slot']} | {row['health']} | {row['root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
