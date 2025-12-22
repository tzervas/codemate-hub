#!/usr/bin/env bash
set -euo pipefail

# Convenience script for managing Python version & dependencies with uv
# Usage: ./scripts/uv-python-manage.sh [python_version]
# Default Python version: 3.12.11 (pinned in pyproject.toml)

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_VERSION=${1:-3.12.11}

echo "[uv-python-manage] Target Python: $PY_VERSION"

# Ensure we can find user-local installs
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found; attempting to install uv (user-local)..."
  if curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --version 0.7.18; then
    echo "Installed uv via installer (requested version)"
  else
    echo "uv installer didn't accept explicit version; falling back to default install"
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi

cd "$PROJECT_ROOT"

echo "Locking dependencies for Python $PY_VERSION (uv lock)"
uv lock --python $PY_VERSION || echo "uv lock failed; check network or permission"

echo "Creating venv (if missing) and syncing dependencies"
# Create a workspace virtualenv and activate it
python3 -m venv .venv || true
. .venv/bin/activate

if command -v uv >/dev/null 2>&1; then
    uv sync --python $PY_VERSION || echo "uv sync failed (host may not have that Python version); try running this inside the devcontainer"
else
    echo "uv is not available after install; skipping sync"
fi

echo "Done. The project lockfile (uv.lock) and venv are now in sync (if Python $PY_VERSION is available)."
