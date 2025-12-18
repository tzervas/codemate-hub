# Langflow Pre-built Flows

This directory contains pre-configured Langflow flows optimized for the codemate-hub environment.

## Available Flows

### 1. RAG Pipeline (`rag-pipeline.json`)
**Purpose**: Document-based question answering with vector search

**Components**:
- ChromaDB vector store integration
- Ollama embeddings (nomic-embed-text)
- Context-aware prompting
- Conversation memory

**Use Cases**:
- Querying uploaded documentation
- Code repository knowledge base
- Technical documentation Q&A

### 2. Document Ingestion (`document-ingestion.json`)
**Purpose**: Multi-format document processing and embedding

**Supported Formats**:
- PDF, DOCX, TXT, MD
- HTML, JSON, CSV
- Code files

**Features**:
- Recursive text chunking (1000 chars, 200 overlap)
- Metadata enrichment (source, timestamp, type)
- Deduplication
- Batch processing

### 3. Code Assistant (`code-assistant.json`)
**Purpose**: Specialized code generation and review

**Modes**:
- **Generation**: Clean, documented code with best practices
- **Review**: Security, performance, quality analysis

**Features**:
- Conditional routing based on request type
- Session memory for context
- Language-agnostic support

### 4. Multi-Agent Orchestrator (`multi-agent-orchestrator.json`)
**Purpose**: Complex task decomposition with Manager-Worker-Evaluator pattern

**Agents**:
- **Manager**: Decomposes tasks, routes to specialists
- **Python Worker**: Python/API development
- **DevOps Worker**: Infrastructure/Docker/CI/CD
- **General Worker**: Documentation/research
- **Evaluator**: Quality gating with scoring

**Output**: Structured JSON with approval status and feedback

### 5. Web Search + RAG (`web-search-rag.json`)
**Purpose**: Hybrid real-time web search with document knowledge

**Features**:
- DuckDuckGo search integration
- Query analysis for routing
- Context merging from multiple sources
- Source citation

## Installation

### Automatic (via Docker volume)
Flows are automatically available when Langflow starts via the mounted volume:
```yaml
volumes:
  - ./config/langflow:/app/.langflow/presets:ro
```

### Manual Import
1. Open Langflow UI: `http://localhost:7860`
2. Click "Import" or drag JSON file
3. Configure any environment-specific settings

## Configuration

### Environment Variables
All flows reference these defaults:
```
OLLAMA_BASE_URL=http://ollama:11434
CHROMA_DB_DIR=/app/chroma_db
```

### Model Defaults
- **LLM**: `qwen2.5-coder:7b-q4_0` (code-optimized)
- **Embeddings**: `nomic-embed-text` (efficient, high-quality)

To use different models, update the `model_name` field in flow JSON.

## Customization

### Adding New Flows
1. Create flow in Langflow UI
2. Export as JSON
3. Save to this directory
4. Commit to version control

### Modifying Existing Flows
1. Import flow into Langflow
2. Make changes
3. Export updated JSON
4. Replace file in this directory

## Best Practices

1. **Version flows**: Include version in JSON metadata
2. **Test before committing**: Validate flow works with current Ollama models
3. **Document changes**: Update this README when adding/modifying flows
4. **Use environment variables**: Don't hardcode URLs or credentials
