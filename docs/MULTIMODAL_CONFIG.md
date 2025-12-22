# Multimodal AI Configuration Guide

This guide covers the preloaded configurations for optimizing the multimodal AI experience in Codemate Hub.

## Quick Start

After deployment, configurations are automatically available:

```bash
# Deploy the cluster
./scripts/deploy-universal.sh

# Or on Windows
.\scripts\Deploy-Universal.ps1
```

## Configuration Structure

```
config/
├── langflow/
│   └── flows/              # Pre-built Langflow workflows
│       ├── rag-pipeline.json
│       ├── document-ingestion.json
│       ├── code-assistant.json
│       ├── multi-agent-orchestrator.json
│       └── web-search-rag.json
├── open-webui/
│   └── presets.json        # Model presets and UI config
├── ollama/
│   └── models.json         # Model configurations and GPU optimization
├── mcp/
│   └── servers.json        # MCP server configurations
└── ssl/                    # SSL certificates (auto-generated)
```

## Langflow Flows

### RAG Pipeline
**File**: `config/langflow/flows/rag-pipeline.json`

Document-based Q&A with:
- ChromaDB vector store
- Ollama embeddings (nomic-embed-text)
- Context-aware prompting

```
[User Query] → [Embeddings] → [Vector Search] → [Context] → [LLM] → [Response]
```

### Document Ingestion
**File**: `config/langflow/flows/document-ingestion.json`

Multi-format document processing:
- PDF, DOCX, TXT, MD, HTML, CSV, JSON
- Recursive text chunking (1000 chars, 200 overlap)
- Metadata enrichment
- ChromaDB storage

### Code Assistant
**File**: `config/langflow/flows/code-assistant.json`

Specialized code workflows:
- **Generation mode**: Clean, documented code
- **Review mode**: Security, performance, best practices

### Multi-Agent Orchestrator
**File**: `config/langflow/flows/multi-agent-orchestrator.json`

Manager-Worker-Evaluator pattern:
- Task decomposition by Manager
- Specialist Workers (Python, DevOps, General)
- Quality gating by Evaluator

### Web Search + RAG
**File**: `config/langflow/flows/web-search-rag.json`

Hybrid search combining:
- DuckDuckGo web search
- ChromaDB document retrieval
- Query analysis for routing

## Open-WebUI Presets

### Model Presets
| Preset | Model | Use Case | Temperature |
|--------|-------|----------|-------------|
| Code Assistant | qwen2.5-coder:7b-q4_0 | Code generation | 0.2 |
| Creative Writer | mistral:latest | Creative content | 0.8 |
| Data Analyst | qwen2.5-coder:7b-q4_0 | Analysis tasks | 0.3 |
| Code Reviewer | qwen2.5-coder:7b-q4_0 | Code review | 0.1 |
| Research Assistant | mistral:latest | Research | 0.4 |

### RAG Configuration
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "top_k": 5,
  "relevance_threshold": 0.7,
  "embedding_model": "nomic-embed-text"
}
```

### Feature Toggles
- **Web Search**: DuckDuckGo (no API key needed)
- **Code Interpreter**: Python, JavaScript, Bash
- **Image Generation**: Disabled (enable Stable Diffusion in docker-compose)

## Ollama Configuration

### GPU Profiles

**RTX 5080 (16GB VRAM)**:
```json
{
  "gpu_layers": 35,
  "batch_size": 512,
  "num_parallel": 4,
  "num_thread": 8
}
```

**RTX 4090 (24GB VRAM)**:
```json
{
  "gpu_layers": 50,
  "batch_size": 1024,
  "num_parallel": 8
}
```

### Custom Modelfiles

Create specialized models:

```bash
# Create codemate-coder model
docker exec ollama ollama create codemate-coder -f /config/modelfiles/codemate-coder
```

Available custom models:
- `codemate-coder`: Code generation specialist
- `codemate-reviewer`: Code review expert
- `codemate-devops`: DevOps/infrastructure specialist

## MCP Servers

### Enabled by Default
| Server | Purpose |
|--------|---------|
| filesystem | File operations (sandboxed) |
| github | Repository management |
| memory | Key-value storage |
| fetch | HTTP requests |
| sqlite | Local database |
| sequential-thinking | Enhanced reasoning |

### Environment Variables
```env
# Required for GitHub MCP
GITHUB_TOKEN=ghp_your_token

# Optional: Brave Search
BRAVE_API_KEY=your_key

# Optional: PostgreSQL
DATABASE_URL=postgresql://...
```

### Custom Tools
- **code_executor**: Sandboxed code execution
- **document_processor**: Document chunking for RAG
- **vector_search**: ChromaDB semantic search
- **git_operations**: Safe git commands

## RAG Services

### Python API

```python
from src.services.rag_pipeline import RAGPipeline

# Initialize
pipeline = RAGPipeline()

# Ingest documents
await pipeline.ingest_file("docs/guide.pdf")
await pipeline.ingest_directory("./knowledge_base")

# Query
result = await pipeline.query("How do I configure Docker?")
print(result["answer"])
print(result["sources"])
```

### Document Ingestion

```python
from src.services.ingestion_service import DocumentIngestionService

service = DocumentIngestionService()

# Ingest with metadata
await service.ingest_file(
    "report.pdf",
    metadata={"category": "reports", "author": "team"}
)

# Batch ingestion
await service.ingest_directory(
    "./docs",
    recursive=True,
    extensions=[".md", ".txt", ".pdf"]
)
```

### Vector Search

```python
from src.tools.vector_search import VectorSearchTool

tool = VectorSearchTool(top_k=5, relevance_threshold=0.7)

results = await tool.search("Python best practices")
for r in results["results"]:
    print(f"Score: {r['score']:.2f}")
    print(f"Content: {r['content'][:200]}...")
```

## Domain Preseeds

Pre-loaded knowledge for agents in `insights/domain-preseeds/`:

- **python-best-practices.md**: Type hints, testing, async patterns
- **docker-devops.md**: Container patterns, CI/CD, Nginx
- **rag-langchain.md**: RAG architecture, embeddings, prompts

These are automatically loaded into ChromaDB on startup.

## Customization

### Adding Langflow Flows
1. Create flow in Langflow UI
2. Export as JSON
3. Save to `config/langflow/flows/`
4. Restart or import manually

### Adding Model Presets
Edit `config/open-webui/presets.json`:
```json
{
  "id": "my-preset",
  "name": "My Custom Preset",
  "model": "model:tag",
  "system_prompt": "...",
  "parameters": {
    "temperature": 0.5
  }
}
```

### Adding MCP Servers
Edit `config/mcp/servers.json`:
```json
{
  "my-server": {
    "package": "@my-org/mcp-server",
    "command": "npx",
    "args": ["-y", "@my-org/mcp-server"],
    "enabled": true
  }
}
```

## Troubleshooting

### Embeddings Not Working
```bash
# Check if embedding model is pulled
docker exec ollama ollama list | grep nomic-embed-text

# Pull if missing
docker exec ollama ollama pull nomic-embed-text
```

### ChromaDB Issues
```bash
# Check collection
docker exec coding-assistant python -c "
from langchain_chroma import Chroma
db = Chroma(persist_directory='/app/chroma_db')
print(f'Documents: {db._collection.count()}')
"
```

### Langflow Flow Import Fails
- Verify JSON syntax
- Check Ollama URL in flow matches environment
- Ensure required components are available

### MCP Server Connection Issues
```bash
# Test MCP server manually
npx -y @modelcontextprotocol/server-filesystem /tmp

# Check Docker networking
docker exec coding-assistant curl http://localhost:3000
```
