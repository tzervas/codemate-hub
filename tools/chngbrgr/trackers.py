"""Tracker file parsing and grouping.

This module handles reading and parsing tracker markdown files
from the trackers/tasks directory.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from tools.chngbrgr.config import TRACKERS_DIR


def read_tracker(path: Path) -> Dict[str, object]:
    """Parse a tracker markdown file into structured data.

    Args:
        path: Path to the tracker markdown file

    Returns:
        Dictionary containing parsed tracker data:
        - title: Task title from first heading
        - status: Status field value
        - completion_date: Completion date if present
        - start_date: Start date if present
        - active_branch: Active branch if specified
        - summary: List of summary bullet points
        - progress: List of progress log entries
        - path: Original file path
    """
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
            # Strip leading '#' and whitespace to match both:
            # - "Summary of Work" (plain text)
            # - "# Summary of Work" (markdown heading)
            normalized = line.strip().lstrip("#").strip().lower()
            if normalized == lower_name:
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

    def normalize_tags(raw: str) -> List[str]:
        tags: List[str] = []
        seen = set()
        for chunk in raw.split(","):
            clean = chunk.strip()
            if not clean:
                continue
            slug = re.sub(r"[^a-z0-9_-]+", "-", clean.lower().replace(" ", "-")).strip("-")
            if not slug:
                continue
            if slug not in seen:
                seen.add(slug)
                tags.append(slug)
        return tags

    title = lines[0].lstrip("# ").strip()
    status = extract_line("Status:")
    completion_date = extract_line("Completion Date:")
    start_date = extract_line("Start Date:")
    active_branch = extract_line("Active Branch:")
    tags = normalize_tags(extract_line("Tags:"))

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
        "tags": tags,
        "path": path,
    }


def group_trackers() -> Dict[str, List[Dict[str, object]]]:
    """Group all tracker files by status.

    Returns:
        Dictionary with keys 'completed', 'active', 'pending'
        containing lists of parsed tracker data.
    """
    completed: List[Dict[str, object]] = []
    active: List[Dict[str, object]] = []
    pending: List[Dict[str, object]] = []

    for path in sorted(TRACKERS_DIR.glob("*.md")):
        tracker = read_tracker(path)
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
