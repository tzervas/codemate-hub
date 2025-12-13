#!/usr/bin/env bash
# Prune unused Ollama models and manage disk usage
# Usage: ./scripts/model-prune.sh [keep-models|list-unused|dry-run]
# Examples:
#   ./scripts/model-prune.sh list-unused      # Show unused models
#   ./scripts/model-prune.sh dry-run          # Preview what would be deleted
#   ./scripts/model-prune.sh keep-models      # Keep specified models, remove rest

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Models to always keep (never prune)
PROTECTED_MODELS=(
  "qwen2.5-coder:7b-q4_0"
  "mistral:latest"
)

function list_local_models() {
  # List all locally cached models
  docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama list
}

function get_model_names() {
  # Extract model names from ollama list output
  list_local_models | awk 'NR>1 {print $1}' | sed 's/:latest$//'
}

function is_protected() {
  # Check if a model is in the protected list
  local model=$1
  for protected in "${PROTECTED_MODELS[@]}"; do
    if [[ "$model" == "$protected" ]] || [[ "$model" == "${protected%:*}" ]]; then
      return 0
    fi
  done
  return 1
}

function get_model_size() {
  # Get approximate size of a model from ollama show command
  local model=$1
  docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama show "$model" 2>/dev/null | \
    grep -i "parameters\|size" | head -1 | awk '{print $NF}' || echo "unknown"
}

function list_unused_models() {
  # List all models that could be pruned (non-protected)
  log_info "Scanning for prunable models..."
  echo ""
  
  local models=()
  while IFS= read -r model; do
    if [[ -n "$model" ]] && ! is_protected "$model"; then
      models+=("$model")
    fi
  done < <(get_model_names)
  
  if [ ${#models[@]} -eq 0 ]; then
    log_success "All local models are protected"
    return 0
  fi
  
  echo "The following models can be pruned:"
  echo ""
  for model in "${models[@]}"; do
    local size=$(get_model_size "$model")
    printf "  • %-40s %s\n" "$model" "($size)"
  done
  echo ""
  echo "Protected models (will NOT be pruned):"
  for protected in "${PROTECTED_MODELS[@]}"; do
    echo "  • $protected"
  done
}

function dry_run_prune() {
  # Show what would be deleted without actually deleting
  log_info "Dry-run: Showing models that would be pruned..."
  echo ""
  
  local prune_count=0
  local total_estimate="0B"
  
  while IFS= read -r model; do
    if [[ -n "$model" ]] && ! is_protected "$model"; then
      ((prune_count++))
      local size=$(get_model_size "$model")
      echo "  [WOULD DELETE] $model ($size)"
    fi
  done < <(get_model_names)
  
  echo ""
  if [ $prune_count -eq 0 ]; then
    log_success "No models to prune"
  else
    log_warn "Dry-run: Would delete $prune_count model(s)"
    echo ""
    echo "To actually prune, run: ./scripts/model-prune.sh keep-models"
  fi
}

function prune_models() {
  # Actually prune non-protected models
  log_warn "Pruning models (this cannot be undone)..."
  echo ""
  
  local prune_count=0
  local failed=0
  
  while IFS= read -r model; do
    if [[ -n "$model" ]] && ! is_protected "$model"; then
      log_info "Pruning: $model"
      
      if docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama rm "$model" > /dev/null 2>&1; then
        log_success "Removed $model"
        ((prune_count++))
      else
        log_error "Failed to remove $model"
        ((failed++))
      fi
    fi
  done < <(get_model_names)
  
  echo ""
  log_success "Pruning complete"
  log_success "Removed: $prune_count model(s)"
  
  if [ $failed -gt 0 ]; then
    log_warn "Failed: $failed model(s)"
    return 1
  fi
  
  # Show remaining models
  echo ""
  log_info "Remaining protected models:"
  list_local_models
}

function show_help() {
  cat << EOF
Model Pruning & Disk Usage Management

Usage: $0 [COMMAND]

Commands:
  list-unused         List all models that can be pruned (not protected)
  dry-run             Preview what would be deleted (no changes made)
  keep-models         Actually prune all non-protected models (DESTRUCTIVE)

Protected Models (never deleted):
$(printf '  • %s\n' "${PROTECTED_MODELS[@]}")

Examples:
  # See what can be pruned
  ./scripts/model-prune.sh list-unused
  
  # Preview deletion
  ./scripts/model-prune.sh dry-run
  
  # Actually delete unused models
  ./scripts/model-prune.sh keep-models

Disk Usage Management:
- Run 'list-unused' or 'dry-run' before pruning to verify
- Protected models are never removed (see list above)
- To add/remove models from protected list, edit PROTECTED_MODELS in this script
- Consider running daily/weekly for large model collections

Notes:
- Model sizes shown are estimates from ollama metadata
- Actual disk usage in ollama_data volume may vary
- Use 'docker system df' to see total Docker disk usage

EOF
}

# Main logic
COMMAND=${1:-list-unused}

case "$COMMAND" in
  list-unused)
    list_unused_models
    ;;
  dry-run)
    dry_run_prune
    ;;
  keep-models)
    prune_models
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    log_error "Unknown command: $COMMAND"
    echo ""
    show_help
    exit 1
    ;;
esac
