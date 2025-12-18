FROM mcr.microsoft.com/devcontainers/python:0-3.12

# Install lightweight tooling commonly used during development
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        vim \
        ca-certificates \
        sudo \
        iproute2 \
        ssh \
        docker.io \
        docker-compose-plugin \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a workspace directory and make sure permissions are correct for the
# default non-root 'vscode' user the devcontainer uses.
WORKDIR /workspace
RUN chown -R vscode:vscode /workspace || true

# Ensure user-installed Python tools are on PATH by default
ENV PATH="$HOME/.local/bin:$PATH"

# Default command
CMD ["bash"]