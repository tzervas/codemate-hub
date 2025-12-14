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
import re
import sys
from typing import List, Optional

from tools.chngbrgr.config import CHANGELOG_PATH
from tools.chngbrgr.git import validate_date_format
from tools.chngbrgr.render import render_changelog


def normalize_for_comparison(text: str) -> str:
    """Normalize changelog text for comparison, removing volatile fields.

    Removes content that varies between environments but doesn't represent
    actual documentation changes:
    - Last updated date in header (timezone differences)
    - Snapshot date headers (timezone differences)
    - Git commit/PR enrichment sections (shallow clone differences)
    - Progress Log sections (git-derived)

    The tracker content hashes (<!-- hash:xxx -->) capture real doc changes.

    Args:
        text: Raw changelog text

    Returns:
        Normalized text suitable for content comparison
    """
    # Remove "Last updated: YYYY-MM-DD" line
    text = re.sub(r"_Last updated: \d{4}-\d{2}-\d{2}_\n?", "", text)
    # Normalize snapshot headers to ignore date (keep structure)
    text = re.sub(r"## Snapshot \d{4}-\d{2}-\d{2}", "## Snapshot", text)
    # Remove Progress Log sections entirely (git-derived, varies with history depth)
    text = re.sub(r"Progress Log:.*?(?=\n####|\n###|\n##|\Z)", "", text, flags=re.DOTALL)
    # Remove any "Recent Commits" or "Recent Changes" sections (git-derived)
    text = re.sub(r"### Recent (?:Commits|Changes).*?(?=\n###|\n##|\Z)", "", text, flags=re.DOTALL)
    # Normalize multiple blank lines to single
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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
        # Compare normalized content to ignore timezone-sensitive date fields
        # The actual tracker content hashes (<!-- hash:xxx -->) capture real changes
        if normalize_for_comparison(existing) != normalize_for_comparison(changelog_content):
            print("CHANGELOG.md is out of date. Run tools/chngbrgr.py to refresh.", file=sys.stderr)
            return 1
        return 0

    CHANGELOG_PATH.write_text(changelog_content, encoding="utf-8")
    print(f"✓ CHANGELOG.md updated ({CHANGELOG_PATH})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
