# Optional FastAPI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.review_orchestrator.security.prompt_sanitizer import PromptSanitizer

app = FastAPI()

# Module-level sanitizer singleton for efficient pattern reuse
_sanitizer = PromptSanitizer()


class PromptRequest(BaseModel):
    """Request model for prompt API."""
    prompt: str


class PromptResponse(BaseModel):
    """Response model for prompt API."""
    sanitized_prompt: str
    original_length: int
    sanitized_length: int


@app.get("/")
def read_root():
    return {"message": "Codemate Hub API", "version": "1.0.0"}


@app.post("/api/sanitize")
def sanitize_prompt(request: PromptRequest) -> PromptResponse:
    """Sanitize a user prompt to remove potential injection attacks.
    
    Args:
        request: The prompt request containing the user input.
        
    Returns:
        PromptResponse with sanitized prompt and metadata.
        
    Raises:
        HTTPException: If input validation fails.
    """
    try:
        original_length = len(request.prompt)
        sanitized = _sanitizer.sanitize(request.prompt)
        sanitized_length = len(sanitized)
        
        return PromptResponse(
            sanitized_prompt=sanitized,
            original_length=original_length,
            sanitized_length=sanitized_length,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Input validation error: {e}")

