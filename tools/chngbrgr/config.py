"""Configuration constants for changelog generation.

This module contains all configurable constants including:
- Path definitions and patterns
- Commit type mappings
- Contributor classification patterns
- Exclusion rules
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

# =============================================================================
# Path Configuration
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]
TRACKERS_DIR = ROOT / "trackers" / "tasks"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
SNAPSHOT_PREFIX = "## Snapshot "

# =============================================================================
# Path Grouping Buckets
# =============================================================================

# Maps area names to file path patterns for classification
PATH_BUCKETS: Dict[str, List[str]] = {
    "Application": ["src/"],
    "Scripts": ["scripts/"],
    "Tests": ["tests/"],
    "Documentation": ["docs/", "*.md", "trackers/"],
    "Configuration": ["docker", "Dockerfile", ".github/", "pyproject.toml", "requirements"],
}

# =============================================================================
# Conventional Commit Mapping
# =============================================================================

# Commit prefix → change type mapping
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

# =============================================================================
# Contributor Classification
# =============================================================================

# Patterns for identifying bot authors
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

# Patterns for identifying AI/agent contributors
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

# Contributor type enum values
CONTRIBUTOR_HUMAN = "Human"
CONTRIBUTOR_BOT = "Bot"
CONTRIBUTOR_AI = "AI/Agent"

# =============================================================================
# Exclusion Rules
# =============================================================================

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
