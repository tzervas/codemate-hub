#!/usr/bin/env bash
# Generate API documentation from Python source code
# Analyzes Python modules and generates MkDocs pages with docstring extraction

set -euo pipefail

# Color output
INFO='\033[0;34m'
SUCCESS='\033[0;32m'
WARN='\033[1;33m'
ERROR='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
DOCS_API_DIR="$PROJECT_ROOT/docs/api-reference"

echo -e "${INFO}🔵 API Documentation Generator${NC}"
echo ""

cd "$PROJECT_ROOT"

# Ensure docs directory exists
mkdir -p "$DOCS_API_DIR"

# Function to generate module documentation
generate_module_doc() {
    local module_path="$1"
    local module_name=$(basename "$module_path" .py)
    local doc_file="$DOCS_API_DIR/${module_name}.md"
    
    # Skip if module already has custom documentation
    if [[ -f "$doc_file" ]] && grep -q "Auto-Generated" "$doc_file" 2>/dev/null; then
        echo -e "${INFO}  ℹ️  Skipping $module_name (custom documentation exists)${NC}"
        return
    fi
    
    echo -e "${INFO}  📄 Generating documentation for $module_name${NC}"
    
    # Extract module docstring if it exists
    local module_doc=""
    # Use python with proper argument passing to avoid shell injection
    module_doc=$(python3 -c "
import sys
sys.path.insert(0, sys.argv[1])
try:
    mod = __import__(sys.argv[2])
    print(mod.__doc__ if mod.__doc__ else 'No description available')
except Exception:
    print('No description available')
" "$SRC_DIR" "$module_name" 2>/dev/null || echo "No description available")
    
    # Create basic documentation page
    cat > "$doc_file" << EOF
# ${module_name^} Module Reference

!!! info "Auto-Generated"
    This page contains auto-generated API documentation.

## Overview

$module_doc

## API Reference

::: src.$module_name
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature_annotations: true
      separate_signature: true

## Usage

\`\`\`python
from src import $module_name

# Add usage examples here
\`\`\`

!!! note "Documentation Status"
    This is auto-generated documentation. Please refer to the source code
    for the most up-to-date information.
EOF
    
    echo -e "${SUCCESS}    ✅ Generated $doc_file${NC}"
}

# Function to scan and generate documentation for all modules
scan_modules() {
    echo -e "${INFO}🔵 Scanning Python modules in $SRC_DIR${NC}"
    echo ""
    
    local count=0
    
    # Find all Python files in src/ (excluding __init__.py and __pycache__)
    while IFS= read -r module; do
        generate_module_doc "$module"
        ((count++))
    done < <(find "$SRC_DIR" -maxdepth 1 -name "*.py" ! -name "__init__.py" -type f)
    
    echo ""
    echo -e "${SUCCESS}✅ Generated documentation for $count module(s)${NC}"
}

# Function to update mkdocs.yml navigation
update_navigation() {
    echo -e "${INFO}🔵 Updating mkdocs.yml navigation...${NC}"
    
    # This is a placeholder - in a real implementation, you would:
    # 1. Parse existing mkdocs.yml
    # 2. Add new modules to API Reference section
    # 3. Preserve manual customizations
    
    echo -e "${WARN}⚠️  Navigation update not implemented yet${NC}"
    echo -e "${INFO}   Please manually add new modules to mkdocs.yml if needed${NC}"
}

# Function to generate API index
generate_api_index() {
    local index_file="$DOCS_API_DIR/index.md"
    
    echo -e "${INFO}🔵 Generating API index...${NC}"
    
    cat > "$index_file" << 'EOF'
# API Reference

Complete API documentation for all Codemate Hub modules.

## Core Modules

| Module | Description |
|--------|-------------|
| [Pipeline](pipeline.md) | Main execution pipeline and orchestration |
| [Orchestrator](orchestrator.md) | Task scheduling and coordination |
| [Agents](agents.md) | Agent management and persona system |
| [Task Manager](task-manager.md) | Task lifecycle and state management |
| [Signals](signals.md) | Event-driven signal system |

## Utility Modules

Additional modules will be listed here as they are documented.

## Quick Links

- [Architecture Overview](../architecture/overview.md)
- [Development Setup](../development/setup.md)
- [Getting Started](../getting-started/quick-start.md)

## Auto-Generated Documentation

All API documentation is automatically generated from Python docstrings using 
MkDocs Material and mkdocstrings. To regenerate:

```bash
./scripts/docs-generate.sh
```

## Contributing to API Docs

When adding or modifying Python modules:

1. Follow Google-style docstrings
2. Include type hints for all public APIs
3. Provide usage examples in docstrings
4. Run documentation generation to verify

See the [Contributing Guide](../development/contributing.md) for more details.
EOF
    
    echo -e "${SUCCESS}✅ Generated $index_file${NC}"
}

# Main execution
echo -e "${INFO}Starting API documentation generation...${NC}"
echo ""

# Generate API index
generate_api_index

# Scan and generate module documentation
# Note: This is disabled by default to preserve existing custom documentation
# Uncomment the next line to enable automatic generation
# scan_modules

echo ""
echo -e "${INFO}📋 Summary:${NC}"
echo -e "${INFO}   API Reference directory: $DOCS_API_DIR${NC}"
echo -e "${INFO}   Source directory: $SRC_DIR${NC}"
echo ""
echo -e "${SUCCESS}✅ API documentation generation complete${NC}"
echo ""
echo -e "${INFO}Next steps:${NC}"
echo -e "${INFO}  1. Review generated documentation in $DOCS_API_DIR${NC}"
echo -e "${INFO}  2. Run: ./scripts/docs-build.sh serve${NC}"
echo -e "${INFO}  3. Visit: http://localhost:8001${NC}"
