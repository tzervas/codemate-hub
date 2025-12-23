# Model Version History

This document tracks the model artifacts used in each release of codemate-hub.

## Overview

Codemate-hub uses locally-hosted LLM models via Ollama for code generation, embeddings, and general AI tasks. This document tracks which models are recommended and tested for each release version.

## Current Production Models (v0.4.0)

### Primary Model (Code Generation & Embeddings)
- **Name:** `qwen2.5-coder:7b-q4_0`
- **Purpose:** Code generation, code analysis, embeddings
- **Size:** ~4.7GB
- **Quantization:** Q4_0 (4-bit quantization)
- **Context Length:** 8192 tokens
- **Languages:** Python, JavaScript, Java, C++, Go, Rust, and 20+ more
- **Pull Command:** `./scripts/model-pull.sh default` or `ollama pull qwen2.5-coder:7b-q4_0`
- **Ollama Hub:** https://ollama.com/library/qwen2.5-coder
- **Performance:** Optimized for code generation, fast inference on CPU
- **Configuration:** Used in `src/memory_setup.py` line 60 for embeddings

**Why Qwen 2.5 Coder:**
- State-of-the-art code generation for its size
- Excellent multilingual support
- Fast inference with Q4 quantization
- Strong performance on code completion and analysis tasks
- Good balance of quality vs. resource usage

### Fallback Model (General Tasks)
- **Name:** `mistral:latest`
- **Purpose:** General-purpose LLM tasks, chat, reasoning
- **Size:** ~4.1GB
- **Quantization:** Q4_0
- **Context Length:** 8192 tokens
- **Pull Command:** `./scripts/model-pull.sh default` or `ollama pull mistral:latest`
- **Ollama Hub:** https://ollama.com/library/mistral
- **Performance:** Fast, efficient, good general-purpose reasoning

**Why Mistral:**
- Reliable general-purpose model
- Fast inference
- Good reasoning capabilities
- Fallback when code-specific model not needed

## Model Selection Criteria

When selecting models for codemate-hub, we consider:

1. **Performance:** Inference speed on target hardware (CPU-first, GPU-optional)
2. **Quality:** Code generation accuracy, context understanding
3. **Size:** Disk space and memory requirements (target: <10GB total)
4. **Quantization:** Balance between quality and performance (Q4_0 preferred)
5. **Compatibility:** Works well with Ollama, LangChain, ChromaDB
6. **Multilingual:** Support for multiple programming languages
7. **License:** Open-source, commercially usable

## Version History

### v0.4.0 (2024-12-23) - Current
**Primary:** qwen2.5-coder:7b-q4_0  
**Fallback:** mistral:latest  
**Changes:** Task 08 (Documentation & QA) - No model changes  
**Notes:** Comprehensive testing and documentation added

### v0.3.0 (2024-12-22)
**Primary:** qwen2.5-coder:7b-q4_0  
**Fallback:** mistral:latest  
**Changes:** Tasks 05-07 (Enclaves, Dev UX, Automation) - No model changes  
**Notes:** Enhanced developer experience and automation

### v0.2.0 (2024-12-16)
**Primary:** qwen2.5-coder:7b-q4_0  
**Fallback:** mistral:latest  
**Changes:** Tasks 03-04 (Application, Langflow) - No model changes  
**Notes:** Pipeline and Langflow integration completed

### v0.1.0 (2024-12-13)
**Primary:** qwen2.5-coder:7b-q4_0  
**Fallback:** mistral:latest  
**Changes:** Initial release (Tasks 01-02: Infrastructure, Models & Data)  
**Notes:** First stable release with core functionality

## Alternative Models

These models are compatible but not default-installed:

### Code-Focused Models
| Model | Size | Context | Notes |
|-------|------|---------|-------|
| `codellama:7b` | 3.8GB | 4096 | Legacy, replaced by Qwen 2.5 |
| `deepseek-coder:6.7b` | 3.8GB | 16384 | Large context, good quality |
| `starcoder2:7b` | 4.0GB | 16384 | Strong code completion |
| `codeqwen:7b` | 4.3GB | 8192 | Predecessor to Qwen 2.5 Coder |

### General-Purpose Models
| Model | Size | Context | Notes |
|-------|------|---------|-------|
| `llama3:8b` | 4.7GB | 8192 | Good reasoning, slower |
| `gemma:7b` | 5.0GB | 8192 | Google's model, efficient |
| `neural-chat:7b` | 4.1GB | 4096 | Fast, conversational |
| `phi3:mini` | 2.3GB | 4096 | Very small, limited quality |

### Large Models (GPU Recommended)
| Model | Size | Context | Notes |
|-------|------|---------|-------|
| `qwen2.5-coder:32b` | 18GB | 8192 | Best quality, requires GPU |
| `codellama:34b` | 19GB | 16384 | Large context, high quality |
| `mixtral:8x7b` | 26GB | 32768 | Mixture of experts, excellent |

## Model Update Procedure

When updating models between releases:

### 1. Test New Model

```bash
# Pull candidate model
./scripts/model-pull.sh <model-name>

# Verify download
docker exec ollama ollama list

# Test generation
docker exec ollama ollama run <model-name> "Write a Python hello world function"
```

### 2. Update Configuration

If changing the primary model:

```bash
# Update embedding model (if applicable)
nano src/memory_setup.py
# Line 60: embedding_model = "new-model:tag"

# Update default model pull script
nano scripts/model-pull.sh
# Update MODEL_DEFAULT variable

# Update documentation
nano README.md
nano docs/MODEL_SELECTION.md
```

### 3. Reinitialize Embeddings

If embedding model changes:

```bash
# Backup existing database
tar -czf chroma_db-backup-$(date +%Y%m%d).tar.gz chroma_db/

# Remove old embeddings
rm -rf chroma_db/

# Reinitialize with new model
docker exec coding-assistant python src/memory_setup.py
```

### 4. Validate Changes

```bash
# Run full test suite
pytest tests/ -v

# Run integration tests
./scripts/test-integration.sh full

# Test pipeline
docker exec coding-assistant python src/pipeline.py

# Test model inference
curl http://localhost:11434/api/generate -d '{
  "model": "new-model",
  "prompt": "def hello_world():",
  "stream": false
}'
```

### 5. Document Update

```bash
# Update this file
nano docs/MODEL_VERSIONS.md
# Add entry under "Version History"

# Update CHANGELOG.md
nano CHANGELOG.md
# Add under "Changed" section

# Commit changes
git add docs/MODEL_VERSIONS.md CHANGELOG.md src/memory_setup.py scripts/model-pull.sh
git commit -m "Update model: <reason>"
```

### 6. Tag Model Configuration

```bash
# Create model configuration tag
git tag -a models-vX.Y.Z -m "Model configuration for version X.Y.Z"
git push origin models-vX.Y.Z
```

## Model Checksums

For verification and reproducibility, record model digests:

### v0.4.0 Models
```bash
# List models with digests
docker exec ollama ollama list

# Example output format:
# NAME                      ID              SIZE
# qwen2.5-coder:7b-q4_0    abc123def456    4.7GB
# mistral:latest            789ghi012jkl    4.1GB
```

To verify a model's integrity:
```bash
docker exec ollama ollama show <model-name> | grep -i digest
```

## Model Storage

### Default Storage Location
- **Container:** `/root/.ollama/models/`
- **Volume:** `ollama_data` (Docker named volume)
- **Persistence:** Survives container restarts, removed by `./scripts/teardown.sh`

### Disk Usage Management

```bash
# Check total disk usage
docker system df

# List all models
docker exec ollama ollama list

# Check model sizes
du -sh $(docker volume inspect ollama_data --format '{{.Mountpoint}}')

# Prune unused models (keeps protected models)
./scripts/model-prune.sh keep-models
```

### Protected Models

Models that are **never pruned** by `model-prune.sh`:
- `qwen2.5-coder` (all variants)
- `mistral` (all variants)

To protect additional models, edit `scripts/model-prune.sh`:
```bash
PROTECTED_MODELS=(
    "qwen2.5-coder"
    "mistral"
    "your-model-here"
)
```

## Performance Benchmarks

Approximate inference speeds on common hardware:

### CPU-Only (Intel i7-12700K, 32GB RAM)
- **qwen2.5-coder:7b-q4_0:** ~12 tokens/sec
- **mistral:latest:** ~15 tokens/sec
- **First token latency:** 200-500ms

### GPU (NVIDIA RTX 3080, 10GB VRAM)
- **qwen2.5-coder:7b-q4_0:** ~40 tokens/sec
- **mistral:latest:** ~45 tokens/sec
- **First token latency:** 50-150ms

### GPU (NVIDIA RTX 4090, 24GB VRAM)
- **qwen2.5-coder:7b-q4_0:** ~80 tokens/sec
- **qwen2.5-coder:32b:** ~25 tokens/sec
- **mistral:latest:** ~90 tokens/sec

*Benchmarks vary based on prompt length, context size, and system load.*

## Troubleshooting

### Model Not Found
```bash
# Pull the model
./scripts/model-pull.sh <model-name>

# Or manually
docker exec ollama ollama pull <model-name>
```

### Embedding Model Mismatch
```bash
# Error: Model specified in memory_setup.py not available

# Solution: Pull the correct model
grep embedding_model src/memory_setup.py
docker exec ollama ollama pull <model-from-above>

# Or update memory_setup.py to use available model
```

### Out of Disk Space
```bash
# Check usage
docker system df

# List unused models
./scripts/model-prune.sh list-unused

# Prune unused models
./scripts/model-prune.sh keep-models

# Or manually remove a model
docker exec ollama ollama rm <model-name>
```

### Slow Inference
```bash
# Check CPU/RAM usage
docker stats

# Consider:
# 1. Use smaller model (e.g., mistral instead of qwen2.5-coder:32b)
# 2. Enable GPU support (see docs/GPU_SETUP.md)
# 3. Increase OLLAMA_NUM_THREAD env var in docker-compose.yml
# 4. Close other applications to free memory
```

## References

- [Ollama Model Library](https://ollama.com/library)
- [Model Selection Guide](MODEL_SELECTION.md)
- [GPU Setup Guide](GPU_SETUP.md)
- [Model Pruning Script](../scripts/model-prune.sh)
- [Memory Setup Script](../src/memory_setup.py)

## Questions?

For questions about model selection or updates:
- Review [docs/MODEL_SELECTION.md](MODEL_SELECTION.md)
- Check [Ollama documentation](https://github.com/ollama/ollama)
- Open an issue on GitHub
