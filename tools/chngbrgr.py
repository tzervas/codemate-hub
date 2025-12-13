#!/usr/bin/env python3
"""chngbrgr - Generate CHANGELOG.md from tracker documents with git/PR enrichment.

This script provides the CLI interface to the modular changelog generation system.
All core functionality is in the tools/chngbrgr/ package.

Usage:
    python tools/chngbrgr.py           # Update CHANGELOG.md
    python tools/chngbrgr.py --check   # Check if up-to-date
    python tools/chngbrgr.py --preview # Print without writing
    python tools/chngbrgr.py --help    # Show all options
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from tools.chngbrgr.config import CHANGELOG_PATH
from tools.chngbrgr.git import validate_date_format
from tools.chngbrgr.render import render_changelog


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description="Generate project changelog from tracker documents with git enrichment."
    )
    parser.add_argument("--check", action="store_true", help="Fail if CHANGELOG.md is out of date")
    parser.add_argument("--date", help="Override date for changelog snapshot (YYYY-MM-DD)")
    parser.add_argument("--since", help="Only include commits since this date (YYYY-MM-DD)")
    parser.add_argument("--no-git", action="store_true", help="Skip git commit summarization")
    parser.add_argument("--only-today", action="store_true", help="Generate only today's snapshot (no history)")
    parser.add_argument("--preview", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args(argv)

    # Validate date arguments early to provide clear error messages
    try:
        validate_date_format(args.date)
        validate_date_format(args.since)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    changelog_content = render_changelog(
        date_override=args.date,
        include_git=not args.no_git,
        since_date=args.since,
        only_today=args.only_today,
    )

    if args.preview:
        print(changelog_content)
        return 0

    if args.check:
        if not CHANGELOG_PATH.exists():
            print("CHANGELOG.md is missing. Run tools/chngbrgr.py to create it.", file=sys.stderr)
            return 1
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
        if existing != changelog_content:
            print("CHANGELOG.md is out of date. Run tools/chngbrgr.py to refresh.", file=sys.stderr)
            return 1
        return 0

    CHANGELOG_PATH.write_text(changelog_content, encoding="utf-8")
    print(f"✓ CHANGELOG.md updated ({CHANGELOG_PATH})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
