#!/usr/bin/env bash
# DNS and SSL Certificate Management for vectorweight.com
# Supports: Cloudflare, Namecheap, GoDaddy, Route53
# Usage: ./manage-dns-ssl.sh [action] [options]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_DIR="$PROJECT_ROOT/config"
CERTS_DIR="$CONFIG_DIR/ssl/certs"
ENV_FILE="$PROJECT_ROOT/.env"

# Load environment
if [[ -f "$ENV_FILE" ]]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# Configuration defaults
DOMAIN="${DOMAIN:-vectorweight.com}"
DNS_PROVIDER="${DNS_PROVIDER:-cloudflare}"
ACME_EMAIL="${ACME_EMAIL:-admin@$DOMAIN}"
STAGING="${STAGING:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Subdomains to configure
SUBDOMAINS=("ai" "langflow" "code" "api" "ollama")

show_help() {
    cat << EOF
DNS and SSL Certificate Manager for Codemate-Hub

Usage: $0 <action> [options]

Actions:
    setup-dns       Configure DNS records with your provider
    get-certs       Obtain Let's Encrypt certificates
    renew-certs     Renew existing certificates
    self-signed     Generate self-signed certificates (fallback)
    status          Show current DNS and certificate status
    update-lan-ip   Update DNS A records with current LAN IP

Options:
    --provider      DNS provider (cloudflare, namecheap, godaddy, route53)
    --domain        Base domain (default: vectorweight.com)
    --email         ACME email for Let's Encrypt
    --staging       Use Let's Encrypt staging (for testing)

Environment Variables (set in .env):
    DOMAIN              Base domain
    DNS_PROVIDER        DNS provider name
    ACME_EMAIL          Email for Let's Encrypt
    
    # Cloudflare
    CF_API_TOKEN        Cloudflare API token
    CF_ZONE_ID          Cloudflare Zone ID
    
    # Namecheap
    NC_API_USER         Namecheap API username
    NC_API_KEY          Namecheap API key
    
    # GoDaddy
    GD_API_KEY          GoDaddy API key
    GD_API_SECRET       GoDaddy API secret
    
    # AWS Route53
    AWS_ACCESS_KEY_ID   AWS access key
    AWS_SECRET_ACCESS_KEY  AWS secret key
    AWS_HOSTED_ZONE_ID  Route53 hosted zone ID

Examples:
    $0 setup-dns --provider cloudflare
    $0 get-certs --email admin@vectorweight.com
    $0 self-signed
    $0 update-lan-ip
EOF
}

detect_lan_ip() {
    local ip=""
    
    # Try different methods based on OS
    if command -v ip &>/dev/null; then
        # Linux
        ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
    fi
    
    if [[ -z "$ip" ]] && command -v hostname &>/dev/null; then
        # macOS / Linux fallback
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    if [[ -z "$ip" ]]; then
        # macOS specific
        ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
    fi
    
    if [[ -z "$ip" ]]; then
        log_error "Could not detect LAN IP address"
        exit 1
    fi
    
    echo "$ip"
}

# Cloudflare DNS management
cloudflare_update_record() {
    local subdomain="$1"
    local ip="$2"
    local record_name="${subdomain}.${DOMAIN}"
    
    if [[ -z "${CF_API_TOKEN:-}" ]] || [[ -z "${CF_ZONE_ID:-}" ]]; then
        log_error "Cloudflare credentials not set (CF_API_TOKEN, CF_ZONE_ID)"
        return 1
    fi
    
    # Check if record exists
    local existing=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records?name=${record_name}&type=A" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")
    
    local record_id=$(echo "$existing" | jq -r '.result[0].id // empty')
    
    if [[ -n "$record_id" ]]; then
        # Update existing record
        log_info "Updating DNS record: ${record_name} -> ${ip}"
        curl -s -X PUT \
            "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/${record_id}" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"A\",\"name\":\"${record_name}\",\"content\":\"${ip}\",\"ttl\":120,\"proxied\":false}" \
            | jq -r '.success'
    else
        # Create new record
        log_info "Creating DNS record: ${record_name} -> ${ip}"
        curl -s -X POST \
            "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"A\",\"name\":\"${record_name}\",\"content\":\"${ip}\",\"ttl\":120,\"proxied\":false}" \
            | jq -r '.success'
    fi
}

# Namecheap DNS management
namecheap_update_record() {
    local subdomain="$1"
    local ip="$2"
    
    if [[ -z "${NC_API_USER:-}" ]] || [[ -z "${NC_API_KEY:-}" ]]; then
        log_error "Namecheap credentials not set (NC_API_USER, NC_API_KEY)"
        return 1
    fi
    
    # Get client IP for Namecheap API whitelist
    local client_ip=$(curl -s https://api.ipify.org)
    
    log_info "Updating Namecheap DNS: ${subdomain}.${DOMAIN} -> ${ip}"
    
    # Namecheap requires setting all host records at once
    # This is a simplified example - production should fetch existing records first
    curl -s "https://api.namecheap.com/xml.response" \
        --data-urlencode "ApiUser=${NC_API_USER}" \
        --data-urlencode "ApiKey=${NC_API_KEY}" \
        --data-urlencode "UserName=${NC_API_USER}" \
        --data-urlencode "ClientIp=${client_ip}" \
        --data-urlencode "Command=namecheap.domains.dns.setHosts" \
        --data-urlencode "SLD=${DOMAIN%.*}" \
        --data-urlencode "TLD=${DOMAIN##*.}" \
        --data-urlencode "HostName1=${subdomain}" \
        --data-urlencode "RecordType1=A" \
        --data-urlencode "Address1=${ip}" \
        --data-urlencode "TTL1=120"
}

# GoDaddy DNS management
godaddy_update_record() {
    local subdomain="$1"
    local ip="$2"
    
    if [[ -z "${GD_API_KEY:-}" ]] || [[ -z "${GD_API_SECRET:-}" ]]; then
        log_error "GoDaddy credentials not set (GD_API_KEY, GD_API_SECRET)"
        return 1
    fi
    
    log_info "Updating GoDaddy DNS: ${subdomain}.${DOMAIN} -> ${ip}"
    
    curl -s -X PUT \
        "https://api.godaddy.com/v1/domains/${DOMAIN}/records/A/${subdomain}" \
        -H "Authorization: sso-key ${GD_API_KEY}:${GD_API_SECRET}" \
        -H "Content-Type: application/json" \
        --data "[{\"data\":\"${ip}\",\"ttl\":600}]"
}

# AWS Route53 DNS management
route53_update_record() {
    local subdomain="$1"
    local ip="$2"
    local record_name="${subdomain}.${DOMAIN}"
    
    if [[ -z "${AWS_HOSTED_ZONE_ID:-}" ]]; then
        log_error "AWS Route53 credentials not set (AWS_HOSTED_ZONE_ID)"
        return 1
    fi
    
    log_info "Updating Route53 DNS: ${record_name} -> ${ip}"
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "${AWS_HOSTED_ZONE_ID}" \
        --change-batch "{
            \"Changes\": [{
                \"Action\": \"UPSERT\",
                \"ResourceRecordSet\": {
                    \"Name\": \"${record_name}.\",
                    \"Type\": \"A\",
                    \"TTL\": 120,
                    \"ResourceRecords\": [{\"Value\": \"${ip}\"}]
                }
            }]
        }"
}

update_dns_record() {
    local subdomain="$1"
    local ip="$2"
    
    case "$DNS_PROVIDER" in
        cloudflare)
            cloudflare_update_record "$subdomain" "$ip"
            ;;
        namecheap)
            namecheap_update_record "$subdomain" "$ip"
            ;;
        godaddy)
            godaddy_update_record "$subdomain" "$ip"
            ;;
        route53)
            route53_update_record "$subdomain" "$ip"
            ;;
        *)
            log_error "Unknown DNS provider: $DNS_PROVIDER"
            exit 1
            ;;
    esac
}

setup_dns() {
    log_info "Setting up DNS records for ${DOMAIN}..."
    local lan_ip=$(detect_lan_ip)
    log_info "Detected LAN IP: ${lan_ip}"
    
    for subdomain in "${SUBDOMAINS[@]}"; do
        update_dns_record "$subdomain" "$lan_ip"
    done
    
    log_success "DNS records configured!"
}

update_lan_ip() {
    log_info "Updating DNS records with current LAN IP..."
    local lan_ip=$(detect_lan_ip)
    log_info "Current LAN IP: ${lan_ip}"
    
    for subdomain in "${SUBDOMAINS[@]}"; do
        update_dns_record "$subdomain" "$lan_ip"
    done
    
    log_success "DNS records updated with IP: ${lan_ip}"
}

get_certificates() {
    mkdir -p "$CERTS_DIR"
    
    # Build domain list for certbot
    local domain_args="-d ${DOMAIN}"
    for subdomain in "${SUBDOMAINS[@]}"; do
        domain_args="$domain_args -d ${subdomain}.${DOMAIN}"
    done
    
    local staging_flag=""
    if [[ "$STAGING" == "true" ]]; then
        staging_flag="--staging"
        log_warn "Using Let's Encrypt STAGING environment"
    fi
    
    log_info "Requesting certificates from Let's Encrypt..."
    
    # Use DNS challenge for wildcard support
    case "$DNS_PROVIDER" in
        cloudflare)
            certbot certonly \
                --dns-cloudflare \
                --dns-cloudflare-credentials "$CONFIG_DIR/cloudflare.ini" \
                $staging_flag \
                --email "$ACME_EMAIL" \
                --agree-tos \
                --non-interactive \
                $domain_args \
                --cert-path "$CERTS_DIR"
            ;;
        route53)
            certbot certonly \
                --dns-route53 \
                $staging_flag \
                --email "$ACME_EMAIL" \
                --agree-tos \
                --non-interactive \
                $domain_args \
                --cert-path "$CERTS_DIR"
            ;;
        *)
            # HTTP challenge fallback
            log_warn "Using HTTP challenge (requires port 80 accessible)"
            certbot certonly \
                --standalone \
                $staging_flag \
                --email "$ACME_EMAIL" \
                --agree-tos \
                --non-interactive \
                $domain_args \
                --cert-path "$CERTS_DIR"
            ;;
    esac
    
    log_success "Certificates obtained!"
}

generate_self_signed() {
    log_info "Generating self-signed certificates..."
    "$SCRIPT_DIR/generate-self-signed.sh" "$DOMAIN" "$CERTS_DIR"
}

show_status() {
    echo ""
    echo "=== DNS and Certificate Status ==="
    echo ""
    echo "Domain: $DOMAIN"
    echo "DNS Provider: $DNS_PROVIDER"
    echo "LAN IP: $(detect_lan_ip)"
    echo ""
    
    echo "DNS Records:"
    for subdomain in "${SUBDOMAINS[@]}"; do
        local resolved=$(dig +short "${subdomain}.${DOMAIN}" 2>/dev/null || echo "NOT RESOLVED")
        echo "  ${subdomain}.${DOMAIN}: ${resolved}"
    done
    echo ""
    
    echo "Certificates:"
    if [[ -f "$CERTS_DIR/fullchain.crt" ]]; then
        local expiry=$(openssl x509 -enddate -noout -in "$CERTS_DIR/fullchain.crt" 2>/dev/null | cut -d= -f2)
        echo "  Status: INSTALLED"
        echo "  Expires: $expiry"
        echo "  Path: $CERTS_DIR"
    else
        echo "  Status: NOT FOUND"
        echo "  Run: $0 get-certs OR $0 self-signed"
    fi
    echo ""
}

# Parse arguments
ACTION="${1:-}"
shift || true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --provider)
            DNS_PROVIDER="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            ACME_EMAIL="$2"
            shift 2
            ;;
        --staging)
            STAGING="true"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute action
case "$ACTION" in
    setup-dns)
        setup_dns
        ;;
    get-certs)
        get_certificates
        ;;
    renew-certs)
        certbot renew
        ;;
    self-signed)
        generate_self_signed
        ;;
    status)
        show_status
        ;;
    update-lan-ip)
        update_lan_ip
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown action: $ACTION"
        show_help
        exit 1
        ;;
esac
