<#
.SYNOPSIS
    Universal Cross-Platform Deployment Script for codemate-hub (PowerShell)
    
.DESCRIPTION
    Deploys the codemate-hub Docker stack with automatic platform detection,
    GPU support, SSL configuration, and network setup.
    
.PARAMETER Ssl
    Enable SSL/TLS with self-signed certificates or Let's Encrypt
    
.PARAMETER Domain
    Domain name for the deployment (default: localhost)
    
.PARAMETER Gpu
    Enable GPU support (auto-detected by default)
    
.PARAMETER NoGpu
    Disable GPU support
    
.PARAMETER Dev
    Development mode (HTTP only, no SSL)
    
.PARAMETER Pull
    Pull latest images before starting
    
.PARAMETER Clean
    Clean start (remove existing volumes)
    
.PARAMETER Email
    Email for Let's Encrypt certificate
    
.EXAMPLE
    .\Deploy-Universal.ps1 -Dev
    
.EXAMPLE
    .\Deploy-Universal.ps1 -Ssl -Domain "vectorweight.com" -Email "admin@vectorweight.com"
#>

[CmdletBinding()]
param(
    [switch]$Ssl,
    [string]$Domain = "localhost",
    [switch]$Gpu,
    [switch]$NoGpu,
    [switch]$Dev,
    [switch]$Pull,
    [switch]$Clean,
    [string]$Email = "",
    [string]$DnsProvider = ""
)

# =============================================================================
# Configuration
# =============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Configuration object
$Config = @{
    Platform = @{
        OS = ""
        Arch = ""
        DockerCompose = ""
    }
    Gpu = @{
        Available = $false
        Type = "none"
        Info = ""
    }
    Network = @{
        LanIp = "127.0.0.1"
        Conflicts = @()
    }
    Ssl = @{
        Enabled = $Ssl.IsPresent -and -not $Dev.IsPresent
        CertPath = Join-Path $ProjectRoot "config\ssl\certs"
    }
    Ports = @{
        NginxHttp = 80
        NginxHttps = 443
        Ingress = 8888
        Ollama = 11434
        OpenWebUi = 3000
        Langflow = 7860
        CodeServer = 8443
        App = 8000
    }
}

# =============================================================================
# Utility Functions
# =============================================================================
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $color = switch ($Type) {
        "Info" { "Cyan" }
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        "Step" { "Magenta" }
        default { "White" }
    }
    
    $prefix = switch ($Type) {
        "Info" { "[INFO]" }
        "Success" { "[✓]" }
        "Warning" { "[WARN]" }
        "Error" { "[ERROR]" }
        "Step" { "[STEP]" }
        default { "" }
    }
    
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# =============================================================================
# Platform Detection
# =============================================================================
function Get-PlatformInfo {
    Write-ColorOutput "Detecting platform..." -Type Step
    
    # OS Detection
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        $Config.Platform.OS = "Windows"
        $Config.Platform.Arch = $env:PROCESSOR_ARCHITECTURE
    }
    elseif ($IsMacOS) {
        $Config.Platform.OS = "macOS"
        $Config.Platform.Arch = (uname -m)
    }
    elseif ($IsLinux) {
        $Config.Platform.OS = "Linux"
        $Config.Platform.Arch = (uname -m)
    }
    else {
        # Fallback for Windows PowerShell 5.1
        $Config.Platform.OS = "Windows"
        $Config.Platform.Arch = $env:PROCESSOR_ARCHITECTURE
    }
    
    # Docker Compose command
    if (Test-CommandExists "docker") {
        $composeTest = docker compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $Config.Platform.DockerCompose = "docker compose"
        }
        elseif (Test-CommandExists "docker-compose") {
            $Config.Platform.DockerCompose = "docker-compose"
        }
    }
    
    Write-ColorOutput "Platform: $($Config.Platform.OS) ($($Config.Platform.Arch))" -Type Success
    Write-ColorOutput "Docker Compose: $($Config.Platform.DockerCompose)" -Type Info
}

# =============================================================================
# GPU Detection
# =============================================================================
function Get-GpuInfo {
    Write-ColorOutput "Detecting GPU capabilities..." -Type Step
    
    if ($NoGpu.IsPresent) {
        Write-ColorOutput "GPU disabled by -NoGpu flag" -Type Info
        return
    }
    
    # Check for NVIDIA GPU
    if (Test-CommandExists "nvidia-smi") {
        try {
            $gpuInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
            if ($LASTEXITCODE -eq 0 -and $gpuInfo) {
                $Config.Gpu.Available = $true
                $Config.Gpu.Type = "nvidia"
                $Config.Gpu.Info = $gpuInfo.Trim()
                Write-ColorOutput "NVIDIA GPU detected: $($Config.Gpu.Info)" -Type Success
                
                # Check for nvidia-docker runtime
                $dockerInfo = docker info 2>&1
                if ($dockerInfo -notmatch "nvidia") {
                    Write-ColorOutput "NVIDIA Docker runtime not configured" -Type Warning
                    Write-ColorOutput "Install nvidia-container-toolkit for GPU support" -Type Info
                    $Config.Gpu.Available = $false
                }
            }
        }
        catch {
            Write-ColorOutput "Could not query NVIDIA GPU" -Type Warning
        }
    }
    
    # macOS Metal (Apple Silicon)
    if ($Config.Platform.OS -eq "macOS" -and $Config.Platform.Arch -eq "arm64") {
        Write-ColorOutput "Apple Silicon detected (M1/M2/M3)" -Type Info
        Write-ColorOutput "GPU acceleration via Metal (handled by Docker Desktop)" -Type Info
        $Config.Gpu.Type = "metal"
    }
    
    if ($Gpu.IsPresent -and -not $Config.Gpu.Available) {
        Write-ColorOutput "GPU requested but not available" -Type Warning
    }
}

# =============================================================================
# Network Detection
# =============================================================================
function Get-NetworkInfo {
    Write-ColorOutput "Detecting network configuration..." -Type Step
    
    # Get LAN IP
    try {
        if ($Config.Platform.OS -eq "Windows") {
            $adapters = Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp, Manual -ErrorAction SilentlyContinue |
                        Where-Object { $_.IPAddress -notmatch "^169\.254\." -and $_.IPAddress -ne "127.0.0.1" }
            if ($adapters) {
                $Config.Network.LanIp = $adapters[0].IPAddress
            }
        }
        else {
            # Linux/macOS
            $ip = hostname -I 2>$null | ForEach-Object { $_.Split()[0] }
            if ($ip) { $Config.Network.LanIp = $ip }
        }
    }
    catch {
        Write-ColorOutput "Could not detect LAN IP, using localhost" -Type Warning
    }
    
    Write-ColorOutput "LAN IP: $($Config.Network.LanIp)" -Type Success
    
    # Check port conflicts
    Write-ColorOutput "Checking port availability..." -Type Info
    $portsToCheck = @(80, 443, 8888, 8443, 3000, 7860, 11434, 8000)
    
    foreach ($port in $portsToCheck) {
        try {
            $tcpConnections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            if ($tcpConnections) {
                $Config.Network.Conflicts += $port
            }
        }
        catch {
            # Port check failed, assume available
        }
    }
    
    if ($Config.Network.Conflicts.Count -gt 0) {
        Write-ColorOutput "Port conflicts detected: $($Config.Network.Conflicts -join ', ')" -Type Warning
        Write-ColorOutput "Update .env to use alternative ports" -Type Info
    }
    else {
        Write-ColorOutput "All required ports are available" -Type Success
    }
}

# =============================================================================
# Prerequisites Check
# =============================================================================
function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." -Type Step
    
    $missing = @()
    
    # Docker
    if (-not (Test-CommandExists "docker")) {
        $missing += "docker"
    }
    
    # Docker Compose
    if (-not $Config.Platform.DockerCompose) {
        $missing += "docker-compose"
    }
    
    # Check Docker is running
    if (Test-CommandExists "docker") {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "Docker daemon is not running" -Type Error
            Write-ColorOutput "Start Docker Desktop and try again" -Type Info
            exit 1
        }
    }
    
    # OpenSSL for certificate generation
    if (-not (Test-CommandExists "openssl")) {
        Write-ColorOutput "OpenSSL not found - using PowerShell certificate generation" -Type Warning
    }
    
    if ($missing.Count -gt 0) {
        Write-ColorOutput "Missing required tools: $($missing -join ', ')" -Type Error
        Write-ColorOutput "Install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/" -Type Info
        exit 1
    }
    
    Write-ColorOutput "All prerequisites met" -Type Success
}

# =============================================================================
# SSL Certificate Generation
# =============================================================================
function New-SelfSignedCertificates {
    Write-ColorOutput "Generating self-signed certificates..." -Type Step
    
    $certPath = $Config.Ssl.CertPath
    if (-not (Test-Path $certPath)) {
        New-Item -ItemType Directory -Path $certPath -Force | Out-Null
    }
    
    # Build DNS names list
    $dnsNames = @("localhost", $Config.Network.LanIp)
    if ($Domain -ne "localhost") {
        $dnsNames += $Domain
        $dnsNames += "ai.$Domain"
        $dnsNames += "langflow.$Domain"
        $dnsNames += "code.$Domain"
        $dnsNames += "api.$Domain"
        $dnsNames += "ollama.$Domain"
    }
    
    # Try OpenSSL first (better compatibility)
    if (Test-CommandExists "openssl") {
        $sanList = ($dnsNames | ForEach-Object { "DNS:$_" }) -join ","
        $sanList += ",IP:127.0.0.1,IP:$($Config.Network.LanIp)"
        
        $opensslConf = @"
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext
x509_extensions = v3_ca

[dn]
C = US
ST = State
L = City
O = codemate-hub
OU = Development
CN = $Domain

[req_ext]
subjectAltName = $sanList

[v3_ca]
subjectAltName = $sanList
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
"@
        
        $confFile = Join-Path $certPath "openssl.cnf"
        $opensslConf | Out-File -FilePath $confFile -Encoding ASCII
        
        # Generate CA
        & openssl genrsa -out "$certPath\ca.key" 4096 2>$null
        & openssl req -new -x509 -days 3650 -key "$certPath\ca.key" -out "$certPath\ca.crt" -config $confFile 2>$null
        
        # Generate server cert
        & openssl genrsa -out "$certPath\server.key" 2048 2>$null
        & openssl req -new -key "$certPath\server.key" -out "$certPath\server.csr" -config $confFile 2>$null
        & openssl x509 -req -days 365 -in "$certPath\server.csr" -CA "$certPath\ca.crt" -CAkey "$certPath\ca.key" -CAcreateserial -out "$certPath\server.crt" -extfile $confFile -extensions req_ext 2>$null
        
        # Create fullchain
        Get-Content "$certPath\server.crt", "$certPath\ca.crt" | Set-Content "$certPath\fullchain.crt"
    }
    else {
        # Use PowerShell New-SelfSignedCertificate
        $params = @{
            Subject = "CN=$Domain"
            DnsName = $dnsNames
            KeyAlgorithm = "RSA"
            KeyLength = 2048
            CertStoreLocation = "Cert:\CurrentUser\My"
            NotAfter = (Get-Date).AddYears(10)
            KeyUsage = @("KeyEncipherment", "DigitalSignature", "CertSign")
            FriendlyName = "codemate-hub CA"
        }
        
        $cert = New-SelfSignedCertificate @params
        
        # Export certificates
        $pwd = ConvertTo-SecureString -String "codemate" -Force -AsPlainText
        Export-PfxCertificate -Cert $cert -FilePath "$certPath\server.pfx" -Password $pwd | Out-Null
        Export-Certificate -Cert $cert -FilePath "$certPath\server.cer" | Out-Null
        
        # Convert to PEM format (requires openssl or manual conversion)
        Write-ColorOutput "Certificates exported to $certPath" -Type Info
        Write-ColorOutput "Note: Convert .pfx to .crt/.key for nginx if needed" -Type Warning
    }
    
    Write-ColorOutput "Self-signed certificates generated in $certPath" -Type Success
    Write-ColorOutput "Import ca.crt to your browser/system to trust the certificate" -Type Warning
}

# =============================================================================
# Environment Configuration
# =============================================================================
function Set-EnvironmentConfig {
    Write-ColorOutput "Configuring environment..." -Type Step
    
    $envFile = Join-Path $ProjectRoot ".env"
    $envExample = Join-Path $ProjectRoot ".env.example"
    
    # Create .env if it doesn't exist
    if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
        Copy-Item $envExample $envFile
        Write-ColorOutput "Created .env from .env.example" -Type Info
    }
    
    # Build environment content
    $envContent = @"
# Auto-configured by Deploy-Universal.ps1 on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Platform: $($Config.Platform.OS) ($($Config.Platform.Arch))

# Core Settings
PASSWORD=$($env:PASSWORD ?? "changeme")
DOMAIN=$Domain
LAN_IP=$($Config.Network.LanIp)

# GPU Configuration
GPU_ENABLED=$($Config.Gpu.Available)
GPU_TYPE=$($Config.Gpu.Type)

# SSL Configuration
SSL_ENABLED=$($Config.Ssl.Enabled)
ACME_EMAIL=$Email
DNS_PROVIDER=$DnsProvider

# Port Configuration (change if conflicts)
NGINX_HTTP_PORT=$($Config.Ports.NginxHttp)
NGINX_HTTPS_PORT=$($Config.Ports.NginxHttps)
INGRESS_PORT=$($Config.Ports.Ingress)
OLLAMA_PORT=$($Config.Ports.Ollama)
OPENWEBUI_PORT=$($Config.Ports.OpenWebUi)
LANGFLOW_PORT=$($Config.Ports.Langflow)
CODE_SERVER_PORT=$($Config.Ports.CodeServer)
APP_PORT=$($Config.Ports.App)

# Ollama Settings
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5-coder:7b-q4_0
"@
    
    $envContent | Out-File -FilePath $envFile -Encoding UTF8
    Write-ColorOutput "Environment configured" -Type Success
}

# =============================================================================
# Docker Compose Operations
# =============================================================================
function Invoke-DockerCompose {
    param(
        [string[]]$Arguments
    )
    
    $composeCmd = $Config.Platform.DockerCompose
    $composeFiles = @("-f", "docker-compose.yml")
    
    # Add GPU config if available
    if ($Config.Gpu.Available -and $Config.Gpu.Type -eq "nvidia") {
        if (Test-Path "docker-compose.gpu.yml") {
            $composeFiles += @("-f", "docker-compose.gpu.yml")
        }
    }
    
    $fullArgs = $composeFiles + $Arguments
    $cmdLine = "$composeCmd $($fullArgs -join ' ')"
    
    Write-ColorOutput "Running: $cmdLine" -Type Info
    
    if ($composeCmd -eq "docker compose") {
        & docker compose @fullArgs
    }
    else {
        & docker-compose @fullArgs
    }
}

function Start-DeploymentStack {
    Write-ColorOutput "Deploying Docker stack..." -Type Step
    
    # Copy SSL nginx config if SSL enabled
    if ($Config.Ssl.Enabled) {
        $sslConf = Join-Path $ProjectRoot "nginx\nginx-ssl.conf"
        $nginxConf = Join-Path $ProjectRoot "nginx\nginx.conf"
        if (Test-Path $sslConf) {
            Copy-Item $sslConf $nginxConf -Force
            Write-ColorOutput "Using SSL-enabled nginx configuration" -Type Info
        }
    }
    
    # Clean start if requested
    if ($Clean.IsPresent) {
        Write-ColorOutput "Clean start requested - removing existing volumes" -Type Warning
        Invoke-DockerCompose @("down", "-v") 2>$null
    }
    
    # Pull images if requested
    if ($Pull.IsPresent) {
        Write-ColorOutput "Pulling latest images..." -Type Info
        Invoke-DockerCompose @("pull")
    }
    
    # Build custom images
    Write-ColorOutput "Building custom images..." -Type Info
    Invoke-DockerCompose @("build")
    
    # Start services
    Write-ColorOutput "Starting services..." -Type Info
    Invoke-DockerCompose @("up", "-d")
    
    Write-ColorOutput "Services started" -Type Success
}

# =============================================================================
# Health Check
# =============================================================================
function Wait-ForServices {
    Write-ColorOutput "Waiting for services to become healthy..." -Type Step
    
    $timeout = 180
    $elapsed = 0
    $interval = 5
    $services = @("ollama", "open-webui", "langflow", "code-server", "app", "nginx")
    
    while ($elapsed -lt $timeout) {
        $allHealthy = $true
        $statusLine = ""
        
        foreach ($svc in $services) {
            $health = "unknown"
            try {
                $ps = Invoke-DockerCompose @("ps", "--format", "json") 2>$null | ConvertFrom-Json
                $svcInfo = $ps | Where-Object { $_.Name -match $svc }
                if ($svcInfo) {
                    $health = $svcInfo.Health ?? "starting"
                }
            }
            catch {
                $health = "checking"
            }
            
            if ($health -eq "healthy") {
                $statusLine += " $svc[OK]"
            }
            else {
                $statusLine += " $svc[$health]"
                $allHealthy = $false
            }
        }
        
        Write-Host "`r[$elapsed s/$timeout]$statusLine" -NoNewline
        
        if ($allHealthy) {
            Write-Host ""
            Write-ColorOutput "All services are healthy!" -Type Success
            return
        }
        
        Start-Sleep -Seconds $interval
        $elapsed += $interval
    }
    
    Write-Host ""
    Write-ColorOutput "Timeout waiting for services" -Type Warning
    Write-ColorOutput "Check logs with: docker compose logs" -Type Info
}

# =============================================================================
# Display Access Information
# =============================================================================
function Show-AccessInfo {
    Write-Host ""
    Write-Host "=============================================="
    Write-ColorOutput "Deployment Complete!" -Type Success
    Write-Host "=============================================="
    Write-Host ""
    
    $protocol = "http"
    $port = $Config.Ports.Ingress
    if ($Config.Ssl.Enabled) {
        $protocol = "https"
        $port = $Config.Ports.NginxHttps
    }
    
    Write-ColorOutput "Access URLs:" -Type Info
    Write-Host ""
    
    if ($Domain -ne "localhost") {
        Write-Host "  Web UI:      $protocol`://ai.$Domain`:$port" -ForegroundColor Green
        Write-Host "  Langflow:    $protocol`://langflow.$Domain`:$port" -ForegroundColor Green
        Write-Host "  Code Server: $protocol`://code.$Domain`:$port" -ForegroundColor Green
        Write-Host "  API:         $protocol`://api.$Domain`:$port" -ForegroundColor Green
        Write-Host "  Ollama:      $protocol`://ollama.$Domain`:$port" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Local Access:" -ForegroundColor Cyan
    Write-Host "  Web UI:      http://localhost:$($Config.Ports.Ingress)" -ForegroundColor Green
    Write-Host "  Direct:"
    Write-Host "    - Ollama:     http://localhost:$($Config.Ports.Ollama)"
    Write-Host "    - Open-WebUI: http://localhost:$($Config.Ports.OpenWebUi)"
    Write-Host "    - Langflow:   http://localhost:$($Config.Ports.Langflow)"
    Write-Host "    - Code:       http://localhost:$($Config.Ports.CodeServer)"
    
    Write-Host ""
    Write-Host "LAN Access (from other devices):" -ForegroundColor Cyan
    Write-Host "  Web UI:      http://$($Config.Network.LanIp):$($Config.Ports.Ingress)" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor Cyan
    Write-Host "  View logs:    docker compose logs -f [service]"
    Write-Host "  Stop all:     docker compose down"
    Write-Host "  Restart:      docker compose restart [service]"
    
    if ($Config.Ssl.Enabled) {
        Write-Host ""
        Write-Host "SSL Note:" -ForegroundColor Yellow
        Write-Host "  Self-signed cert CA is at: config\ssl\certs\ca.crt"
        Write-Host "  Import this to your browser/system to trust the certificate"
    }
    
    Write-Host ""
}

# =============================================================================
# Main
# =============================================================================
function Main {
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "codemate-hub Universal Deployment (PowerShell)" -ForegroundColor Cyan
    Write-Host "=============================================="
    Write-Host ""
    
    Get-PlatformInfo
    Test-Prerequisites
    Get-GpuInfo
    Get-NetworkInfo
    Set-EnvironmentConfig
    
    if ($Config.Ssl.Enabled) {
        New-SelfSignedCertificates
    }
    
    Start-DeploymentStack
    Wait-ForServices
    Show-AccessInfo
}

# Run main
Main
