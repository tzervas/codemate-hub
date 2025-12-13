"""Changelog and snapshot rendering.

This module handles:
- Building tracker sections with hash-based duplicate suppression
- Building git/PR enriched sections
- Rendering complete changelog snapshots
- Managing changelog history and updates
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from tools.chngbrgr.config import (
    CHANGE_TYPE_PREFIXES,
    CHANGELOG_PATH,
    CONTRIBUTOR_AI,
    CONTRIBUTOR_BOT,
    CONTRIBUTOR_HUMAN,
    SNAPSHOT_PREFIX,
)
from tools.chngbrgr.git import classify_areas, get_commits_since, get_merge_prs_since
from tools.chngbrgr.models import CommitInfo
from tools.chngbrgr.trackers import group_trackers


def strip_header(changelog_text: str) -> str:
    """Remove the title/last-updated preamble from changelog.

    Args:
        changelog_text: Full changelog text

    Returns:
        Changelog text without header
    """
    if not changelog_text:
        return ""

    lines = changelog_text.splitlines()
    idx = 0

    if idx < len(lines) and lines[idx].startswith("# Changelog"):
        idx += 1
    if idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and lines[idx].startswith("_Last updated:"):
        idx += 1
    if idx < len(lines) and not lines[idx].strip():
        idx += 1

    return "\n".join(lines[idx:]).strip()


def existing_snapshot_dates(history: str) -> List[str]:
    """Extract all snapshot dates from changelog history.

    Args:
        history: Changelog history text (without header)

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    # Build regex from SNAPSHOT_PREFIX constant to stay aligned
    # Note: SNAPSHOT_PREFIX includes trailing space, so use rstrip() for regex escaping
    escaped_prefix = re.escape(SNAPSHOT_PREFIX.rstrip())
    pattern = re.compile(rf"^{escaped_prefix} ?(\d{{4}}-\d{{2}}-\d{{2}})$")
    dates: List[str] = []
    for line in history.splitlines():
        match = pattern.match(line.strip())
        if match:
            dates.append(match.group(1))
    return dates


def remove_snapshot(history: str, target_date: str) -> str:
    """Remove a specific snapshot from history.

    Args:
        history: Changelog history text
        target_date: Date of snapshot to remove (YYYY-MM-DD)

    Returns:
        History text with target snapshot removed
    """
    if not history:
        return ""

    lines = history.splitlines()
    target_heading = f"{SNAPSHOT_PREFIX}{target_date}"
    output: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == target_heading:
            i += 1
            while i < len(lines) and not lines[i].startswith(SNAPSHOT_PREFIX):
                i += 1
            continue
        output.append(line)
        i += 1

    return "\n".join(output).strip()


# =============================================================================
# Git Section Building
# =============================================================================


def build_git_section(
    commits: List[CommitInfo],
    prs: List[Tuple[int, str]],
) -> List[str]:
    """Build enriched git section with PRs, contributors, areas, and change types.

    Args:
        commits: List of CommitInfo objects
        prs: List of (pr_number, title) tuples

    Returns:
        List of markdown lines for git section
    """
    lines: List[str] = []

    if not commits and not prs:
        return lines

    # PRs section
    if prs:
        lines.append("### Pull Requests")
        lines.append("")
        for pr_num, title in prs:
            lines.append(f"- #{pr_num}: {title}")
        lines.append("")

    if not commits:
        return lines

    # Group commits by contributor type
    by_contributor_type: Dict[str, List[CommitInfo]] = defaultdict(list)
    for commit in commits:
        by_contributor_type[commit.contributor_type].append(commit)

    # Process each contributor type section
    contributor_order = [CONTRIBUTOR_HUMAN, CONTRIBUTOR_AI, CONTRIBUTOR_BOT]

    for contrib_type in contributor_order:
        type_commits = by_contributor_type.get(contrib_type, [])
        if not type_commits:
            continue

        # Section header with emoji
        emoji = {"Human": "👤", "AI/Agent": "🤖", "Bot": "⚙️"}.get(contrib_type, "")
        lines.append(f"### {emoji} {contrib_type} Changes")
        lines.append("")

        # Group by change type within contributor type
        by_type: Dict[str, List[CommitInfo]] = defaultdict(list)
        for commit in type_commits:
            by_type[commit.change_type].append(commit)

        for change_type in list(CHANGE_TYPE_PREFIXES.values()) + ["Other"]:
            if change_type in by_type:
                lines.append(f"**{change_type}**")
                for commit in by_type[change_type]:
                    pr_ref = f" (#{commit.pr_number})" if commit.pr_number else ""
                    lines.append(f"- {commit.sha} {commit.subject}{pr_ref}")
                lines.append("")

    # Contributors summary (all types combined)
    authors_by_type: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for commit in commits:
        authors_by_type[commit.contributor_type][commit.author] += 1

    if any(authors_by_type.values()):
        lines.append("### Contributors")
        lines.append("")
        for contrib_type in contributor_order:
            authors = authors_by_type.get(contrib_type, {})
            if authors:
                emoji = {"Human": "👤", "AI/Agent": "🤖", "Bot": "⚙️"}.get(contrib_type, "")
                lines.append(f"**{emoji} {contrib_type}**")
                for author, count in sorted(authors.items(), key=lambda x: -x[1]):
                    lines.append(f"- {author} ({count} commit{'s' if count > 1 else ''})")
                lines.append("")

    # Areas touched
    all_files: List[str] = []
    for commit in commits:
        all_files.extend(commit.files)
    areas = classify_areas(all_files)
    if areas:
        lines.append("### Areas Touched")
        lines.append("")
        for area in areas:
            lines.append(f"- {area}")
        lines.append("")

    return lines


# =============================================================================
# Duplicate Suppression
# =============================================================================


def hash_tracker_content(tracker: Dict[str, object]) -> str:
    """Generate hash of tracker content for duplicate detection.

    Args:
        tracker: Parsed tracker data dictionary

    Returns:
        8-character MD5 hash of tracker content
    """
    content = f"{tracker.get('status', '')}{tracker.get('summary', '')}{tracker.get('progress', '')}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def extract_tracker_hashes_from_history(
    history: str, exclude_date: Optional[str] = None
) -> Dict[str, Tuple[str, str]]:
    """Extract tracker hashes from previous snapshots for duplicate suppression.

    Args:
        history: The changelog history text
        exclude_date: Date to exclude from hash extraction (typically today's date)

    Returns:
        Dict mapping tracker title to (hash, date) tuple for most recent occurrence
    """
    hashes: Dict[str, Tuple[str, str]] = {}
    current_date: Optional[str] = None

    for line in history.splitlines():
        # Use SNAPSHOT_PREFIX constant to match snapshot headings
        escaped_prefix = re.escape(SNAPSHOT_PREFIX.rstrip())
        date_match = re.match(rf"^{escaped_prefix} ?(\d{{4}}-\d{{2}}-\d{{2}})$", line.strip())
        if date_match:
            current_date = date_match.group(1)
            continue
        # Skip hashes from the excluded date (prevents self-referential suppression)
        if current_date and exclude_date and current_date == exclude_date:
            continue
        hash_match = re.match(r"^#### (.+) <!-- hash:(\w+) -->$", line.strip())
        if hash_match and current_date:
            title, hash_val = hash_match.groups()
            if title not in hashes:
                hashes[title] = (hash_val, current_date)

    return hashes


def build_section_with_hash(
    title: str,
    tracker: Dict[str, object],
    heading_level: int = 4,
    previous_hashes: Optional[Dict[str, Tuple[str, str]]] = None,
) -> List[str]:
    """Build tracker section with hash for duplicate detection.

    Args:
        title: Section title
        tracker: Parsed tracker data
        heading_level: Markdown heading level (default 4)
        previous_hashes: Dict of previous tracker hashes for duplicate suppression

    Returns:
        List of markdown lines for the section
    """
    current_hash = hash_tracker_content(tracker)
    prefix = "#" * max(1, heading_level)

    # Check for duplicate suppression
    if previous_hashes and title in previous_hashes:
        prev_hash, prev_date = previous_hashes[title]
        if prev_hash == current_hash:
            return [f"{prefix} {title}", f"_(unchanged since {prev_date})_", ""]

    lines: List[str] = [f"{prefix} {title} <!-- hash:{current_hash} -->"]
    status = tracker.get("status")
    if status:
        lines.append(f"- Status: {status}")
    completion_date = tracker.get("completion_date")
    if completion_date:
        lines.append(f"- Completion Date: {completion_date}")
    start_date = tracker.get("start_date")
    if start_date and not completion_date:
        lines.append(f"- Start Date: {start_date}")
    branch = tracker.get("active_branch")
    if branch:
        lines.append(f"- Branch: {branch}")

    summary = tracker.get("summary") or []
    if summary:
        lines.append("")
        lines.append("Highlights:")
        lines.extend(summary)

    progress = tracker.get("progress") or []
    if progress:
        lines.append("")
        lines.append("Progress Log:")
        lines.extend(progress)

    lines.append("")
    return lines


# =============================================================================
# Snapshot Building
# =============================================================================


def build_snapshot(
    date_str: str,
    grouped: Dict[str, List[Dict[str, object]]],
    last_snapshot_date: Optional[str],
    include_git: bool,
    history: str = "",
) -> str:
    """Build a complete changelog snapshot.

    Args:
        date_str: Snapshot date (YYYY-MM-DD)
        grouped: Grouped tracker data (completed, active, pending)
        last_snapshot_date: Previous snapshot date for git range
        include_git: Whether to include git enrichment
        history: Full changelog history for duplicate suppression

    Returns:
        Markdown text for the snapshot
    """
    lines: List[str] = [f"{SNAPSHOT_PREFIX}{date_str}", ""]

    # Extract previous hashes for duplicate suppression (exclude today to prevent self-reference)
    previous_hashes = extract_tracker_hashes_from_history(history, exclude_date=date_str) if history else None

    def add_group(title: str, trackers: List[Dict[str, object]]):
        if not trackers:
            return
        lines.append(f"### {title}")
        lines.append("")
        for tracker in trackers:
            lines.extend(
                build_section_with_hash(
                    tracker["title"],
                    tracker,
                    heading_level=4,
                    previous_hashes=previous_hashes,
                )
            )
        lines.append("")

    add_group("Completed Tasks", grouped["completed"])
    add_group("Active Tasks", grouped["active"])
    add_group("Pending Tasks", grouped["pending"])

    if include_git:
        commits = get_commits_since(last_snapshot_date)
        prs = get_merge_prs_since(last_snapshot_date)
        git_lines = build_git_section(commits, prs)
        if git_lines:
            lines.extend(git_lines)

    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Main Render Function
# =============================================================================


def render_changelog(
    date_override: Optional[str] = None,
    include_git: bool = True,
    since_date: Optional[str] = None,
    only_today: bool = False,
) -> str:
    """Render complete changelog content.

    Args:
        date_override: Override today's date (YYYY-MM-DD)
        include_git: Include git commit enrichment
        since_date: Only include commits since this date
        only_today: Generate only today's snapshot without history

    Returns:
        Complete changelog markdown text
    """
    grouped = group_trackers()
    today = date_override or _dt.date.today().isoformat()

    existing_text = CHANGELOG_PATH.read_text(encoding="utf-8") if CHANGELOG_PATH.exists() else ""
    history = strip_header(existing_text)
    existing_dates = existing_snapshot_dates(history)

    def _previous_snapshot_date(dates: List[str], current: str) -> Optional[str]:
        for date in dates:
            if date != current:
                return date
        return None

    # Use explicit --since if provided, else previous snapshot date
    effective_since = since_date or _previous_snapshot_date(existing_dates, today)

    if only_today:
        # Only generate today's snapshot, don't include history
        history_without_today = ""
    else:
        history_without_today = remove_snapshot(history, today)

    snapshot = build_snapshot(today, grouped, effective_since, include_git, history)

    header = "\n".join(["# Changelog", "", f"_Last updated: {today}_", ""]) + "\n"

    parts = [header, snapshot]
    if history_without_today:
        parts.append(history_without_today.strip() + "\n")

    combined = "\n".join(parts)
    return combined.rstrip() + "\n"
