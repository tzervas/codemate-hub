# Preseed: Python Development Best Practices

## Code Style and Quality

### Type Hints
Always use type hints for function signatures and complex variables:
```python
def process_data(items: list[dict[str, Any]], limit: int = 100) -> list[str]:
    """Process items and return list of results."""
    ...
```

### Docstrings
Use Google-style docstrings for all public functions and classes:
```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """
    Fetch data from a URL.
    
    Args:
        url: The URL to fetch from
        timeout: Request timeout in seconds
        
    Returns:
        Parsed JSON response as dictionary
        
    Raises:
        RequestError: If the request fails
    """
```

### Error Handling
Use specific exceptions and provide context:
```python
try:
    result = process_item(item)
except ValidationError as e:
    logger.error(f"Validation failed for {item.id}: {e}")
    raise ProcessingError(f"Failed to process item {item.id}") from e
```

## Project Structure

### Modern Python Project Layout
```
project/
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock             # Locked dependencies
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── main.py
│       └── utils/
├── tests/
│   ├── __init__.py
│   └── test_main.py
└── docs/
```

### Dependency Management with uv
Use `uv` for fast, reliable dependency management:
```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev pytest

# Lock dependencies
uv lock

# Sync environment
uv sync
```

## Testing

### Test Structure
```python
import pytest

class TestProcessor:
    """Tests for Processor class."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return Processor(config=TestConfig())
    
    def test_process_valid_input(self, processor):
        """Should process valid input correctly."""
        result = processor.process({"key": "value"})
        assert result.success is True
    
    @pytest.mark.parametrize("input,expected", [
        ("", False),
        ("valid", True),
    ])
    def test_validate(self, processor, input, expected):
        """Should validate inputs correctly."""
        assert processor.validate(input) == expected
```

## Async Patterns

### Async Context Managers
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource():
    resource = await acquire_resource()
    try:
        yield resource
    finally:
        await resource.close()
```

### Concurrent Operations
```python
import asyncio

async def fetch_all(urls: list[str]) -> list[Response]:
    """Fetch multiple URLs concurrently."""
    tasks = [fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Configuration

### Pydantic Settings
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    database_url: str
    api_key: str
    debug: bool = False
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

## Logging

### Structured Logging
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_data)
```
