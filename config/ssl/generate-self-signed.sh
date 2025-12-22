#!/usr/bin/env bash
# Generate self-signed SSL certificates for development/fallback
# Usage: ./generate-self-signed.sh [domain] [output_dir]

set -euo pipefail

DOMAIN="${1:-vectorweight.com}"
OUTPUT_DIR="${2:-./certs}"
DAYS_VALID=365

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Define subdomains
SUBDOMAINS=(
    "ai"        # Main Open-WebUI
    "langflow"  # Langflow UI
    "code"      # Code-Server
    "api"       # App API
    "ollama"    # Ollama API
)

# Generate CA key and certificate
log_info "Generating Certificate Authority..."
openssl genrsa -out "$OUTPUT_DIR/ca.key" 4096

openssl req -x509 -new -nodes \
    -key "$OUTPUT_DIR/ca.key" \
    -sha256 \
    -days 1825 \
    -out "$OUTPUT_DIR/ca.crt" \
    -subj "/C=US/ST=Local/L=Local/O=Codemate-Hub/OU=Development/CN=Codemate-Hub CA"

# Generate SAN (Subject Alternative Names) config
log_info "Creating SAN configuration..."
cat > "$OUTPUT_DIR/san.cnf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
C = US
ST = Local
L = Local
O = Codemate-Hub
OU = Development
CN = ${DOMAIN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = *.${DOMAIN}
DNS.3 = localhost
DNS.4 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Add subdomain entries
idx=5
for sub in "${SUBDOMAINS[@]}"; do
    echo "DNS.${idx} = ${sub}.${DOMAIN}" >> "$OUTPUT_DIR/san.cnf"
    ((idx++))
done

# Generate server key
log_info "Generating server private key..."
openssl genrsa -out "$OUTPUT_DIR/server.key" 2048

# Generate CSR
log_info "Generating Certificate Signing Request..."
openssl req -new \
    -key "$OUTPUT_DIR/server.key" \
    -out "$OUTPUT_DIR/server.csr" \
    -config "$OUTPUT_DIR/san.cnf"

# Sign certificate with CA
log_info "Signing certificate with CA..."
openssl x509 -req \
    -in "$OUTPUT_DIR/server.csr" \
    -CA "$OUTPUT_DIR/ca.crt" \
    -CAkey "$OUTPUT_DIR/ca.key" \
    -CAcreateserial \
    -out "$OUTPUT_DIR/server.crt" \
    -days "$DAYS_VALID" \
    -sha256 \
    -extfile "$OUTPUT_DIR/san.cnf" \
    -extensions req_ext

# Create combined certificate for nginx
cat "$OUTPUT_DIR/server.crt" "$OUTPUT_DIR/ca.crt" > "$OUTPUT_DIR/fullchain.crt"

# Set permissions
chmod 600 "$OUTPUT_DIR"/*.key
chmod 644 "$OUTPUT_DIR"/*.crt

log_info "Self-signed certificates generated successfully!"
log_info "Files created in: $OUTPUT_DIR"
echo ""
log_warn "To trust these certificates on your system:"
echo "  Linux:   sudo cp $OUTPUT_DIR/ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates"
echo "  macOS:   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $OUTPUT_DIR/ca.crt"
echo "  Windows: Import $OUTPUT_DIR/ca.crt into 'Trusted Root Certification Authorities'"
