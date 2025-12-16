# Contributing to Codemate Hub

Thank you for your interest in contributing to Codemate Hub! This guide will help you get started.

## Quick Links

- 📖 [Development Documentation](docs/development/setup.md)
- 🧪 [Testing Guide](docs/development/testing.md)
- 🐛 [Troubleshooting](TROUBLESHOOTING.md)
- 📋 [Project Tracker](trackers/PLAN.md)

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/codemate-hub.git
cd codemate-hub
```

### 2. Set Up Development Environment

```bash
# Run preflight checks
./scripts/preflight-check.sh

# Build the project
./scripts/build.sh

# Deploy in development mode
./scripts/deploy.sh
```

For detailed setup instructions, see [Development Setup](docs/development/setup.md).

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

## Development Workflow

### Code Quality Standards

#### Python Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type Hints**: Required for public APIs
- **Docstrings**: Google style

```python
def example_function(param: str, count: int = 0) -> dict[str, Any]:
    """Brief description of the function.

    Longer description if needed, explaining the purpose and behavior.

    Args:
        param: Description of param.
        count: Description of count. Defaults to 0.

    Returns:
        Dictionary containing results.

    Raises:
        ValueError: If param is empty.
    """
    if not param:
        raise ValueError("param cannot be empty")
    return {"param": param, "count": count}
```

#### Running Code Quality Tools

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Run all checks
black --check src/ tests/
ruff check src/ tests/
```

### Testing

All contributions should include appropriate tests.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline.py

# Run with coverage
pytest --cov=src --cov-report=html
```

See [Testing Guide](docs/development/testing.md) for more details.

### Documentation

#### Updating Documentation

When adding or modifying features:

1. Update relevant documentation in `docs/`
2. Update API documentation if public APIs changed
3. Add examples and usage instructions
4. Update README.md if needed

#### Building Documentation Locally

```bash
# Build documentation
./scripts/docs-build.sh build

# Serve with live reload
./scripts/docs-build.sh serve

# Validate documentation
./scripts/docs-build.sh validate
```

Visit http://localhost:8001 to view the documentation.

#### Documentation Structure

```
docs/
├── getting-started/    # User-facing guides
├── architecture/       # System design documentation
├── api-reference/      # Auto-generated API docs
├── development/        # Developer guides
└── guides/            # How-to guides
```

#### Writing Documentation

- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Use admonitions for notes, warnings, tips:

```markdown
!!! note
    This is a note.

!!! warning
    This is a warning.

!!! tip
    This is a helpful tip.
```

## Commit Guidelines

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Build process, dependency updates, etc.

Examples:

```
feat(orchestrator): add parallel task execution

Implements TaskOrchestrator.execute_tasks_parallel() with configurable
concurrency limits and proper error handling.

Closes #42
```

```
fix(pipeline): handle empty model responses

Adds validation for empty responses from Ollama API to prevent
downstream errors.

Fixes #38
```

```
docs(guides): add GPU setup guide

Comprehensive guide for configuring NVIDIA GPU support with
nvidia-docker and performance tuning recommendations.
```

## Pull Request Process

### Before Submitting

1. **Update from main branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run all checks**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   pytest
   ```

3. **Update documentation**
   - Update relevant docs in `docs/`
   - Build and review documentation locally
   - Update CHANGELOG.md if applicable

### Submitting the PR

1. Push your branch to your fork
   ```bash
   git push origin your-feature-branch
   ```

2. Open a Pull Request on GitHub

3. Fill out the PR template with:
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes
   - Testing instructions

### PR Review Checklist

Your PR will be reviewed for:

- [ ] Code quality and style compliance
- [ ] Test coverage for new code
- [ ] Documentation updates
- [ ] No breaking changes (or properly documented)
- [ ] Commits follow conventional commits
- [ ] CI/CD checks pass

## Project Structure

```
codemate-hub/
├── docs/               # Documentation source
├── scripts/            # Operational scripts
├── src/                # Python application code
│   ├── pipeline.py     # Main pipeline
│   ├── orchestrator.py # Task orchestration
│   ├── agents.py       # Agent management
│   └── ...
├── tests/              # Test suite
├── trackers/           # Project planning and tracking
├── docker-compose.yml  # Service definitions
└── mkdocs.yml         # Documentation configuration
```

## Development Tips

### Working with Docker

```bash
# Rebuild specific service
docker compose build app

# View logs
docker compose logs -f app

# Shell into container
docker exec -it coding-assistant bash

# Restart services
docker compose restart
```

### Debugging

- Use `docker compose logs -f [service]` for service logs
- Add breakpoints with `import pdb; pdb.set_trace()`
- Enable debug logging in code
- See [Debugging Guide](docs/development/debugging.md)

### Common Tasks

```bash
# Add Python dependency
# Edit pyproject.toml, then:
uv lock --python 3.12.11
uv sync --python 3.12.11
docker compose build app

# Pull new model
./scripts/model-pull.sh mistral:latest

# Check service health
./scripts/check-health.sh 120

# Run integration tests
./scripts/test-integration.sh
```

## Getting Help

- 📖 Check the [documentation](http://localhost:8001)
- 🐛 Search [existing issues](https://github.com/tzervas/codemate-hub/issues)
- 💬 Start a [discussion](https://github.com/tzervas/codemate-hub/discussions)
- 📧 Contact maintainers: tz-dev@vectorweight.com

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the best outcome for the project
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Codemate Hub! 🚀
