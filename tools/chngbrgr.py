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
import logging
import os
import re
import sys
from typing import List, Optional

from tools.chngbrgr.config import CHANGELOG_PATH
from tools.chngbrgr.git import validate_date_format
from tools.chngbrgr.render import render_changelog

# Configure logging - DEBUG level when DEBUG env var is set
log_level = logging.DEBUG if os.environ.get("DEBUG") else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def normalize_for_comparison(text: str, debug: bool = False) -> str:
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
        debug: Log transformation steps

    Returns:
        Normalized text suitable for content comparison
    """
    original_len = len(text)
    
    # Remove "Last updated: YYYY-MM-DD" line
    text = re.sub(r"_Last updated: \d{4}-\d{2}-\d{2}_\n?", "", text)
    if debug:
        logger.debug(f"After date header removal: {len(text)} chars (was {original_len})")
    
    # Normalize snapshot headers to ignore date (keep structure)
    text = re.sub(r"## Snapshot \d{4}-\d{2}-\d{2}", "## Snapshot", text)
    if debug:
        logger.debug(f"After snapshot normalization: {len(text)} chars")
    
    # Remove hash comment markers from tracker headers (<!-- hash:xxx -->)
    # These are content fingerprints that vary between generator runs
    text = re.sub(r" <!-- hash:[a-f0-9]+ -->", "", text)
    if debug:
        logger.debug(f"After hash marker removal: {len(text)} chars")
    
    # Remove "unchanged since" markers that appear in freshly generated content
    # _(unchanged since YYYY-MM-DD)_ on its own line
    text = re.sub(r"\n_\(unchanged since \d{4}-\d{2}-\d{2}\)_", "", text)
    if debug:
        logger.debug(f"After unchanged marker removal: {len(text)} chars")
    
    # Remove Progress Log sections entirely (git-derived, varies with history depth)
    text = re.sub(r"Progress Log:.*?(?=\n####|\n###|\n##|\Z)", "", text, flags=re.DOTALL)
    if debug:
        logger.debug(f"After Progress Log removal: {len(text)} chars")
    
    # Remove any "Recent Commits" or "Recent Changes" sections (git-derived)
    text = re.sub(r"### Recent (?:Commits|Changes).*?(?=\n###|\n##|\Z)", "", text, flags=re.DOTALL)
    if debug:
        logger.debug(f"After Recent sections removal: {len(text)} chars")
    
    # Strip trailing whitespace from each line (hash removal can leave orphan spaces)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    
    # Normalize multiple blank lines to single
    text = re.sub(r"\n{3,}", "\n\n", text)
    result = text.strip()
    
    if debug:
        logger.debug(f"Final normalized length: {len(result)} chars")
    
    return result


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
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

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
        suppress_duplicates=not args.check,  # Disable for --check to get full content
    )

    if args.preview:
        print(changelog_content)
        return 0

    if args.check:
        if not CHANGELOG_PATH.exists():
            print("CHANGELOG.md is missing. Run tools/chngbrgr.py to create it.", file=sys.stderr)
            return 1
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
        
        logger.debug(f"Existing changelog: {len(existing)} chars")
        logger.debug(f"Generated changelog: {len(changelog_content)} chars")
        
        # Compare normalized content to ignore timezone-sensitive date fields
        # The actual tracker content hashes (<!-- hash:xxx -->) capture real changes
        debug_mode = args.debug or os.environ.get("DEBUG")
        norm_existing = normalize_for_comparison(existing, debug=debug_mode)
        norm_generated = normalize_for_comparison(changelog_content, debug=debug_mode)
        
        logger.debug(f"Normalized existing: {len(norm_existing)} chars")
        logger.debug(f"Normalized generated: {len(norm_generated)} chars")
        
        if norm_existing != norm_generated:
            # Find and report first difference for debugging
            for i, (a, b) in enumerate(zip(norm_existing, norm_generated)):
                if a != b:
                    logger.debug(f"First difference at position {i}:")
                    logger.debug(f"  Existing char: {repr(a)}")
                    logger.debug(f"  Generated char: {repr(b)}")
                    logger.debug(f"  Context existing: {repr(norm_existing[max(0,i-30):i+30])}")
                    logger.debug(f"  Context generated: {repr(norm_generated[max(0,i-30):i+30])}")
                    break
            else:
                # Length mismatch
                shorter = min(len(norm_existing), len(norm_generated))
                logger.debug(f"Length mismatch at position {shorter}")
                if len(norm_existing) > shorter:
                    logger.debug(f"  Extra in existing: {repr(norm_existing[shorter:shorter+50])}")
                else:
                    logger.debug(f"  Extra in generated: {repr(norm_generated[shorter:shorter+50])}")
            
            print("CHANGELOG.md is out of date. Run tools/chngbrgr.py to refresh.", file=sys.stderr)
            return 1
        return 0

    CHANGELOG_PATH.write_text(changelog_content, encoding="utf-8")
    print(f"✓ CHANGELOG.md updated ({CHANGELOG_PATH})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
