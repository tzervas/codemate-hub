# Documentation Setup Summary

This document provides a quick reference for the documentation infrastructure setup in Codemate Hub.

## Overview

Codemate Hub uses **MkDocs** with the **Material theme** to provide comprehensive, self-hosted documentation that deploys automatically with the stack.

## Key Components

### 1. Documentation Service (Docker)

- **Container**: `docs-site`
- **Port**: 8001
- **Dockerfile**: `Dockerfile.docs`
- **Live Reload**: Yes (development mode)
- **Build Command**: `mkdocs serve --dev-addr=0.0.0.0:8001`

### 2. Documentation Structure

```
docs/
├── index.md                    # Homepage with quick links
├── getting-started/            # User-facing guides
│   ├── quick-start.md
│   ├── installation.md
│   ├── configuration.md
│   └── first-steps.md
├── architecture/               # System design
│   ├── overview.md
│   ├── services.md
│   ├── data-flow.md
│   └── signal-system.md
├── api-reference/              # Auto-generated API docs
│   ├── index.md
│   ├── pipeline.md
│   ├── orchestrator.md
│   ├── agents.md
│   └── task-manager.md
├── development/                # Developer guides
│   ├── setup.md
│   ├── contributing.md
│   ├── testing.md
│   └── debugging.md
└── guides/                     # How-to guides
    ├── model-management.md
    ├── memory-persistence.md
    ├── gpu-support.md
    └── troubleshooting.md
```

### 3. Automation Scripts

#### docs-build.sh

```bash
./scripts/docs-build.sh build      # Build static site to site/
./scripts/docs-build.sh serve      # Serve with live reload at :8001
./scripts/docs-build.sh validate   # Validate structure and links
```

#### docs-generate.sh

```bash
./scripts/docs-generate.sh         # Generate API docs from Python docstrings
```

## Configuration

### mkdocs.yml

Key configuration settings:

- **Theme**: Material with dark/light mode toggle
- **Plugins**: search, mkdocstrings (for API docs)
- **Extensions**: admonitions, code highlighting, mermaid diagrams
- **Navigation**: 5 main sections with 30+ pages

### Features Enabled

- ✅ Dark/light theme toggle
- ✅ Search with suggestions and highlighting
- ✅ Code syntax highlighting with copy button
- ✅ Navigation tabs and sections
- ✅ Mermaid diagram support
- ✅ Admonitions (notes, warnings, tips)
- ✅ Auto-generated API documentation (mkdocstrings)

## Development Workflow

### Adding New Documentation

1. Create markdown file in appropriate section (e.g., `docs/guides/new-guide.md`)
2. Add to navigation in `mkdocs.yml`
3. Build and preview: `./scripts/docs-build.sh serve`
4. Validate: `./scripts/docs-build.sh validate`

### Writing Documentation

Follow these conventions:

- Use Google-style docstrings for Python code
- Include code examples in fenced blocks with language tags
- Use admonitions for important notes:
  ```markdown
  !!! note "Title"
      Content here
  
  !!! warning
      Warning content
  
  !!! tip
      Helpful tip
  ```
- Link to other pages with relative paths: `[Link](../section/page.md)`

### API Documentation

For Python modules with comprehensive docstrings, use mkdocstrings:

```markdown
::: src.module_name
    options:
      show_source: true
      heading_level: 3
```

See `docs/api-reference/` for examples.

## Current Status

### Completed

- [x] MkDocs infrastructure setup
- [x] Docker service integration
- [x] 30+ placeholder pages with TODOs
- [x] Automation scripts
- [x] CONTRIBUTING.md guidelines
- [x] README.md documentation section
- [x] Successful local builds
- [x] Validation passing

### TODO (Future Content Creation)

All documentation pages have comprehensive TODO markers indicating what content needs to be added. Key areas:

- **Getting Started**: Complete installation and configuration guides
- **Architecture**: System diagrams and detailed component descriptions  
- **API Reference**: Add docstrings to Python modules for auto-generation
- **Development**: Setup instructions and debugging guides
- **Guides**: Model management, GPU setup, troubleshooting details

## Accessing Documentation

### Local Development

```bash
./scripts/docs-build.sh serve
# Visit http://localhost:8001
```

### Deployed Stack

Once deployed with `./scripts/deploy.sh`:

- **URL**: http://localhost:8001
- **Auto-reload**: Yes (in development mode)
- **Build on start**: Yes

## CI/CD Considerations

- Documentation builds with `mkdocs build --strict` in CI
- SSL certificate issues may occur in some CI environments (known issue)
- Dockerfile is production-ready despite CI build limitations
- Static site builds to `site/` directory (excluded in .gitignore)

## Resources

- **MkDocs**: https://www.mkdocs.org/
- **Material Theme**: https://squidfunk.github.io/mkdocs-material/
- **mkdocstrings**: https://mkdocstrings.github.io/
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)

## Questions?

- Check [CONTRIBUTING.md](../CONTRIBUTING.md) for documentation guidelines
- Review existing pages in `docs/` for examples
- Run `./scripts/docs-build.sh validate` to check for issues
- See [README.md](../README.md) for deployment information
