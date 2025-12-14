#!/usr/bin/env bash
set -euo pipefail

# Changelog helper
# Usage:
#   scripts/changelog.sh check       # verify trackers vs CHANGELOG (no git, no history)
#   scripts/changelog.sh regen       # regenerate changelog (no git enrichment)
#   scripts/changelog.sh full        # regenerate with git enrichment (for merge)

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

uv_run() {
  uv run python tools/chngbrgr.py "$@"
}

case "${1:-}" in
  check)
    uv_run --check --no-git ;;
  regen)
    uv_run --no-git ;;
  full)
    uv_run ;;
  *)
    echo "Usage: $0 {check|regen|full}" >&2
    exit 1 ;;
esac
