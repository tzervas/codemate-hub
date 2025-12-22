# Model Context Protocol (MCP) Configuration

This directory contains MCP server configurations for enhanced tool capabilities.

## Overview

MCP (Model Context Protocol) provides a standardized way for AI assistants to interact with external tools and services. This configuration includes both official MCP servers and custom tools.

## Official MCP Servers

### Enabled by Default

| Server | Description | Use Case |
|--------|-------------|----------|
| filesystem | File system operations | Read/write project files |
| github | GitHub API integration | Repository management |
| memory | Key-value storage | Persistent context |
| fetch | HTTP requests | Web content retrieval |
| sqlite | SQLite database | Local data storage |
| sequential-thinking | Chain-of-thought | Enhanced reasoning |

### Optional (Require Configuration)

| Server | Description | Requirements |
|--------|-------------|--------------|
| postgres | PostgreSQL database | `DATABASE_URL` env var |
| brave-search | Web search | `BRAVE_API_KEY` env var |
| puppeteer | Browser automation | Chromium installation |

## Custom Tools

### code_executor
Sandboxed code execution with:
- Python, JavaScript, Bash support
- 30-second timeout
- 512MB memory limit
- Isolated execution environment

### document_processor
Document processing for RAG:
- Supports PDF, DOCX, TXT, MD, HTML, CSV, JSON
- Configurable chunking (1000 chars, 200 overlap)
- Metadata extraction

### vector_search
Semantic search in ChromaDB:
- Uses nomic-embed-text embeddings
- Top-K retrieval (default: 5)
- Relevance threshold filtering

### git_operations
Git repository operations:
- Status, diff, log viewing
- Branch management
- Commit and push (with safeguards)

## Configuration

### Environment Variables

Add to `.env`:
```env
# GitHub MCP Server
GITHUB_TOKEN=ghp_your_token_here

# Brave Search (optional)
BRAVE_API_KEY=your_brave_api_key

# PostgreSQL (optional)
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Enabling/Disabling Servers

Edit `servers.json` and set `"enabled": true/false` for each server.

## Tool Groups

Pre-configured tool groups for common workflows:

### Development
- filesystem, github, code_executor, git_operations

### Research
- fetch, brave-search, vector_search, sequential-thinking

### Data
- sqlite, postgres, document_processor, vector_search

## Integration

### With Langflow
MCP tools can be used in Langflow via custom components:
1. Import tool configuration
2. Create Langflow component wrapper
3. Add to flow as tool node

### With CrewAI/LangChain
```python
from langchain.tools import Tool
from src.tools import load_mcp_tools

tools = load_mcp_tools(config_path="config/mcp/servers.json")
```

### Direct Usage
```python
from src.mcp_client import MCPClient

client = MCPClient(config_path="config/mcp/servers.json")
result = await client.call_tool("filesystem", "read_file", {"path": "/app/src/app.py"})
```

## Security Considerations

1. **Filesystem**: Restricted to allowed_paths only
2. **GitHub**: Use fine-grained tokens with minimal permissions
3. **Code Executor**: Runs in sandbox with resource limits
4. **Database**: Use read-only credentials where possible

## Adding New MCP Servers

1. Add server configuration to `servers.json`
2. Install required packages: `npm install -g @modelcontextprotocol/server-<name>`
3. Set required environment variables
4. Enable in configuration
5. Restart services

## Troubleshooting

### Server not starting
```bash
# Check if package is installed
npx -y @modelcontextprotocol/server-<name> --help

# Check environment variables
env | grep -E 'GITHUB|BRAVE|DATABASE'
```

### Connection issues
```bash
# Test server manually
npx -y @modelcontextprotocol/server-filesystem /tmp

# Check Docker networking
docker exec coding-assistant curl http://localhost:3000
```
