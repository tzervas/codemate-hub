# Codemate Hub Documentation

Welcome to the comprehensive documentation for **Codemate Hub** - a containerized multi-service platform for running an AI-powered coding assistant with Ollama, Langflow, and a development environment.

## What is Codemate Hub?

Codemate Hub is a Dockerized agentic coding assistant that combines:

- **Ollama**: Local LLM inference engine for running AI models
- **Langflow**: Visual workflow orchestration for AI pipelines
- **Code-Server**: Remote VS Code IDE for development
- **Python App**: CrewAI-powered coding assistant with signal-based orchestration

## Quick Links

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __Quick Start__

    ---

    Get up and running in minutes with our step-by-step guide

    [:octicons-arrow-right-24: Getting Started](getting-started/quick-start.md)

-   :material-book-open-variant:{ .lg .middle } __Architecture__

    ---

    Understand the system design and component interactions

    [:octicons-arrow-right-24: Architecture Overview](architecture/overview.md)

-   :material-code-braces:{ .lg .middle } __API Reference__

    ---

    Detailed API documentation for all components

    [:octicons-arrow-right-24: API Docs](api-reference/index.md)

-   :material-tools:{ .lg .middle } __Development__

    ---

    Learn how to contribute and develop features

    [:octicons-arrow-right-24: Development Guide](development/setup.md)

</div>

## Features

- **🚀 Fast Deployment**: Single-command deployment with Docker Compose
- **🤖 AI-Powered**: Multiple LLM models for code generation and assistance
- **🔧 Extensible**: Plugin-based architecture with CrewAI agents
- **📊 Visual Workflows**: Langflow integration for workflow design
- **🔒 Secure**: Isolated execution with enclave support (in development)
- **📚 Memory System**: ChromaDB-powered vector memory for context retention

## System Requirements

- **Docker** and **Docker Compose**
- **10+ GB** free disk space (for models)
- **Linux** host (or Windows/Mac with Docker Desktop)
- **Optional**: NVIDIA GPU with nvidia-docker for acceleration

## Getting Help

- 📖 Check our [Troubleshooting Guide](guides/troubleshooting.md)
- 🐛 Report issues on [GitHub](https://github.com/tzervas/codemate-hub/issues)
- 💬 Join discussions in [GitHub Discussions](https://github.com/tzervas/codemate-hub/discussions)

## Project Status

Codemate Hub is currently in **active development** (v0.4.0). Core features are functional, with ongoing work on:

- Enhanced enclave security (Task 05)
- Langflow integration improvements (Task 04)
- Developer experience enhancements (Task 06)
- Comprehensive documentation (Task 08)

See our [project tracker](https://github.com/tzervas/codemate-hub/tree/main/trackers) for detailed progress.
