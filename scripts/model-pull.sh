#!/usr/bin/env bash
# Pull and manage Ollama models into local cache
# Usage: ./scripts/model-pull.sh [model_name|list|default]
# Examples:
#   ./scripts/model-pull.sh default        # Pull all default models
#   ./scripts/model-pull.sh list           # List available models on hub
#   ./scripts/model-pull.sh mistral        # Pull specific model

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Default models: balanced set for coding assistant
# qwen2.5-coder: 7B coding-optimized model (primary)
# mistral: 7B general-purpose (fallback)
# neural-chat: 7B instruction-tuned (alternative)
DEFAULT_MODELS=(
  "qwen2.5-coder:7b-q4_0"
  "mistral:latest"
)

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function log_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

function log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

function log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

function log_error() {
  echo -e "${RED}✗${NC} $1" >&2
}

function list_available_models() {
  log_info "Querying Ollama Hub for available models..."
  log_info "Top recommended models for coding:"
  echo "  • qwen2.5-coder:7b-q4_0   - Qwen 2.5 Coder (7B, quantized)"
  echo "  • mistral:latest          - Mistral 7B (versatile)"
  echo "  • neural-chat:latest      - Neural Chat (instruction-tuned)"
  echo "  • llama2:latest           - Llama 2 (meta's model)"
  echo ""
  echo "For full list, visit: https://ollama.ai/library"
}

function pull_model() {
  local model=$1
  log_info "Pulling model: $model"
  
  if docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama pull "$model"; then
    log_success "Model $model pulled successfully"
    return 0
  else
    log_error "Failed to pull model $model"
    return 1
  fi
}

function list_local_models() {
  log_info "Local models:"
  docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama list
}

function pull_default_models() {
  log_info "Pulling default models..."
  local failed=0
  
  for model in "${DEFAULT_MODELS[@]}"; do
    if ! pull_model "$model"; then
      ((failed++))
    fi
  done
  
  echo ""
  if [ $failed -eq 0 ]; then
    log_success "All default models pulled successfully"
  else
    log_warn "$failed model(s) failed to pull"
    return 1
  fi
  
  list_local_models
}

# Main script logic
COMMAND=${1:-default}

case "$COMMAND" in
  list)
    list_available_models
    ;;
  default)
    pull_default_models
    ;;
  *)
    # Assume it's a model name
    pull_model "$COMMAND"
    echo ""
    list_local_models
    ;;
esac
