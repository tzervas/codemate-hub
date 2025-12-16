# Codemate Hub Documentation

This directory contains the source files for the Codemate Hub documentation site.

## Quick Start

### View Documentation Locally

```bash
# From project root
./scripts/docs-build.sh serve
```

Visit http://localhost:8001 to view the documentation with live reload.

### Build Static Site

```bash
# From project root
./scripts/docs-build.sh build
```

Output will be in `site/` directory.

### Validate Documentation

```bash
# From project root
./scripts/docs-build.sh validate
```

Checks for:
- MkDocs configuration validity
- Navigation file existence
- Build errors
- TODO markers (informational)

## Structure

```
docs/
├── index.md                 # Homepage
├── getting-started/         # User guides
├── architecture/            # System design
├── api-reference/           # API documentation
├── development/             # Developer guides
├── guides/                  # How-to guides
└── DOCUMENTATION_SETUP.md   # This setup guide
```

## Adding New Pages

1. Create a new markdown file in the appropriate directory
2. Add the page to navigation in `mkdocs.yml`:
   ```yaml
   nav:
     - Section Name:
       - Page Title: path/to/file.md
   ```
3. Preview with `./scripts/docs-build.sh serve`
4. Validate with `./scripts/docs-build.sh validate`

## Writing Guidelines

### Markdown Basics

- Use `#` for headings (increasing for deeper levels)
- Use triple backticks for code blocks with language tags
- Use `[text](link)` for links (relative paths for internal docs)

### Admonitions

```markdown
!!! note "Optional Title"
    Note content here

!!! warning
    Warning content

!!! tip
    Helpful tip

!!! info "TODO"
    Marks planned content
```

### Code Examples

````markdown
```python
def example():
    """Docstring here"""
    return "Hello, World!"
```
````

### API Documentation

For documented Python modules:

```markdown
::: src.module_name
    options:
      show_source: true
```

This will auto-generate documentation from docstrings.

## Current Status

The documentation infrastructure is **complete** and ready for content.

All pages currently have TODO markers indicating what content needs to be added. This is expected for the stub/scaffolding phase.

See [DOCUMENTATION_SETUP.md](DOCUMENTATION_SETUP.md) for complete setup details.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for documentation style guidelines and workflows.

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material Theme Docs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
