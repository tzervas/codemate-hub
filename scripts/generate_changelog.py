#!/usr/bin/env python3
"""Generate CHANGELOG.md from tracker documents with git/PR enrichment."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
TRACKERS_DIR = ROOT / "trackers" / "tasks"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
SNAPSHOT_PREFIX = "## Snapshot "

# Path grouping buckets for area classification
PATH_BUCKETS: Dict[str, List[str]] = {
    "Application": ["src/"],
    "Scripts": ["scripts/"],
    "Tests": ["tests/"],
    "Documentation": ["docs/", "*.md", "trackers/"],
    "Configuration": ["docker", "Dockerfile", ".github/", "pyproject.toml", "requirements"],
}

# Commit prefix → change type mapping (conventional commits)
CHANGE_TYPE_PREFIXES: Dict[str, str] = {
    "feat": "Features",
    "fix": "Fixes",
    "docs": "Documentation",
    "chore": "Chores",
    "refactor": "Refactors",
    "test": "Tests",
    "ci": "CI/CD",
    "style": "Style",
    "perf": "Performance",
}

# Contributor type classification
# Pattern lists for identifying commit author types
BOT_PATTERNS: List[str] = [
    "[bot]",
    "dependabot",
    "renovate",
    "github-actions",
    "pre-commit",
    "semantic-release",
    "release-please",
    "snyk",
    "greenkeeper",
    "imgbot",
    "allcontributors",
]

AI_AGENT_PATTERNS: List[str] = [
    "copilot",
    "github copilot",
    "claude",
    "anthropic",
    "openai",
    "gpt",
    "chatgpt",
    "cursor",
    "codeium",
    "tabnine",
    "sourcery",
    "aider",
    "devin",
]

# Patterns to exclude from changelog (prevent recursion - changelog-only commits)
# These match commit subjects that indicate changelog-maintenance commits
EXCLUDED_COMMIT_PATTERNS: List[str] = [
    # Changelog-specific (self-referential)
    "update changelog",
    "changelog update",
    "regenerate changelog",
    "refresh changelog",
    "sync changelog",
    # Conventional commit scopes for changelog
    "chore: changelog",
    "chore(changelog)",
    "docs: changelog",
    "docs(changelog)",
    "ci: changelog",
]

# Files that indicate a changelog/meta-only commit (excluded from git section)
# Commits touching ONLY these files are filtered out
CHANGELOG_ONLY_FILES: set[str] = {
    "CHANGELOG.md",
    "CHANGELOG",
    "changelog.md",
}

# Additional files that, when committed alone, suggest automation (but keep in changelog)
AUTOMATION_ONLY_FILES: set[str] = {
    "CHANGELOG.md",
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "Cargo.lock",
}

# Contributor type enum values
CONTRIBUTOR_HUMAN = "Human"
CONTRIBUTOR_BOT = "Bot"
CONTRIBUTOR_AI = "AI/Agent"


@dataclass
class CommitInfo:
    """Parsed commit metadata."""

    sha: str
    subject: str
    author: str
    files: List[str] = field(default_factory=list)
    pr_number: Optional[int] = None
    change_type: str = "Other"
    contributor_type: str = CONTRIBUTOR_HUMAN  # Human, Bot, or AI/Agent


def _read_tracker(path: Path) -> Dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()

    def extract_line(prefix: str) -> str:
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return ""

    def extract_section(name: str) -> List[str]:
        lower_name = name.lower()
        start = None
        for idx, line in enumerate(lines):
            if line.strip().lower() == lower_name:
                start = idx + 1
                break
        if start is None:
            return []

        # Skip underline of dashes or equals
        while start < len(lines) and set(lines[start].strip()) <= {"-"} and lines[start].strip():
            start += 1

        collected: List[str] = []
        for idx in range(start, len(lines)):
            line = lines[idx]
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if line.strip() and next_line and set(next_line.strip()) <= {"-"} and len(next_line.strip()) >= 3:
                break
            collected.append(line)
        while collected and not collected[-1].strip():
            collected.pop()
        return collected

    def as_bullets(raw_lines: List[str]) -> List[str]:
        bullets: List[str] = []
        for raw in raw_lines:
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith("- "):
                bullets.append(stripped)
            else:
                bullets.append(f"- {stripped}")
        return bullets

    title = lines[0].lstrip("# ").strip()
    status = extract_line("Status:")
    completion_date = extract_line("Completion Date:")
    start_date = extract_line("Start Date:")
    active_branch = extract_line("Active Branch:")

    summary = as_bullets(extract_section("Summary of Work"))
    progress = as_bullets(extract_section("Progress Log"))

    return {
        "title": title,
        "status": status,
        "completion_date": completion_date,
        "start_date": start_date,
        "active_branch": active_branch,
        "summary": summary,
        "progress": progress,
        "path": path,
    }


def _group_trackers() -> Dict[str, List[Dict[str, object]]]:
    completed: List[Dict[str, object]] = []
    active: List[Dict[str, object]] = []
    pending: List[Dict[str, object]] = []

    for path in sorted(TRACKERS_DIR.glob("*.md")):
        tracker = _read_tracker(path)
        status = tracker.get("status", "").lower()

        if "complete" in status or "✅" in status:
            completed.append(tracker)
        elif "progress" in status:
            active.append(tracker)
        else:
            pending.append(tracker)

    return {
        "completed": completed,
        "active": active,
        "pending": pending,
    }


def _build_section(title: str, tracker: Dict[str, object], heading_level: int = 4) -> List[str]:
    prefix = "#" * max(1, heading_level)
    lines: List[str] = [f"{prefix} {title}"]
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


def _strip_header(changelog_text: str) -> str:
    """Remove the title/last-updated preamble so history can be preserved cleanly."""

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


def _existing_snapshot_dates(history: str) -> List[str]:
    # Build regex from SNAPSHOT_PREFIX constant to stay aligned
    escaped_prefix = re.escape(SNAPSHOT_PREFIX.strip())
    pattern = re.compile(rf"^{escaped_prefix}(\d{{4}}-\d{{2}}-\d{{2}})$")
    dates: List[str] = []
    for line in history.splitlines():
        match = pattern.match(line.strip())
        if match:
            dates.append(match.group(1))
    return dates


def _remove_snapshot(history: str, target_date: str) -> str:
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
# Git/PR Enrichment Functions
# =============================================================================


def _classify_contributor_type(author: str, subject: str) -> str:
    """Classify contributor as Human, Bot, or AI/Agent based on author name and commit subject."""
    lower_author = author.lower()
    lower_subject = subject.lower()
    
    # Check for bot patterns in author name
    for pattern in BOT_PATTERNS:
        if pattern in lower_author:
            return CONTRIBUTOR_BOT
    
    # Check for AI/agent patterns in author name or subject
    for pattern in AI_AGENT_PATTERNS:
        if pattern in lower_author or pattern in lower_subject:
            return CONTRIBUTOR_AI
    
    # Check for common bot author name patterns
    if lower_author.endswith("[bot]") or lower_author.endswith("-bot"):
        return CONTRIBUTOR_BOT
    
    # Check for AI-assisted commit indicators in subject
    if any(marker in lower_subject for marker in ["co-authored-by: github copilot", "🤖", "generated by"]):
        return CONTRIBUTOR_AI
    
    return CONTRIBUTOR_HUMAN


def _is_changelog_commit(subject: str, files: List[str]) -> bool:
    """Check if commit is a changelog-only update (should be excluded).
    
    Exclusion criteria:
    1. Subject matches known changelog-maintenance patterns
    2. Commit only touches CHANGELOG.md (self-referential)
    
    This prevents recursive changelog entries.
    Note: Bot/AI commits are NOT excluded here - they go in separate sections.
    """
    lower = subject.lower()
    
    # Check subject patterns for changelog-specific commits
    for pattern in EXCLUDED_COMMIT_PATTERNS:
        if pattern in lower:
            return True
    
    # Check if commit only touches changelog file(s) - self-referential
    if files and set(files) <= CHANGELOG_ONLY_FILES:
        return True
    
    # Empty commits (merge commits with no file changes recorded)
    # These are typically already filtered by --no-merges but double-check
    if not files and not subject.strip():
        return True
    
    return False


def _classify_change_type(subject: str) -> str:
    """Classify commit by conventional commit prefix."""
    lower = subject.lower()
    for prefix, change_type in CHANGE_TYPE_PREFIXES.items():
        if lower.startswith(f"{prefix}:") or lower.startswith(f"{prefix}("):
            return change_type
    return "Other"


def _extract_pr_number(subject: str) -> Optional[int]:
    """Extract PR number from merge commit or squash-merge subject."""
    # Merge pull request #123 from ...
    match = re.search(r"Merge pull request #(\d+)", subject)
    if match:
        return int(match.group(1))
    # Subject (#123) - squash merge format
    match = re.search(r"\(#(\d+)\)\s*$", subject)
    if match:
        return int(match.group(1))
    return None


def _classify_areas(files: List[str]) -> List[str]:
    """Classify changed files into area buckets."""
    areas: set[str] = set()
    for file_path in files:
        matched = False
        for area, patterns in PATH_BUCKETS.items():
            for pattern in patterns:
                if pattern.startswith("*"):
                    if file_path.endswith(pattern[1:]):
                        areas.add(area)
                        matched = True
                        break
                elif file_path.startswith(pattern) or pattern in file_path:
                    areas.add(area)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            areas.add("Other")
    return sorted(areas)


def _git_commits_since(since_date: Optional[str]) -> List[CommitInfo]:
    """Get detailed commit info since a date."""
    if not since_date:
        return []

    cmd = [
        "git",
        "log",
        f"--since={since_date}T00:00:00",
        "--pretty=format:%h|%s|%an",
        "--no-merges",
    ]
    # Security: cmd is constructed from internal constants only (since_date from internal logic).
    # No user input flows into the command. Using list form prevents shell injection.
    try:
        output = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []

    commits: List[CommitInfo] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        sha, subject, author = parts

        # Get files changed by this commit
        try:
            files_output = subprocess.check_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            files = [f.strip() for f in files_output.splitlines() if f.strip()]
        except Exception:
            files = []

        # Skip changelog-only commits to prevent recursion
        if _is_changelog_commit(subject, files):
            continue

        commits.append(
            CommitInfo(
                sha=sha,
                subject=subject,
                author=author,
                files=files,
                pr_number=_extract_pr_number(subject),
                change_type=_classify_change_type(subject),
                contributor_type=_classify_contributor_type(author, subject),
            )
        )

    return commits


def _is_excluded_pr(subject: str) -> bool:
    """Check if a PR merge commit should be excluded from changelog."""
    lower = subject.lower()
    for pattern in EXCLUDED_COMMIT_PATTERNS:
        if pattern in lower:
            return True
    return False


def _get_merge_prs_since(since_date: Optional[str]) -> List[Tuple[int, str]]:
    """Get merged PR numbers and titles from merge commits."""
    if not since_date:
        return []

    cmd = [
        "git",
        "log",
        f"--since={since_date}T00:00:00",
        "--merges",
        "--pretty=format:%s",
    ]
    # Security: cmd constructed from internal constants only. No external input.
    try:
        output = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []

    prs: List[Tuple[int, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        # Skip excluded PRs (changelog updates, bots, etc.)
        if _is_excluded_pr(line):
            continue
        pr_num = _extract_pr_number(line)
        if pr_num:
            # Extract branch name as proxy for title
            match = re.search(r"from \S+/(.+)$", line)
            title = match.group(1).replace("-", " ").replace("_", " ") if match else line
            prs.append((pr_num, title))

    return prs


def _build_git_section(
    commits: List[CommitInfo],
    prs: List[Tuple[int, str]],
) -> List[str]:
    """Build enriched git section with PRs, contributors by type, areas, and change types."""
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
    areas = _classify_areas(all_files)
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


def _hash_tracker_content(tracker: Dict[str, object]) -> str:
    """Generate hash of tracker content for duplicate detection."""
    content = f"{tracker.get('status', '')}{tracker.get('summary', '')}{tracker.get('progress', '')}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def _extract_tracker_hashes_from_history(history: str, exclude_date: Optional[str] = None) -> Dict[str, Tuple[str, str]]:
    """Extract tracker hashes from previous snapshots for duplicate suppression.
    
    Args:
        history: The changelog history text
        exclude_date: Date to exclude from hash extraction (typically today's date)
    
    Returns:
        Dict mapping tracker title to (hash, date) tuple for most recent occurrence
    """
    # Returns {tracker_title: (hash, date)} for the most recent occurrence
    hashes: Dict[str, Tuple[str, str]] = {}
    current_date: Optional[str] = None

    for line in history.splitlines():
        date_match = re.match(r"^## Snapshot (\d{4}-\d{2}-\d{2})$", line.strip())
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


def _build_section_with_hash(
    title: str,
    tracker: Dict[str, object],
    heading_level: int = 4,
    previous_hashes: Optional[Dict[str, Tuple[str, str]]] = None,
) -> List[str]:
    """Build tracker section with hash for duplicate detection."""
    current_hash = _hash_tracker_content(tracker)
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


def _build_snapshot(
    date_str: str,
    grouped: Dict[str, List[Dict[str, object]]],
    last_snapshot_date: Optional[str],
    include_git: bool,
    history: str = "",
) -> str:
    lines: List[str] = [f"{SNAPSHOT_PREFIX}{date_str}", ""]

    # Extract previous hashes for duplicate suppression (exclude today to prevent self-reference)
    previous_hashes = _extract_tracker_hashes_from_history(history, exclude_date=date_str) if history else None

    def add_group(title: str, trackers: List[Dict[str, object]]):
        if not trackers:
            return
        lines.append(f"### {title}")
        lines.append("")
        for tracker in trackers:
            lines.extend(
                _build_section_with_hash(
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
        commits = _git_commits_since(last_snapshot_date)
        prs = _get_merge_prs_since(last_snapshot_date)
        git_lines = _build_git_section(commits, prs)
        if git_lines:
            lines.extend(git_lines)

    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("")
    return "\n".join(lines)


def render_changelog(
    date_override: Optional[str] = None,
    include_git: bool = True,
    since_date: Optional[str] = None,
    only_today: bool = False,
) -> str:
    grouped = _group_trackers()
    today = date_override or _dt.date.today().isoformat()

    existing_text = CHANGELOG_PATH.read_text(encoding="utf-8") if CHANGELOG_PATH.exists() else ""
    history = _strip_header(existing_text)
    existing_dates = _existing_snapshot_dates(history)

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
        history_without_today = _remove_snapshot(history, today)

    snapshot = _build_snapshot(today, grouped, effective_since, include_git, history)

    header = "\n".join(["# Changelog", "", f"_Last updated: {today}_", ""]) + "\n"

    parts = [header, snapshot]
    if history_without_today:
        parts.append(history_without_today.strip() + "\n")

    combined = "\n".join(parts)
    return combined.rstrip() + "\n"


def main(argv: List[str] | None = None) -> int:
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
            print("CHANGELOG.md is missing. Run scripts/generate_changelog.py to create it.", file=sys.stderr)
            return 1
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
        if existing != changelog_content:
            print("CHANGELOG.md is out of date. Run scripts/generate_changelog.py to refresh.", file=sys.stderr)
            return 1
        return 0

    CHANGELOG_PATH.write_text(changelog_content, encoding="utf-8")
    print(f"✓ CHANGELOG.md updated ({CHANGELOG_PATH})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
