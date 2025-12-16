"""Prompt sanitization to prevent injection attacks."""

import re
from typing import List


class PromptSanitizer:
    """Sanitizer to remove potential prompt injection attempts."""
    
    DANGEROUS_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"system\s*:\s*",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\].*\[/INST\]",
    ]
    
    MAX_INPUT_LENGTH = 8192
    
    def sanitize(self, user_input: str) -> str:
        """Remove potential prompt injection attempts.
        
        Args:
            user_input: The user input string to sanitize.
            
        Returns:
            The sanitized string with dangerous patterns removed and whitespace normalized.
            
        Raises:
            ValueError: If input exceeds MAX_INPUT_LENGTH.
        """
        if len(user_input) > self.MAX_INPUT_LENGTH:
            raise ValueError("Input exceeds maximum length")
            
        sanitized = user_input
        
        for pattern in self.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
            
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
