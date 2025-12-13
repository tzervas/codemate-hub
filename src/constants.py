"""
Shared constants for the coding assistant application.

This module contains configuration constants used across multiple modules
to maintain a single source of truth.
"""

# Model configuration
DEFAULT_MODEL = "qwen2.5-coder:7b-q4_0"

# Service URLs
DEFAULT_OLLAMA_URL = "http://ollama:11434"

# Storage paths
DEFAULT_CHROMA_DIR = "./chroma_db"

# Collection names
DEFAULT_COLLECTION_NAME = "documents"

# HTTP status codes
HTTP_SERVICE_UNAVAILABLE = 503

# Display and formatting
PROMPT_PREVIEW_LENGTH = 100

# Time conversion
MS_PER_SECOND = 1000
