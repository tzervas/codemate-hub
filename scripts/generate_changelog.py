#!/usr/bin/env python3
"""Generate CHANGELOG.md from tracker documents."""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
TRACKERS_DIR = ROOT / "trackers" / "tasks"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"


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


def _build_section(title: str, tracker: Dict[str, object]) -> List[str]:
    lines: List[str] = [f"### {title}"]
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


def render_changelog() -> str:
    grouped = _group_trackers()
    today = _dt.date.today().isoformat()

    output: List[str] = ["# Changelog", "", f"_Last updated: {today}_", ""]

    if grouped["completed"]:
        output.append("## Completed Tasks")
        output.append("")
        for tracker in grouped["completed"]:
            output.extend(_build_section(tracker["title"], tracker))

    if grouped["active"]:
        output.append("## Active Tasks")
        output.append("")
        for tracker in grouped["active"]:
            output.extend(_build_section(tracker["title"], tracker))

    if grouped["pending"]:
        output.append("## Pending Tasks")
        output.append("")
        for tracker in grouped["pending"]:
            output.extend(_build_section(tracker["title"], tracker))

    # Ensure trailing newline
    if output[-1] != "":
        output.append("")
    return "\n".join(output)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate project changelog from tracker documents.")
    parser.add_argument("--check", action="store_true", help="Fail if CHANGELOG.md is out of date")
    args = parser.parse_args(argv)

    changelog_content = render_changelog()

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
