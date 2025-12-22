# Ollama Configuration

This directory contains Ollama model configurations and optimization settings.

## Files

### models.json
Comprehensive model configuration including:
- Model selections per use case
- Parameter presets
- GPU optimization profiles
- Custom Modelfile definitions

## Model Categories

### Code Generation
- **Primary**: qwen2.5-coder:7b-q4_0 (optimized for code)
- **Fallback**: codellama:7b
- **Parameters**: Low temperature (0.2), high context (8192)

### Embeddings
- **Primary**: nomic-embed-text (fast, high quality)
- **Fallback**: all-minilm
- Used by ChromaDB for vector storage

### Chat/General
- **Primary**: mistral:latest
- **Fallback**: llama3.2:latest
- Balanced for conversational use

### Vision (Multimodal)
- **Primary**: llava:7b
- Requires separate pull if image understanding needed

## GPU Profiles

### RTX 5080 (16GB VRAM)
```json
{
  "gpu_layers": 35,
  "batch_size": 512,
  "num_parallel": 4
}
```

### RTX 4090 (24GB VRAM)
```json
{
  "gpu_layers": 50,
  "batch_size": 1024,
  "num_parallel": 8
}
```

### CPU-Only
```json
{
  "num_gpu": 0,
  "batch_size": 256,
  "num_parallel": 2
}
```

## Custom Modelfiles

The `modelfiles` section defines custom model configurations:

### codemate-coder
Specialized for code generation with project-specific system prompt.

### codemate-reviewer
Optimized for code review with security and best practice focus.

### codemate-devops
Infrastructure and DevOps specialist configuration.

## Creating Custom Modelfiles

```bash
# Create Modelfile
cat > Modelfile << 'EOF'
FROM qwen2.5-coder:7b-q4_0
SYSTEM "Your custom system prompt here"
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
EOF

# Build custom model
docker exec ollama ollama create codemate-coder -f /path/to/Modelfile
```

## Environment Variables

Set in docker-compose.yml or .env:
```env
OLLAMA_NUM_PARALLEL=4
OLLAMA_NUM_THREAD=8
OLLAMA_HOST=0.0.0.0:11434
NVIDIA_VISIBLE_DEVICES=all
```

## Model Management

### Pull models on startup
Models listed in `pull_on_startup` are automatically pulled:
```bash
./scripts/model-pull.sh default
```

### List available models
```bash
docker exec ollama ollama list
```

### Remove unused models
```bash
./scripts/model-prune.sh list-unused
./scripts/model-prune.sh keep-models
```
