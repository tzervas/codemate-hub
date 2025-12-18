# Development Container for Ubuntu on WSL2

This project sets up a development container using Ubuntu on a Windows machine with WSL2. The container is designed to provide a consistent development environment that can be easily shared and replicated.

## Project Structure

The project consists of the following key components:

- **.devcontainer/**: Contains all the configuration files necessary for the development container.
  - **devcontainer.json**: Configuration for the development container.
  - **Dockerfile**: Instructions to build the Docker image.
  - **docker-compose.yml**: Defines services and configurations for multi-container applications.
  - **devcontainer.env**: Environment variables for the container.
  - **scripts/**: Contains scripts that run during the container setup.
    - **postCreateCommand.sh**: Script for additional setup tasks after container creation.
  - **README.md**: Documentation specific to the development container setup.

- **.vscode/**: Contains Visual Studio Code specific settings and extensions.
  - **settings.json**: Workspace-specific settings.
  - **extensions.json**: Recommended extensions for the project.

- **src/**: Contains the source code for the project.
  - **README.md**: Documentation for the source code directory.

- **.gitignore**: Specifies files and directories to be ignored by Git.

- **README.md**: Main documentation for the project, including setup instructions and usage guidelines.

## Getting Started

1. **Install WSL2**: Ensure that WSL2 is installed and set up on your Windows machine.
2. **Clone the Repository**: Clone this repository to your local machine.
3. **Open in VS Code**: Open the project folder in Visual Studio Code.
4. **Reopen in Container**: Use the command palette (Ctrl+Shift+P) and select "Remote-Containers: Reopen in Container" to build and start the development container.

## Usage

Once the container is running, you can start developing your application within the Ubuntu environment. Any dependencies or tools specified in the Dockerfile or postCreateCommand.sh will be available for use.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests. Make sure to follow the project's coding standards and guidelines.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.