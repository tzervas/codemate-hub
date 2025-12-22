# SSL Certificates Directory

This directory contains SSL certificates for the nginx reverse proxy.

## Contents (after generation)

- `ca.crt` - Certificate Authority certificate (import to trust self-signed certs)
- `ca.key` - CA private key (keep secure!)
- `server.crt` - Server certificate
- `server.key` - Server private key
- `fullchain.crt` - Full certificate chain (server + CA)
- `openssl.cnf` - OpenSSL configuration used for generation

## Generation

### Self-signed (development/LAN):
```bash
# Bash
../generate-self-signed.sh vectorweight.com

# PowerShell
..\Generate-SelfSignedCerts.ps1 -Domain vectorweight.com
```

### Let's Encrypt (production):
See [docs/SSL_DNS_SETUP.md](../../../docs/SSL_DNS_SETUP.md)

## Security Notes

- **Never commit** `ca.key` or `server.key` to version control
- The `.gitignore` should exclude `*.key` files
- Rotate certificates annually for self-signed
- Let's Encrypt auto-renews every 60-90 days
