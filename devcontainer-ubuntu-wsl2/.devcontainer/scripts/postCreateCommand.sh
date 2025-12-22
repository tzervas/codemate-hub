#!/bin/bash
set -euo pipefail

# Update package lists and install base tooling. This script runs as the
# non-root 'vscode' user in the devcontainer, so use sudo when needed.
sudo apt-get update
sudo apt-get install -y --no-install-recommends build-essential git curl python3-venv python3-distutils
sudo apt-get clean

# Install uv (dependency manager used by the project) for the current user.
if ! command -v uv >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --version 0.7.18
fi

# Make sure ~/.local/bin is on PATH for this script's session
export PATH="$HOME/.local/bin:$PATH"

# Ensure Python 3.12 is available in the container
PY_BIN=$(which python3 || true)
if [ -z "$PY_BIN" ]; then
	echo "python3 not found - you may need to rebuild the container based on a Python image. Skipping uv sync."
else
	# Create a virtual environment for the container workspace and sync dependencies
	python3 -m venv .venv || true
	. .venv/bin/activate
	# Use project helper to manage uv lock & venv sync
	if [ -x "$(pwd)/scripts/uv-python-manage.sh" ] || [ -f "$(pwd)/scripts/uv-python-manage.sh" ]; then
		bash "$(pwd)/scripts/uv-python-manage.sh" 3.12.11 || echo "uv python manage failed (will continue)"
	else
		if command -v uv >/dev/null 2>&1; then
			uv sync --python 3.12.11 || echo "uv sync failed (will continue)"
		fi
	fi
fi

echo "Post-create setup completed."