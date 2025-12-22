<#
.SYNOPSIS
    Pre-flight checks and deployment validation for the Codemate-Hub cluster.

.DESCRIPTION
    This script performs comprehensive pre-deployment validation including:
    - Docker and Docker Compose availability
    - GPU detection and NVIDIA container toolkit validation
    - Port availability checks
    - Environment configuration validation
    - Network connectivity tests

.PARAMETER SkipGpuCheck
    Skip GPU validation (useful for CPU-only deployments)

.PARAMETER Verbose
    Enable verbose output for debugging

.EXAMPLE
    .\scripts\Deploy-Cluster.ps1
    .\scripts\Deploy-Cluster.ps1 -SkipGpuCheck
#>

[CmdletBinding()]
param(
    [switch]$SkipGpuCheck,
    [switch]$SkipBuild,
    [switch]$Detached = $true,
    [int]$HealthTimeout = 300
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

# Color output helpers
function Write-Status { param($Message) Write-Host "🔵 $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Failure { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

function Test-Prerequisites {
    Write-Status "Running pre-flight checks..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker found: $dockerVersion"
    } catch {
        Write-Failure "Docker is not installed or not in PATH"
        return $false
    }
    
    # Check Docker daemon
    try {
        docker ps | Out-Null
        Write-Success "Docker daemon is running"
    } catch {
        Write-Failure "Docker daemon is not running. Start Docker Desktop."
        return $false
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker compose version
        Write-Success "Docker Compose available: $composeVersion"
    } catch {
        Write-Failure "Docker Compose not available"
        return $false
    }
    
    return $true
}

function Test-GpuAvailability {
    if ($SkipGpuCheck) {
        Write-Warning "GPU check skipped"
        return $false
    }
    
    Write-Status "Checking GPU availability..."
    
    try {
        $nvidiaSmi = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
        if ($nvidiaSmi) {
            Write-Success "NVIDIA GPU detected: $nvidiaSmi"
            
            # Test nvidia-docker
            try {
                docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi 2>$null | Out-Null
                Write-Success "NVIDIA Container Toolkit is working"
                return $true
            } catch {
                Write-Warning "NVIDIA GPU found but container toolkit may not be configured"
                return $false
            }
        }
    } catch {
        Write-Warning "No NVIDIA GPU detected - using CPU-only mode"
    }
    
    return $false
}

function Test-PortAvailability {
    Write-Status "Checking port availability..."
    
    # Load configured ports from .env if available
    $envFile = Join-Path $ProjectRoot ".env"
    $nginxPort = 8888
    $codeServerPort = 8443
    
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        $nginxMatch = $envContent | Select-String "NGINX_PORT=(\d+)"
        $codeMatch = $envContent | Select-String "CODE_SERVER_PORT=(\d+)"
        if ($nginxMatch) { $nginxPort = [int]$nginxMatch.Matches[0].Groups[1].Value }
        if ($codeMatch) { $codeServerPort = [int]$codeMatch.Matches[0].Groups[1].Value }
    }
    
    $requiredPorts = @(
        @{Port = $nginxPort; Service = "Nginx Ingress"},
        @{Port = 3000; Service = "Open-WebUI"},
        @{Port = 7860; Service = "Langflow"},
        @{Port = 7861; Service = "Stable Diffusion"},
        @{Port = 8000; Service = "App API"},
        @{Port = $codeServerPort; Service = "Code-Server"},
        @{Port = 11434; Service = "Ollama"}
    )
    
    $allAvailable = $true
    foreach ($portInfo in $requiredPorts) {
        $connection = Get-NetTCPConnection -LocalPort $portInfo.Port -ErrorAction SilentlyContinue
        if ($connection) {
            Write-Warning "Port $($portInfo.Port) ($($portInfo.Service)) is in use by PID $($connection.OwningProcess)"
            $allAvailable = $false
        }
    }
    
    if ($allAvailable) {
        Write-Success "All required ports are available"
    }
    
    return $allAvailable
}

function Test-EnvironmentConfig {
    Write-Status "Validating environment configuration..."
    
    $envFile = Join-Path $ProjectRoot ".env"
    $envExample = Join-Path $ProjectRoot ".env.example"
    
    if (-not (Test-Path $envFile)) {
        if (Test-Path $envExample) {
            Write-Warning ".env file not found. Creating from .env.example..."
            Copy-Item $envExample $envFile
            Write-Warning "Please edit .env and set PASSWORD before continuing"
            return $false
        } else {
            Write-Failure ".env and .env.example both missing"
            return $false
        }
    }
    
    # Load and validate .env
    $envContent = Get-Content $envFile -Raw
    if ($envContent -notmatch 'PASSWORD\s*=\s*\S+') {
        Write-Failure "PASSWORD not set in .env file"
        return $false
    }
    
    if ($envContent -match 'PASSWORD\s*=\s*your-secure-password-here') {
        Write-Failure "PASSWORD still has default value. Please set a secure password."
        return $false
    }
    
    Write-Success "Environment configuration valid"
    return $true
}

function Test-DiskSpace {
    Write-Status "Checking disk space..."
    
    $drive = (Get-Item $ProjectRoot).PSDrive
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    
    if ($freeSpaceGB -lt 20) {
        Write-Warning "Low disk space: ${freeSpaceGB}GB available. Models require 10-30GB each."
    } else {
        Write-Success "Disk space OK: ${freeSpaceGB}GB available"
    }
    
    return $freeSpaceGB -ge 10
}

function Start-ClusterBuild {
    Write-Status "Building application containers..."
    
    Push-Location $ProjectRoot
    try {
        docker compose build
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Build failed"
            return $false
        }
        Write-Success "Build completed"
        return $true
    } finally {
        Pop-Location
    }
}

function Start-OllamaWithModel {
    Write-Status "Starting Ollama and pulling default model..."
    
    Push-Location $ProjectRoot
    try {
        # Start just Ollama first
        docker compose up -d ollama
        
        # Wait for Ollama to be healthy
        $timeout = 120
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction SilentlyContinue
                if ($response) {
                    Write-Success "Ollama is healthy"
                    break
                }
            } catch { }
            Start-Sleep -Seconds 3
            $elapsed += 3
            Write-Host "." -NoNewline
        }
        Write-Host ""
        
        if ($elapsed -ge $timeout) {
            Write-Warning "Ollama health check timed out, attempting model pull anyway..."
        }
        
        # Pull default model
        Write-Status "Pulling qwen2.5-coder:7b-q4_0 model..."
        docker compose run --rm ollama ollama pull qwen2.5-coder:7b-q4_0
        
        return $true
    } finally {
        Pop-Location
    }
}

function Start-FullCluster {
    Write-Status "Starting full cluster..."
    
    Push-Location $ProjectRoot
    try {
        if ($Detached) {
            docker compose up -d
        } else {
            docker compose up
            return $true  # Won't reach here in attached mode
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Failed to start cluster"
            return $false
        }
        
        Write-Success "Cluster started"
        return $true
    } finally {
        Pop-Location
    }
}

function Wait-ForHealthyServices {
    param([int]$Timeout = 300)
    
    Write-Status "Waiting for services to become healthy (timeout: ${Timeout}s)..."
    
    # Load configured ports from .env if available
    $envFile = Join-Path $ProjectRoot ".env"
    $nginxPort = 8888
    
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        $nginxMatch = $envContent | Select-String "NGINX_PORT=(\d+)"
        if ($nginxMatch) { $nginxPort = [int]$nginxMatch.Matches[0].Groups[1].Value }
    }
    
    $services = @(
        @{Name = "Ollama"; Url = "http://localhost:11434/api/tags"},
        @{Name = "Open-WebUI"; Url = "http://localhost:3000/health"},
        @{Name = "Langflow"; Url = "http://localhost:7860/"},
        @{Name = "Nginx Ingress"; Url = "http://localhost:$nginxPort/"}
    )
    
    $startTime = Get-Date
    $healthyServices = @{}
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $Timeout) {
        foreach ($svc in $services) {
            if ($healthyServices[$svc.Name]) { continue }
            
            try {
                $response = Invoke-WebRequest -Uri $svc.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Success "$($svc.Name) is healthy"
                    $healthyServices[$svc.Name] = $true
                }
            } catch { }
        }
        
        if ($healthyServices.Count -eq $services.Count) {
            Write-Success "All services are healthy!"
            return $true
        }
        
        Start-Sleep -Seconds 5
    }
    
    $unhealthy = $services | Where-Object { -not $healthyServices[$_.Name] } | ForEach-Object { $_.Name }
    Write-Failure "Services failed to become healthy: $($unhealthy -join ', ')"
    return $false
}

function Get-LanIpAddress {
    try {
        $adapter = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceDescription -notmatch 'Virtual|Loopback' } | Select-Object -First 1
        if ($adapter) {
            $ip = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 | Select-Object -First 1
            return $ip.IPAddress
        }
    } catch { }
    return $null
}

function Show-AccessPoints {
    $lanIp = Get-LanIpAddress
    
    # Load configured ports from .env
    $envFile = Join-Path $ProjectRoot ".env"
    $nginxPort = 8888
    $codeServerPort = 8443
    
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        $nginxMatch = $envContent | Select-String "NGINX_PORT=(\d+)"
        $codeMatch = $envContent | Select-String "CODE_SERVER_PORT=(\d+)"
        if ($nginxMatch) { $nginxPort = [int]$nginxMatch.Matches[0].Groups[1].Value }
        if ($codeMatch) { $codeServerPort = [int]$codeMatch.Matches[0].Groups[1].Value }
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                    DEPLOYMENT SUCCESSFUL                       " -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Local Access (this machine):" -ForegroundColor Yellow
    Write-Host "  • Open-WebUI (Main):    http://localhost:$nginxPort"
    Write-Host "  • Langflow UI:          http://localhost:$nginxPort/langflow/"
    Write-Host "  • Code-Server:          http://localhost:$nginxPort/code/"
    Write-Host "  • App API:              http://localhost:$nginxPort/api/"
    Write-Host ""
    
    if ($lanIp) {
        Write-Host "LAN Access (same network):" -ForegroundColor Yellow
        Write-Host "  • Open-WebUI (Main):    http://${lanIp}:$nginxPort"
        Write-Host "  • Langflow UI:          http://${lanIp}:$nginxPort/langflow/"
        Write-Host "  • Code-Server:          http://${lanIp}:$nginxPort/code/"
        Write-Host "  • App API:              http://${lanIp}:$nginxPort/api/"
        Write-Host ""
    }
    
    Write-Host "Direct Service Ports:" -ForegroundColor Yellow
    Write-Host "  • Ollama API:           http://localhost:11434"
    Write-Host "  • Open-WebUI Direct:    http://localhost:3000"
    Write-Host "  • Code-Server Direct:   http://localhost:$codeServerPort"
    Write-Host "  • Stable Diffusion:     http://localhost:7861"
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor Yellow
    Write-Host "  • View logs:            docker compose logs -f"
    Write-Host "  • Stop cluster:         docker compose down"
    Write-Host "  • Restart service:      docker compose restart <service>"
    Write-Host ""
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          Codemate-Hub Cluster Deployment                      ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # Pre-flight checks
    if (-not (Test-Prerequisites)) { exit 1 }
    if (-not (Test-EnvironmentConfig)) { exit 1 }
    if (-not (Test-DiskSpace)) {
        Write-Warning "Continuing despite disk space warning..."
    }
    if (-not (Test-PortAvailability)) {
        Write-Warning "Some ports are in use. Deployment may fail."
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y') { exit 1 }
    }
    
    $gpuAvailable = Test-GpuAvailability
    
    # Build phase
    if (-not $SkipBuild) {
        if (-not (Start-ClusterBuild)) { exit 1 }
    }
    
    # Start Ollama and pull model
    if (-not (Start-OllamaWithModel)) { exit 1 }
    
    # Start full cluster
    if (-not (Start-FullCluster)) { exit 1 }
    
    # Wait for health
    if (-not (Wait-ForHealthyServices -Timeout $HealthTimeout)) {
        Write-Warning "Not all services healthy. Check logs with: docker compose logs"
    }
    
    # Show access points
    Show-AccessPoints
}

Main
