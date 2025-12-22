#!/usr/bin/env bash
#
# Universal Cross-Platform Deployment Script for codemate-hub
# Supports: Linux (Ubuntu, Debian, Fedora, Arch, RHEL), macOS, Windows (via WSL/Git Bash)
#
# Usage: ./deploy-universal.sh [options]
# Options:
#   --ssl           Enable SSL/TLS with Let's Encrypt or self-signed
#   --domain NAME   Set domain (default: localhost)
#   --gpu           Enable GPU support (auto-detected)
#   --no-gpu        Disable GPU support
#   --dev           Development mode (HTTP only, no SSL)
#   --pull          Pull latest images before starting
#   --clean         Clean start (remove volumes)
#   --help          Show this help message
#
set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Defaults
ENABLE_SSL=false
DOMAIN="localhost"
ENABLE_GPU="auto"
DEV_MODE=false
PULL_IMAGES=false
CLEAN_START=false
DNS_PROVIDER=""
ACME_EMAIL=""

# =============================================================================
# Utility Functions
# =============================================================================
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step() { echo -e "${CYAN}[STEP]${NC} $*"; }

show_help() {
    head -20 "$0" | tail -15
    exit 0
}

# =============================================================================
# Platform Detection
# =============================================================================
detect_platform() {
    log_step "Detecting platform..."
    
    OS_TYPE=""
    OS_DISTRO=""
    PKG_MANAGER=""
    DOCKER_COMPOSE_CMD=""
    
    case "$(uname -s)" in
        Linux*)
            OS_TYPE="linux"
            if [[ -f /etc/os-release ]]; then
                . /etc/os-release
                OS_DISTRO="${ID:-unknown}"
            fi
            
            # Detect package manager
            if command -v apt-get &>/dev/null; then
                PKG_MANAGER="apt"
            elif command -v dnf &>/dev/null; then
                PKG_MANAGER="dnf"
            elif command -v yum &>/dev/null; then
                PKG_MANAGER="yum"
            elif command -v pacman &>/dev/null; then
                PKG_MANAGER="pacman"
            elif command -v apk &>/dev/null; then
                PKG_MANAGER="apk"
            fi
            ;;
        Darwin*)
            OS_TYPE="macos"
            OS_DISTRO="macos"
            if command -v brew &>/dev/null; then
                PKG_MANAGER="brew"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_TYPE="windows"
            OS_DISTRO="windows"
            PKG_MANAGER="none"
            ;;
        *)
            log_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
    
    # Detect Docker Compose command
    if command -v docker &>/dev/null; then
        if docker compose version &>/dev/null 2>&1; then
            DOCKER_COMPOSE_CMD="docker compose"
        elif command -v docker-compose &>/dev/null; then
            DOCKER_COMPOSE_CMD="docker-compose"
        fi
    fi
    
    log_success "Platform: $OS_TYPE ($OS_DISTRO)"
    log_info "Package manager: ${PKG_MANAGER:-none}"
    log_info "Docker Compose: ${DOCKER_COMPOSE_CMD:-not found}"
}

# =============================================================================
# GPU Detection
# =============================================================================
detect_gpu() {
    log_step "Detecting GPU capabilities..."
    
    GPU_AVAILABLE=false
    GPU_TYPE=""
    
    case "$OS_TYPE" in
        linux|windows)
            # Check for NVIDIA GPU
            if command -v nvidia-smi &>/dev/null; then
                if nvidia-smi &>/dev/null 2>&1; then
                    GPU_AVAILABLE=true
                    GPU_TYPE="nvidia"
                    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1)
                    log_success "NVIDIA GPU detected: $GPU_INFO"
                fi
            fi
            
            # Check for NVIDIA Docker runtime
            if [[ "$GPU_AVAILABLE" == "true" ]]; then
                if ! docker info 2>/dev/null | grep -q "nvidia"; then
                    log_warn "NVIDIA Docker runtime not configured"
                    log_info "Install nvidia-container-toolkit for GPU support"
                    GPU_AVAILABLE=false
                fi
            fi
            ;;
        macos)
            # Check for Apple Silicon
            if [[ "$(uname -m)" == "arm64" ]]; then
                log_info "Apple Silicon detected (M1/M2/M3)"
                log_info "GPU acceleration via Metal (handled by Docker Desktop)"
                GPU_TYPE="metal"
                # Metal GPU is handled automatically by Docker Desktop
            else
                log_info "Intel Mac detected - no GPU acceleration available"
            fi
            ;;
    esac
    
    # Override based on flags
    if [[ "$ENABLE_GPU" == "false" ]]; then
        GPU_AVAILABLE=false
        log_info "GPU disabled by --no-gpu flag"
    elif [[ "$ENABLE_GPU" == "true" ]] && [[ "$GPU_AVAILABLE" == "false" ]]; then
        log_warn "GPU requested but not available"
    fi
    
    export GPU_AVAILABLE GPU_TYPE
}

# =============================================================================
# Network Detection
# =============================================================================
detect_network() {
    log_step "Detecting network configuration..."
    
    # Get LAN IP
    LAN_IP=""
    case "$OS_TYPE" in
        linux)
            LAN_IP=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || hostname -I 2>/dev/null | awk '{print $1}')
            ;;
        macos)
            LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
            ;;
        windows)
            LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig 2>/dev/null | grep -oP 'IPv4.*: \K[\d.]+' | head -1)
            ;;
    esac
    
    if [[ -n "$LAN_IP" ]]; then
        log_success "LAN IP: $LAN_IP"
    else
        LAN_IP="127.0.0.1"
        log_warn "Could not detect LAN IP, using localhost"
    fi
    
    # Check for port conflicts
    log_info "Checking port availability..."
    PORTS_TO_CHECK=(80 443 8888 8443 3000 7860 11434 8000)
    CONFLICTS=()
    
    for port in "${PORTS_TO_CHECK[@]}"; do
        if command -v ss &>/dev/null; then
            if ss -tuln 2>/dev/null | grep -q ":$port "; then
                CONFLICTS+=("$port")
            fi
        elif command -v netstat &>/dev/null; then
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                CONFLICTS+=("$port")
            fi
        elif command -v lsof &>/dev/null; then
            if lsof -i ":$port" &>/dev/null 2>&1; then
                CONFLICTS+=("$port")
            fi
        fi
    done
    
    if [[ ${#CONFLICTS[@]} -gt 0 ]]; then
        log_warn "Port conflicts detected: ${CONFLICTS[*]}"
        log_info "Update .env to use alternative ports"
    else
        log_success "All required ports are available"
    fi
    
    export LAN_IP
}

# =============================================================================
# Prerequisites Check
# =============================================================================
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing=()
    
    # Docker
    if ! command -v docker &>/dev/null; then
        missing+=("docker")
    fi
    
    # Docker Compose
    if [[ -z "$DOCKER_COMPOSE_CMD" ]]; then
        missing+=("docker-compose")
    fi
    
    # Check Docker is running
    if command -v docker &>/dev/null; then
        if ! docker info &>/dev/null 2>&1; then
            log_error "Docker daemon is not running"
            case "$OS_TYPE" in
                linux)
                    log_info "Try: sudo systemctl start docker"
                    ;;
                macos|windows)
                    log_info "Start Docker Desktop and try again"
                    ;;
            esac
            exit 1
        fi
    fi
    
    # Optional but recommended
    if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
        log_warn "Neither curl nor wget found - some features may not work"
    fi
    
    if ! command -v openssl &>/dev/null; then
        log_warn "OpenSSL not found - self-signed cert generation unavailable"
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Installation instructions:"
        
        case "$OS_TYPE" in
            linux)
                case "$PKG_MANAGER" in
                    apt)
                        log_info "  sudo apt update && sudo apt install -y docker.io docker-compose-plugin"
                        ;;
                    dnf|yum)
                        log_info "  sudo dnf install -y docker docker-compose-plugin"
                        ;;
                    pacman)
                        log_info "  sudo pacman -S docker docker-compose"
                        ;;
                esac
                ;;
            macos)
                log_info "  Install Docker Desktop: https://docs.docker.com/desktop/mac/install/"
                ;;
            windows)
                log_info "  Install Docker Desktop: https://docs.docker.com/desktop/windows/install/"
                ;;
        esac
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# =============================================================================
# SSL Certificate Management
# =============================================================================
setup_ssl() {
    log_step "Setting up SSL certificates..."
    
    SSL_DIR="$PROJECT_ROOT/config/ssl/certs"
    mkdir -p "$SSL_DIR"
    
    if [[ "$DOMAIN" != "localhost" ]] && [[ "$DEV_MODE" == "false" ]]; then
        # Try Let's Encrypt first
        if [[ -n "$ACME_EMAIL" ]] && command -v certbot &>/dev/null; then
            log_info "Attempting Let's Encrypt certificate..."
            
            if certbot certonly --standalone \
                -d "$DOMAIN" \
                -d "ai.$DOMAIN" \
                -d "langflow.$DOMAIN" \
                -d "code.$DOMAIN" \
                -d "api.$DOMAIN" \
                -d "ollama.$DOMAIN" \
                --email "$ACME_EMAIL" \
                --agree-tos \
                --non-interactive \
                2>/dev/null; then
                
                log_success "Let's Encrypt certificate obtained"
                cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/fullchain.crt"
                cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/server.key"
                return 0
            else
                log_warn "Let's Encrypt failed, falling back to self-signed"
            fi
        fi
    fi
    
    # Generate self-signed certificate
    generate_self_signed_cert
}

generate_self_signed_cert() {
    log_info "Generating self-signed certificates..."
    
    SSL_DIR="$PROJECT_ROOT/config/ssl/certs"
    mkdir -p "$SSL_DIR"
    
    # Prepare SAN list
    DOMAINS=("localhost" "127.0.0.1" "$LAN_IP")
    if [[ "$DOMAIN" != "localhost" ]]; then
        DOMAINS+=("$DOMAIN" "ai.$DOMAIN" "langflow.$DOMAIN" "code.$DOMAIN" "api.$DOMAIN" "ollama.$DOMAIN")
    fi
    
    # Build SAN string
    SAN=""
    DNS_COUNT=1
    IP_COUNT=1
    for d in "${DOMAINS[@]}"; do
        if [[ "$d" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            SAN="${SAN}IP.${IP_COUNT} = $d\n"
            ((IP_COUNT++))
        else
            SAN="${SAN}DNS.${DNS_COUNT} = $d\n"
            ((DNS_COUNT++))
        fi
    done
    
    # Create OpenSSL config
    cat > "$SSL_DIR/openssl.cnf" <<EOF
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
CN = ${DOMAIN}

[req_ext]
subjectAltName = @alt_names

[v3_ca]
subjectAltName = @alt_names
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[alt_names]
$(echo -e "$SAN")
EOF
    
    # Generate CA key and certificate
    openssl genrsa -out "$SSL_DIR/ca.key" 4096 2>/dev/null
    openssl req -new -x509 -days 3650 -key "$SSL_DIR/ca.key" \
        -out "$SSL_DIR/ca.crt" \
        -config "$SSL_DIR/openssl.cnf" \
        2>/dev/null
    
    # Generate server key and CSR
    openssl genrsa -out "$SSL_DIR/server.key" 2048 2>/dev/null
    openssl req -new -key "$SSL_DIR/server.key" \
        -out "$SSL_DIR/server.csr" \
        -config "$SSL_DIR/openssl.cnf" \
        2>/dev/null
    
    # Sign server certificate
    openssl x509 -req -days 365 \
        -in "$SSL_DIR/server.csr" \
        -CA "$SSL_DIR/ca.crt" \
        -CAkey "$SSL_DIR/ca.key" \
        -CAcreateserial \
        -out "$SSL_DIR/server.crt" \
        -extfile "$SSL_DIR/openssl.cnf" \
        -extensions req_ext \
        2>/dev/null
    
    # Create fullchain
    cat "$SSL_DIR/server.crt" "$SSL_DIR/ca.crt" > "$SSL_DIR/fullchain.crt"
    
    log_success "Self-signed certificates generated in $SSL_DIR"
    log_warn "Import ca.crt to your browser/system to trust the certificate"
}

# =============================================================================
# Environment Configuration
# =============================================================================
configure_environment() {
    log_step "Configuring environment..."
    
    ENV_FILE="$PROJECT_ROOT/.env"
    
    # Create .env if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]] && [[ -f "$PROJECT_ROOT/.env.example" ]]; then
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        log_info "Created .env from .env.example"
    fi
    
    # Update or create .env with detected values
    {
        echo "# Auto-configured by deploy-universal.sh on $(date)"
        echo "# Platform: $OS_TYPE ($OS_DISTRO)"
        echo ""
        echo "# Core Settings"
        echo "PASSWORD=${PASSWORD:-changeme}"
        echo "DOMAIN=${DOMAIN}"
        echo "LAN_IP=${LAN_IP}"
        echo ""
        echo "# GPU Configuration"
        echo "GPU_ENABLED=${GPU_AVAILABLE}"
        echo "GPU_TYPE=${GPU_TYPE:-none}"
        echo ""
        echo "# SSL Configuration"
        echo "SSL_ENABLED=${ENABLE_SSL}"
        echo "ACME_EMAIL=${ACME_EMAIL:-}"
        echo "DNS_PROVIDER=${DNS_PROVIDER:-}"
        echo ""
        echo "# Port Configuration (change if conflicts)"
        echo "NGINX_HTTP_PORT=${NGINX_HTTP_PORT:-80}"
        echo "NGINX_HTTPS_PORT=${NGINX_HTTPS_PORT:-443}"
        echo "INGRESS_PORT=${INGRESS_PORT:-8888}"
        echo "OLLAMA_PORT=${OLLAMA_PORT:-11434}"
        echo "OPENWEBUI_PORT=${OPENWEBUI_PORT:-3000}"
        echo "LANGFLOW_PORT=${LANGFLOW_PORT:-7860}"
        echo "CODE_SERVER_PORT=${CODE_SERVER_PORT:-8443}"
        echo "APP_PORT=${APP_PORT:-8000}"
        echo ""
        echo "# Ollama Settings"
        echo "OLLAMA_BASE_URL=http://ollama:11434"
        echo "OLLAMA_MODEL=qwen2.5-coder:7b-q4_0"
    } > "$ENV_FILE"
    
    # Source the env file
    set -a
    source "$ENV_FILE"
    set +a
    
    log_success "Environment configured"
}

# =============================================================================
# Docker Compose File Selection
# =============================================================================
select_compose_file() {
    log_step "Selecting Docker Compose configuration..."
    
    COMPOSE_FILES=("-f" "docker-compose.yml")
    
    # GPU configuration
    if [[ "$GPU_AVAILABLE" == "true" ]] && [[ "$GPU_TYPE" == "nvidia" ]]; then
        if [[ -f "docker-compose.gpu.yml" ]]; then
            COMPOSE_FILES+=("-f" "docker-compose.gpu.yml")
            log_info "Using GPU-enabled configuration"
        fi
    fi
    
    # SSL configuration (copy appropriate nginx config)
    if [[ "$ENABLE_SSL" == "true" ]]; then
        if [[ -f "nginx/nginx-ssl.conf" ]]; then
            cp "nginx/nginx-ssl.conf" "nginx/nginx.conf"
            log_info "Using SSL-enabled nginx configuration"
        fi
    fi
    
    export COMPOSE_FILES
}

# =============================================================================
# Deployment
# =============================================================================
deploy_stack() {
    log_step "Deploying Docker stack..."
    
    # Clean start if requested
    if [[ "$CLEAN_START" == "true" ]]; then
        log_warn "Clean start requested - removing existing volumes"
        $DOCKER_COMPOSE_CMD "${COMPOSE_FILES[@]}" down -v 2>/dev/null || true
    fi
    
    # Pull images if requested
    if [[ "$PULL_IMAGES" == "true" ]]; then
        log_info "Pulling latest images..."
        $DOCKER_COMPOSE_CMD "${COMPOSE_FILES[@]}" pull
    fi
    
    # Build custom images
    log_info "Building custom images..."
    $DOCKER_COMPOSE_CMD "${COMPOSE_FILES[@]}" build --parallel 2>/dev/null || \
        $DOCKER_COMPOSE_CMD "${COMPOSE_FILES[@]}" build
    
    # Start services
    log_info "Starting services..."
    $DOCKER_COMPOSE_CMD "${COMPOSE_FILES[@]}" up -d
    
    log_success "Services started"
}

# =============================================================================
# Health Check
# =============================================================================
wait_for_services() {
    log_step "Waiting for services to become healthy..."
    
    local timeout=180
    local elapsed=0
    local interval=5
    local services=("ollama" "open-webui" "langflow" "code-server" "app" "nginx")
    
    while [[ $elapsed -lt $timeout ]]; do
        local all_healthy=true
        local status_line=""
        
        for svc in "${services[@]}"; do
            local health
            health=$($DOCKER_COMPOSE_CMD "${COMPOSE_FILES[@]}" ps --format json 2>/dev/null | \
                     grep -o "\"$svc\"[^}]*" | grep -oP '"Health":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
            
            if [[ "$health" == "healthy" ]]; then
                status_line="$status_line ${GREEN}$svc✓${NC}"
            elif [[ "$health" == "starting" ]]; then
                status_line="$status_line ${YELLOW}$svc...${NC}"
                all_healthy=false
            else
                status_line="$status_line ${RED}$svc✗${NC}"
                all_healthy=false
            fi
        done
        
        echo -ne "\r[${elapsed}s/$timeout] $status_line"
        
        if [[ "$all_healthy" == "true" ]]; then
            echo ""
            log_success "All services are healthy!"
            return 0
        fi
        
        sleep $interval
        ((elapsed += interval))
    done
    
    echo ""
    log_error "Timeout waiting for services"
    log_info "Check logs with: $DOCKER_COMPOSE_CMD ${COMPOSE_FILES[*]} logs"
    return 1
}

# =============================================================================
# Display Access Information
# =============================================================================
show_access_info() {
    echo ""
    echo "=============================================="
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "=============================================="
    echo ""
    
    local protocol="http"
    local port="$INGRESS_PORT"
    if [[ "$ENABLE_SSL" == "true" ]]; then
        protocol="https"
        port="${NGINX_HTTPS_PORT:-443}"
    fi
    
    echo -e "${CYAN}Access URLs:${NC}"
    echo ""
    
    if [[ "$DOMAIN" != "localhost" ]]; then
        echo -e "  ${GREEN}Web UI:${NC}      ${protocol}://ai.${DOMAIN}:${port}"
        echo -e "  ${GREEN}Langflow:${NC}    ${protocol}://langflow.${DOMAIN}:${port}"
        echo -e "  ${GREEN}Code Server:${NC} ${protocol}://code.${DOMAIN}:${port}"
        echo -e "  ${GREEN}API:${NC}         ${protocol}://api.${DOMAIN}:${port}"
        echo -e "  ${GREEN}Ollama:${NC}      ${protocol}://ollama.${DOMAIN}:${port}"
    fi
    
    echo ""
    echo -e "${CYAN}Local Access:${NC}"
    echo -e "  ${GREEN}Web UI:${NC}      http://localhost:${INGRESS_PORT}"
    echo -e "  ${GREEN}Direct:${NC}"
    echo -e "    - Ollama:     http://localhost:${OLLAMA_PORT:-11434}"
    echo -e "    - Open-WebUI: http://localhost:${OPENWEBUI_PORT:-3000}"
    echo -e "    - Langflow:   http://localhost:${LANGFLOW_PORT:-7860}"
    echo -e "    - Code:       http://localhost:${CODE_SERVER_PORT:-8443}"
    
    echo ""
    echo -e "${CYAN}LAN Access (from other devices):${NC}"
    echo -e "  ${GREEN}Web UI:${NC}      http://${LAN_IP}:${INGRESS_PORT}"
    
    echo ""
    echo -e "${CYAN}Useful Commands:${NC}"
    echo "  View logs:    $DOCKER_COMPOSE_CMD logs -f [service]"
    echo "  Stop all:     $DOCKER_COMPOSE_CMD down"
    echo "  Restart:      $DOCKER_COMPOSE_CMD restart [service]"
    
    if [[ "$ENABLE_SSL" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}SSL Note:${NC}"
        echo "  Self-signed cert CA is at: config/ssl/certs/ca.crt"
        echo "  Import this to your browser/system to trust the certificate"
    fi
    
    echo ""
}

# =============================================================================
# Main
# =============================================================================
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --ssl)
                ENABLE_SSL=true
                shift
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --gpu)
                ENABLE_GPU=true
                shift
                ;;
            --no-gpu)
                ENABLE_GPU=false
                shift
                ;;
            --dev)
                DEV_MODE=true
                ENABLE_SSL=false
                shift
                ;;
            --pull)
                PULL_IMAGES=true
                shift
                ;;
            --clean)
                CLEAN_START=true
                shift
                ;;
            --email)
                ACME_EMAIL="$2"
                shift 2
                ;;
            --dns-provider)
                DNS_PROVIDER="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
    
    echo ""
    echo "=============================================="
    echo -e "${CYAN}codemate-hub Universal Deployment${NC}"
    echo "=============================================="
    echo ""
    
    detect_platform
    check_prerequisites
    detect_gpu
    detect_network
    configure_environment
    
    if [[ "$ENABLE_SSL" == "true" ]]; then
        setup_ssl
    fi
    
    select_compose_file
    deploy_stack
    wait_for_services
    show_access_info
}

main "$@"
