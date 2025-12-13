# GitHub Configuration & AI Agent Guides

This directory contains GitHub-specific configurations and documentation for AI coding assistants.

## For AI Agents

**START HERE:** [copilot-instructions.md](copilot-instructions.md)

Quick reference guide with:
- Architecture overview and data flows
- Critical developer workflows (build, deploy, test)
- Python dependency management with `uv`
- Common gotchas and troubleshooting tips
- Direct links to authoritative documentation

## For Developers

**Finding Documentation:** [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md)

Comprehensive index mapping every task to its authoritative documentation:
- Getting started & deployment
- Development workflows
- Operations & maintenance
- Troubleshooting by error type
- Configuration reference
- Scripts reference

## Documentation Structure

This project follows a "single source of truth" approach:

| Document | Purpose | Audience |
|----------|---------|----------|
| [../README.md](../README.md) | Complete user guide: setup, commands, all operations | Everyone |
| [../TOOLING.md](../TOOLING.md) | Python/uv dependency management specifics | Developers |
| [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Error-indexed problem solving (649 lines) | Operations |
| [../trackers/](../trackers/) | Project planning, architecture, specifications | Contributors |
| [copilot-instructions.md](copilot-instructions.md) | AI agent quick reference with links | AI Agents |
| [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md) | Topic→documentation mapper | Everyone |

## Key Principle

**This directory provides navigation and AI-specific guidance—it does NOT duplicate content.**

All substantive documentation lives in the repo root and `trackers/`. Files here link to authoritative sources to eliminate confusion and maintain consistency.

## Quick Links

- **First time setup?** → [README.md Quick Start](../README.md#Quick-Start)
- **Something broken?** → [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
- **Adding dependencies?** → [TOOLING.md](../TOOLING.md#Adding-Dependencies)
- **Need command reference?** → [README.md Common Commands](../README.md#Common-Commands)
- **Architecture questions?** → [trackers/OVERVIEW.md](../trackers/OVERVIEW.md)
