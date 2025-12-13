"""Data models for changelog generation.

This module contains data classes used throughout the changelog system:
- CommitInfo: Parsed commit metadata with classification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from tools.chngbrgr.config import CONTRIBUTOR_HUMAN


@dataclass
class CommitInfo:
    """Parsed commit metadata with classification.

    Attributes:
        sha: Short commit SHA
        subject: Commit subject line
        author: Commit author name
        files: List of files changed in the commit
        pr_number: Associated PR number if any
        change_type: Classified change type (Features, Fixes, etc.)
        contributor_type: Human, Bot, or AI/Agent classification
    """

    sha: str
    subject: str
    author: str
    files: List[str] = field(default_factory=list)
    pr_number: Optional[int] = None
    change_type: str = "Other"
    contributor_type: str = CONTRIBUTOR_HUMAN
