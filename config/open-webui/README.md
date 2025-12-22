# Open-WebUI Configuration

This directory contains configuration presets and customizations for Open-WebUI.

## Files

### presets.json
Model presets with optimized parameters for different use cases:
- **Code Assistant**: Low temperature, high context for precise code generation
- **Creative Writer**: Higher temperature for creative content
- **Data Analyst**: Balanced settings for analysis tasks
- **Code Reviewer**: Very low temperature for consistent reviews
- **Research Assistant**: Moderate temperature for balanced research

## Features Configured

### RAG (Retrieval-Augmented Generation)
- Chunk size: 1000 characters
- Chunk overlap: 200 characters
- Top-K results: 5
- Relevance threshold: 0.7
- Embedding model: nomic-embed-text

### Web Search
- Engine: DuckDuckGo (no API key required)
- Max results: 5

### Code Interpreter
- Enabled with sandboxing
- Supported: Python, JavaScript, Bash

## Environment Variables

Configure in `.env`:
```env
WEBUI_SECRET_KEY=your-secret-key
OLLAMA_BASE_URL=http://ollama:11434
```

## Integration with Langflow

Open-WebUI can use the same Ollama instance as Langflow. Both services share:
- Ollama API at `http://ollama:11434`
- ChromaDB for vector storage (via mounted volumes)

## Customization

### Adding Model Presets
1. Edit `presets.json`
2. Add new preset object to `models.presets` array
3. Restart Open-WebUI or refresh the UI

### Changing Default Model
Update `ui.default_model` in `presets.json` or set via environment:
```env
DEFAULT_MODEL=qwen2.5-coder:7b-q4_0
```
