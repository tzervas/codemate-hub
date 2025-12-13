# Tooling & Dependency Management

## Python Dependency Resolution

### Tool: uv

We use **[uv](https://github.com/astral-sh/uv)** for all Python dependency management and resolution.

**Why uv?**
- **Fast**: Resolves dependencies 10-100x faster than pip
- **Reliable**: Proper dependency conflict detection and resolution
- **Reproducible**: Generates `uv.lock` for exact version pinning
- **Multi-version support**: Handles complex multi-platform constraints elegantly
- **Modern**: Written in Rust for better performance and safety

### Installation

```bash
# Local development (pin to project toolchain)
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --version 0.7.18

# In CI (mirrors local install)
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --version 0.7.18
echo "$HOME/.local/bin" >> $GITHUB_PATH
```

## Dependency Resolution Strategy

### pyproject.toml
Primary dependency specification. Defines exact versions and constraints.

### uv.lock
Generated lock file from `uv lock` command. Ensures reproducible installs across all environments.

**Generate/Update:**
```bash
uv lock --python 3.12.11
```

### uv sync
Synchronizes the local environment with `uv.lock` specifications.

**Usage:**
```bash
# Development environment
uv sync --python 3.12.11

# CI (frozen, no updates)
uv sync --python 3.12.11 --frozen
```

## Dependency Conflicts Resolved

### Conflict: aider-chat vs crewai
- **Issue**: `aider-chat==0.58.0` requires `regex==2024.9.11`
- **Issue**: `crewai==0.51.1` requires `regex>=2023.12.25,<2024.0.0`
- **Resolution**: Removed `aider-chat` from core dependencies
- **Reason**: `aider-chat` is not essential for current task (Models & Data)
- **Future**: Can be re-evaluated when versions are compatible or crewai upgrades

### Successfully Resolved Dependencies
- `langchain` ecosystem (langchain, langchain-community, langchain-chroma)
- `ollama` with embeddings integration
- `sentence-transformers` for model management
- `pydantic` for validation
- `crewai` for agent framework

**Total resolved**: 213 packages with zero conflicts

## Python Version

- **Target**: Python 3.12.11 (pinned)
- **CI**: Uses Python 3.12.11 via `setup-python` action  
- **Local**: `uv` automatically installs/uses 3.12.11 based on `pyproject.toml`
- **Note**: Python 3.13 remains unsupported until dependent native extensions update.


## Dependency Installation in CI

### python-checks Job
```bash
uv sync --python 3.12.11 --frozen
```
Installs all dependencies including optional dev dependencies.

### memory-initialization Job
```bash
uv sync --python 3.12.11 --frozen
```
Uses the same frozen lock for consistency.

## Local Development

### First Time Setup
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --version 0.7.18

# Sync environment
uv sync --python 3.12.11
```

### Running Commands
```bash
# Python scripts
uv run python src/memory_setup.py

# With specific version
uv run --python 3.12.11 python src/pipeline.py

# Direct execution (uses synced environment)
python src/app.py
```

### Adding Dependencies
```bash
# Add new package
uv add package-name==version

# Update lock file
uv lock
```

## Future Considerations

1. **Optional Dependencies**: Can add `[dev]`, `[test]`, `[docs]` extras to `pyproject.toml`
2. **Dependency Upgrades**: Use `uv update` to safely upgrade packages
3. **Conflict Monitoring**: GitHub Dependabot alerts on security issues
4. **Lock File Verification**: Always commit `uv.lock` to ensure reproducibility

## Troubleshooting

### Dependency Conflict
If `uv lock` reports unsatisfiable requirements:
1. Check conflicting package versions
2. Look for newer versions that resolve conflicts
3. Remove non-essential packages blocking resolution
4. Document the decision in this file

### Sync Failures
If `uv sync` fails:
```bash
# Clear cache and retry
rm -rf .venv
uv sync --python 3.12.11
```

### Version Pinning
For strict reproducibility across all environments:
- Commit `uv.lock` to version control
- Use `--frozen` flag in CI to prevent automatic updates
- Review Dependabot alerts regularly

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [pyproject.toml Spec](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [PEP 508 - Dependency Specifiers](https://www.python.org/dev/peps/pep-0508/)
