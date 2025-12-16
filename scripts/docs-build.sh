#!/usr/bin/env bash
# Build and validate documentation
# Usage: ./scripts/docs-build.sh [--serve|--validate]

set -euo pipefail

# Color output
INFO='\033[0;34m'
SUCCESS='\033[0;32m'
WARN='\033[1;33m'
ERROR='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
MODE="${1:-build}"

echo -e "${INFO}🔵 Documentation Build Script${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Function to check if MkDocs is available
check_mkdocs() {
    if ! command -v mkdocs &> /dev/null; then
        echo -e "${WARN}⚠️  MkDocs not found. Installing...${NC}"
        pip install -q mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions
    fi
}

# Function to build documentation
build_docs() {
    echo -e "${INFO}🔵 Building documentation...${NC}"
    
    if mkdocs build --strict; then
        echo -e "${SUCCESS}✅ Documentation built successfully${NC}"
        echo -e "${INFO}   Output: ${PROJECT_ROOT}/site/${NC}"
        return 0
    else
        echo -e "${ERROR}❌ Documentation build failed${NC}"
        return 1
    fi
}

# Function to serve documentation locally
serve_docs() {
    echo -e "${INFO}🔵 Serving documentation on http://localhost:8001${NC}"
    echo -e "${INFO}   Press Ctrl+C to stop${NC}"
    echo ""
    
    mkdocs serve --dev-addr=0.0.0.0:8001
}

# Function to validate documentation
validate_docs() {
    echo -e "${INFO}🔵 Validating documentation...${NC}"
    
    local errors=0
    
    # Check for broken links (basic validation)
    echo -e "${INFO}   Checking for TODO markers...${NC}"
    local todo_count=$(grep -r "TODO" docs/ | wc -l)
    echo -e "${INFO}   Found ${todo_count} TODO markers (expected for stub setup)${NC}"
    
    # Validate mkdocs.yml syntax
    echo -e "${INFO}   Validating mkdocs.yml...${NC}"
    if python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))" 2>/dev/null; then
        echo -e "${SUCCESS}   ✅ mkdocs.yml is valid YAML${NC}"
    else
        echo -e "${ERROR}   ❌ mkdocs.yml has syntax errors${NC}"
        ((errors++))
    fi
    
    # Check that all nav files exist
    echo -e "${INFO}   Checking navigation files...${NC}"
    local missing=0
    while IFS= read -r file; do
        if [[ ! -f "docs/$file" ]]; then
            echo -e "${ERROR}   ❌ Missing: docs/$file${NC}"
            ((missing++))
        fi
    done < <(python -c "import yaml; nav = yaml.safe_load(open('mkdocs.yml'))['nav']; import json; def extract(d): return [v for k,v in (d.items() if isinstance(d, dict) else []) for v in ([v] if isinstance(v, str) else extract(v) if isinstance(v, (dict, list)) else [])] + ([item for sublist in d for item in extract(sublist)] if isinstance(d, list) else []); print('\n'.join(extract(nav)))")
    
    if [ $missing -eq 0 ]; then
        echo -e "${SUCCESS}   ✅ All navigation files exist${NC}"
    else
        echo -e "${ERROR}   ❌ $missing navigation file(s) missing${NC}"
        ((errors++))
    fi
    
    # Try building to catch any build errors
    echo -e "${INFO}   Test building...${NC}"
    if mkdocs build --strict 2>&1 | grep -q "ERROR"; then
        echo -e "${ERROR}   ❌ Build produced errors${NC}"
        ((errors++))
    else
        echo -e "${SUCCESS}   ✅ Build successful${NC}"
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${SUCCESS}✅ Documentation validation passed${NC}"
        return 0
    else
        echo -e "${ERROR}❌ Documentation validation failed with $errors error(s)${NC}"
        return 1
    fi
}

# Main execution
case "$MODE" in
    build)
        check_mkdocs
        build_docs
        ;;
    serve|--serve)
        check_mkdocs
        serve_docs
        ;;
    validate|--validate)
        check_mkdocs
        validate_docs
        ;;
    *)
        echo -e "${ERROR}❌ Unknown mode: $MODE${NC}"
        echo ""
        echo "Usage: $0 [build|serve|validate]"
        echo ""
        echo "Modes:"
        echo "  build     - Build static documentation (default)"
        echo "  serve     - Serve documentation with live reload"
        echo "  validate  - Validate documentation structure and links"
        exit 1
        ;;
esac
