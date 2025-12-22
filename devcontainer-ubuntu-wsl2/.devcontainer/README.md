# Development Container for Ubuntu on WSL2

This README provides information on setting up and using the development container configured for Ubuntu on a Windows machine using WSL2.

## Overview

This project utilizes a development container to create a consistent and portable development environment. The container is based on Ubuntu and is designed to work seamlessly with Visual Studio Code.

## Getting Started

### Prerequisites

- Windows 10 or later
- WSL2 installed and configured
- Docker Desktop installed and running
- Visual Studio Code installed
- Remote - Containers extension for Visual Studio Code

### Setup Instructions

1. **Clone the Repository**: 
   Clone this repository to your local machine.

   ```bash
   git clone <repository-url>
   cd devcontainer-ubuntu-wsl2
   ```

2. **Open in Visual Studio Code**: 
   Open the project folder in Visual Studio Code.

3. **Reopen in Container**: 
   Use the Command Palette (Ctrl+Shift+P) and select `Remote-Containers: Reopen in Container`. This will build the Docker image and start the container.

4. **Post-Create Commands**: 
   The `postCreateCommand.sh` script will run automatically after the container is created, installing any necessary dependencies.

## Customization

- Modify the `devcontainer.json` file to change the configuration of the development container.
- Update the `Dockerfile` to include additional packages or tools as needed.
- Use the `devcontainer.env` file to set environment variables for your development environment.

## Usage

Once the container is running, you can start developing your application. The source code can be found in the `src` directory. 

## Troubleshooting

If you encounter any issues, check the logs in the terminal for error messages. Ensure that Docker is running and that WSL2 is properly configured.

## Windows / PowerShell notes

- If you are launching the container from Windows, make sure Docker Desktop is configured to use WSL2 as the backend and ensure any required WSL2 distributions are enabled. From PowerShell, you can verify WSL status:

```powershell
wsl --status
Get-Service -Name docker
```

- Opening the repo in VS Code and using `Remote-Containers: Reopen in Container` (or the `Dev Containers` command in newer versions) should build the devcontainer. If you prefer to use the command line, open a WSL terminal and run:

```powershell
# From PowerShell: use the helper script to open the devcontainer folder in VS Code
scripts\open-devcontainer.ps1
# Then inside VS Code: 'Dev Containers: Reopen in Container' via the Command Palette
```

## Enabling Raptor mini (Preview) for all clients

There are two ways to enable Raptor mini depending on whether you want to enable it for this workspace or enable it for all organization users in GitHub (admin required).

1. Workspace-level (per-repository or per-user):

    - Add the following entries to `.vscode/settings.json` so clients opening this workspace will receive the setting from the repository (VS Code will prompt users to accept workspace settings):

       ```json
       {
          "github.copilot": {
             "enable": true,
             "experimental": {
                "enableRaptorMini": true
             }
          }
       }
       ```

    - Not all clients or Copilot builds may respect experimental settings. If the setting isn't available yet on a particular version, the setting will simply be ignored.

2. Organization-level (Admin action):

    - Org administrators can enable experimental model selection for all users by visiting the organization Copilot settings (https://github.com/organizations/<org>/settings/copilot) and toggling the option to allow experimental models or enabling specific models if available.

    - For GitHub Enterprise customers, check the admin console for Copilot configuration and model rollout controls.

If you need help configuring this centrally, share the organization details and I can provide the exact steps based on your GitHub subscription (Enterprise / Team / Free).

For strict, org-only enablement instructions (recommended for `vector-weight` org and personal account `tzervas`) see: `docs/ENABLE_RAPTOR_MINI.md`.

## Additional Resources

- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Documentation](https://docs.docker.com/)
- [Visual Studio Code Remote - Containers](https://code.visualstudio.com/docs/remote/containers)

Feel free to reach out if you have any questions or need further assistance!