"""
Prompt Sanitizer for Review Orchestrator.

This module provides protection against prompt injection attacks by detecting
and removing dangerous patterns from user input.
"""

import re
from typing import List, Pattern


class PromptSanitizer:
    """Sanitizes user input to prevent prompt injection attacks."""

    # Define dangerous patterns as raw strings
    DANGEROUS_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"system\s*:\s*",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\].*?\[/INST\]",
    ]

    MAX_INPUT_LENGTH = 8192

    def __init__(self):
        """Initialize sanitizer with pre-compiled regex patterns for performance."""
        # Pre-compile patterns for better performance
        self._compiled_patterns: List[Pattern[str]] = [
            re.compile(pattern, flags=re.IGNORECASE)
            for pattern in self.DANGEROUS_PATTERNS
        ]
        # Pre-compile whitespace pattern
        self._whitespace_pattern: Pattern[str] = re.compile(r"\s+")

    def sanitize(self, user_input: str) -> str:
        """Remove potential prompt injection attempts.

        Args:
            user_input: The raw user input string to sanitize.

        Returns:
            The sanitized input with dangerous patterns removed and whitespace normalized.

        Raises:
            ValueError: If input exceeds MAX_INPUT_LENGTH.
        """
        # Early validation
        if not user_input:
            return ""

        if len(user_input) > self.MAX_INPUT_LENGTH:
            raise ValueError("Input exceeds maximum length")

        sanitized = user_input

        # Apply all dangerous pattern filters using pre-compiled patterns
        for pattern in self._compiled_patterns:
            sanitized = pattern.sub("", sanitized)

        # Remove excessive whitespace using pre-compiled pattern
        sanitized = self._whitespace_pattern.sub(" ", sanitized).strip()

        return sanitized
