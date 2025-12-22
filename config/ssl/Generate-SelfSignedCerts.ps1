<#
.SYNOPSIS
    Generate self-signed SSL certificates for development/fallback (Windows)

.DESCRIPTION
    Creates a Certificate Authority and server certificates with SAN support
    for the Codemate-Hub deployment.

.PARAMETER Domain
    Base domain name (default: vectorweight.com)

.PARAMETER OutputDir
    Directory for certificate output (default: ./certs)

.EXAMPLE
    .\Generate-SelfSignedCerts.ps1 -Domain "vectorweight.com"
#>

param(
    [string]$Domain = "vectorweight.com",
    [string]$OutputDir = ".\certs",
    [int]$DaysValid = 365
)

$ErrorActionPreference = "Stop"

function Write-Status { param($Message) Write-Host "🔵 $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$OutputDir = Resolve-Path $OutputDir

# Define subdomains
$Subdomains = @("ai", "langflow", "code", "api", "ollama")

Write-Status "Generating Certificate Authority..."

# Generate CA certificate using PowerShell
$caParams = @{
    DnsName = "Codemate-Hub CA"
    KeyLength = 4096
    KeyAlgorithm = "RSA"
    HashAlgorithm = "SHA256"
    KeyExportPolicy = "Exportable"
    NotAfter = (Get-Date).AddYears(5)
    CertStoreLocation = "Cert:\CurrentUser\My"
    KeyUsage = "CertSign", "CRLSign"
    TextExtension = @("2.5.29.19={critical}{text}CA=TRUE")
}

$caCert = New-SelfSignedCertificate @caParams
Write-Success "CA Certificate created: $($caCert.Thumbprint)"

# Build SAN list
$sanList = @(
    $Domain,
    "*.$Domain",
    "localhost",
    "*.localhost"
)
foreach ($sub in $Subdomains) {
    $sanList += "$sub.$Domain"
}

Write-Status "Generating server certificate with SANs..."

# Generate server certificate signed by CA
$serverParams = @{
    DnsName = $sanList
    Signer = $caCert
    KeyLength = 2048
    KeyAlgorithm = "RSA"
    HashAlgorithm = "SHA256"
    KeyExportPolicy = "Exportable"
    NotAfter = (Get-Date).AddDays($DaysValid)
    CertStoreLocation = "Cert:\CurrentUser\My"
    KeyUsage = "DigitalSignature", "KeyEncipherment"
    TextExtension = @("2.5.29.37={text}1.3.6.1.5.5.7.3.1")
}

$serverCert = New-SelfSignedCertificate @serverParams
Write-Success "Server Certificate created: $($serverCert.Thumbprint)"

# Export certificates
Write-Status "Exporting certificates..."

# Export CA certificate
$caCertPath = Join-Path $OutputDir "ca.crt"
Export-Certificate -Cert $caCert -FilePath $caCertPath -Type CERT | Out-Null

# Export server certificate (PFX with private key)
$pfxPassword = ConvertTo-SecureString -String "changeit" -Force -AsPlainText
$pfxPath = Join-Path $OutputDir "server.pfx"
Export-PfxCertificate -Cert $serverCert -FilePath $pfxPath -Password $pfxPassword | Out-Null

# Convert PFX to PEM format for nginx (requires openssl)
$opensslAvailable = Get-Command openssl -ErrorAction SilentlyContinue

if ($opensslAvailable) {
    Write-Status "Converting to PEM format..."
    
    $keyPath = Join-Path $OutputDir "server.key"
    $certPath = Join-Path $OutputDir "server.crt"
    $fullchainPath = Join-Path $OutputDir "fullchain.crt"
    
    # Extract private key
    openssl pkcs12 -in $pfxPath -nocerts -nodes -out $keyPath -password pass:changeit 2>$null
    
    # Extract certificate
    openssl pkcs12 -in $pfxPath -clcerts -nokeys -out $certPath -password pass:changeit 2>$null
    
    # Create fullchain
    $caCertPem = Join-Path $OutputDir "ca.pem"
    openssl x509 -inform DER -in $caCertPath -out $caCertPem 2>$null
    Get-Content $certPath, $caCertPem | Set-Content $fullchainPath
    
    Write-Success "PEM files created"
} else {
    Write-Warn "OpenSSL not found. PFX exported but PEM conversion skipped."
    Write-Warn "Install OpenSSL or use WSL to convert: openssl pkcs12 -in server.pfx -out server.pem"
}

Write-Success "Certificates generated in: $OutputDir"
Write-Host ""
Write-Warn "To trust the CA certificate on Windows:"
Write-Host "  1. Double-click $caCertPath"
Write-Host "  2. Click 'Install Certificate'"
Write-Host "  3. Select 'Local Machine' > 'Trusted Root Certification Authorities'"
Write-Host ""
Write-Host "Certificate Thumbprints:" -ForegroundColor Yellow
Write-Host "  CA:     $($caCert.Thumbprint)"
Write-Host "  Server: $($serverCert.Thumbprint)"
