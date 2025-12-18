# SSL & DNS Configuration Guide

This guide covers setting up SSL certificates and DNS for the codemate-hub deployment.

## Quick Start

### Development Mode (No SSL)

```bash
# Bash (Linux/macOS/WSL)
./scripts/deploy-universal.sh --dev

# PowerShell (Windows)
.\scripts\Deploy-Universal.ps1 -Dev
```

### Production Mode with SSL

```bash
# With self-signed certificates
./scripts/deploy-universal.sh --ssl --domain vectorweight.com

# With Let's Encrypt
./scripts/deploy-universal.sh --ssl --domain vectorweight.com --email admin@vectorweight.com
```

## SSL Certificate Options

### Option 1: Self-Signed Certificates (Development/LAN)

Self-signed certificates work immediately without internet access but require importing the CA certificate into your browser/system.

**Generate certificates:**
```bash
# Bash
./config/ssl/generate-self-signed.sh vectorweight.com

# PowerShell
.\config\ssl\Generate-SelfSignedCerts.ps1 -Domain vectorweight.com
```

**Trust the CA certificate:**

**Windows:**
1. Double-click `config/ssl/certs/ca.crt`
2. Click "Install Certificate"
3. Select "Local Machine" → "Trusted Root Certification Authorities"
4. Complete the wizard

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain config/ssl/certs/ca.crt
```

**Linux (Ubuntu/Debian):**
```bash
sudo cp config/ssl/certs/ca.crt /usr/local/share/ca-certificates/codemate-hub.crt
sudo update-ca-certificates
```

**Firefox (all platforms):**
1. Go to `about:preferences#privacy`
2. Scroll to "Certificates" → "View Certificates"
3. Import `ca.crt` under "Authorities" tab

### Option 2: Let's Encrypt (Production)

Requires:
- A public domain pointing to your server
- Ports 80/443 accessible from the internet

**Obtain certificate:**
```bash
# Using certbot container
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d vectorweight.com \
  -d ai.vectorweight.com \
  -d langflow.vectorweight.com \
  -d code.vectorweight.com \
  -d api.vectorweight.com \
  -d ollama.vectorweight.com \
  --email admin@vectorweight.com \
  --agree-tos

# Copy certificates to nginx directory
cp /etc/letsencrypt/live/vectorweight.com/fullchain.pem config/ssl/certs/fullchain.crt
cp /etc/letsencrypt/live/vectorweight.com/privkey.pem config/ssl/certs/server.key
```

**Auto-renewal:**
The certbot container automatically renews certificates every 12 hours if they're within 30 days of expiration.

To enable auto-renewal:
```bash
docker compose --profile ssl up -d certbot
```

## DNS Configuration

### Subdomain Structure

| Subdomain | Service | Description |
|-----------|---------|-------------|
| `ai.vectorweight.com` | Open-WebUI | Main AI chat interface |
| `langflow.vectorweight.com` | Langflow | Visual workflow builder |
| `code.vectorweight.com` | Code-Server | VS Code in browser |
| `api.vectorweight.com` | App | Python API endpoint |
| `ollama.vectorweight.com` | Ollama | LLM API (for external access) |

### Manual DNS Setup

Add these DNS records at your registrar:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | vectorweight.com | YOUR_PUBLIC_IP | 300 |
| A | ai | YOUR_PUBLIC_IP | 300 |
| A | langflow | YOUR_PUBLIC_IP | 300 |
| A | code | YOUR_PUBLIC_IP | 300 |
| A | api | YOUR_PUBLIC_IP | 300 |
| A | ollama | YOUR_PUBLIC_IP | 300 |

For LAN-only access, use your LAN IP (e.g., `192.168.1.100`).

### Automated DNS Setup

The `manage-dns-ssl.sh` script automates DNS record creation.

**Supported providers:**
- Cloudflare
- Namecheap
- GoDaddy
- AWS Route53

**Setup:**
```bash
# Set provider credentials in .env
export DNS_PROVIDER=cloudflare
export CF_API_TOKEN=your-api-token
export CF_ZONE_ID=your-zone-id

# Run DNS setup
./config/ssl/manage-dns-ssl.sh setup vectorweight.com
```

### Provider-Specific Configuration

#### Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your domain → Get Zone ID from the sidebar
3. Go to "My Profile" → "API Tokens" → "Create Token"
4. Use "Edit zone DNS" template
5. Set permissions: `Zone:DNS:Edit`

```bash
export CF_API_TOKEN=your-token
export CF_ZONE_ID=your-zone-id
```

#### Namecheap

1. Enable API access at [Namecheap API Settings](https://ap.www.namecheap.com/settings/tools/apiaccess/)
2. Whitelist your IP address
3. Note your API user and key

```bash
export NAMECHEAP_API_USER=your-username
export NAMECHEAP_API_KEY=your-api-key
```

#### GoDaddy

1. Go to [GoDaddy Developer Portal](https://developer.godaddy.com/keys)
2. Create a production API key

```bash
export GODADDY_API_KEY=your-key
export GODADDY_API_SECRET=your-secret
```

#### AWS Route53

1. Create an IAM user with `AmazonRoute53FullAccess` policy
2. Generate access keys

```bash
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_HOSTED_ZONE_ID=your-zone-id
```

## Nginx Configuration

### HTTP Mode (Development)

Uses `nginx/nginx-http.conf`:
- Path-based routing (`/langflow`, `/code`, `/api`, `/ollama`)
- Listens on port 80 and 8888
- WebSocket support for all services

### HTTPS Mode (Production)

Uses `nginx/nginx-ssl.conf`:
- Subdomain-based routing
- TLS 1.2/1.3 with modern ciphers
- HSTS enabled
- HTTP → HTTPS redirect
- Let's Encrypt ACME challenge support

**Switch between modes:**
```bash
# HTTP mode
cp nginx/nginx-http.conf nginx/nginx.conf
docker compose restart nginx

# HTTPS mode
cp nginx/nginx-ssl.conf nginx/nginx.conf
docker compose restart nginx
```

## Network Configuration

### LAN Access

The deployment automatically detects your LAN IP and configures services for local network access.

**Access from other devices:**
```
http://YOUR_LAN_IP:8888
```

### Firewall Rules

If using a firewall, open these ports:

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8888/tcp  # Nginx ingress
sudo ufw allow 11434/tcp # Ollama (optional, for external API access)

# firewalld (RHEL/CentOS)
sudo firewall-cmd --add-port={80,443,8888,11434}/tcp --permanent
sudo firewall-cmd --reload
```

### Router Port Forwarding

For external access (Let's Encrypt or public deployment):

| External Port | Internal Port | Service |
|---------------|---------------|---------|
| 80 | 80 | Nginx (HTTP/ACME) |
| 443 | 443 | Nginx (HTTPS) |

## Troubleshooting

### Certificate Errors

**"NET::ERR_CERT_AUTHORITY_INVALID"**
- Import `ca.crt` as described above

**"Connection refused on port 443"**
- Ensure SSL certificates exist in `config/ssl/certs/`
- Check nginx is using `nginx-ssl.conf`
- Verify ports 443 is exposed in docker-compose.yml

### DNS Issues

**"DNS_PROBE_FINISHED_NXDOMAIN"**
- DNS records not propagated (wait 5-60 minutes)
- Check records with `dig ai.vectorweight.com`
- Verify domain ownership

**"ERR_NAME_NOT_RESOLVED" on LAN**
- Add entries to local hosts file:
  ```
  192.168.1.100 ai.vectorweight.com langflow.vectorweight.com code.vectorweight.com
  ```

### Let's Encrypt Errors

**"Rate limit exceeded"**
- Use staging server for testing: `--staging` flag
- Wait 1 hour between attempts

**"Challenge failed"**
- Ensure port 80 is accessible from internet
- Check `.well-known/acme-challenge/` is served correctly
- Verify DNS points to correct IP

## Security Recommendations

1. **Use Let's Encrypt** for production deployments
2. **Enable HSTS** (already configured in nginx-ssl.conf)
3. **Restrict Ollama access** - don't expose port 11434 publicly unless needed
4. **Use strong passwords** for Code-Server
5. **Keep certificates renewed** - enable certbot auto-renewal
6. **Firewall all unused ports** - only expose 80, 443, and 8888
7. **Regular updates** - keep Docker images updated

## Quick Reference

```bash
# Generate self-signed certs
./config/ssl/generate-self-signed.sh vectorweight.com

# Setup DNS records
./config/ssl/manage-dns-ssl.sh setup vectorweight.com

# Get Let's Encrypt certs
./config/ssl/manage-dns-ssl.sh ssl-letsencrypt vectorweight.com

# Check certificate expiry
openssl x509 -in config/ssl/certs/server.crt -noout -dates

# Test HTTPS
curl -v https://ai.vectorweight.com/health

# Verify nginx config
docker compose exec nginx nginx -t
```
