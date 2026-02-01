#!/bin/bash

################################################################################
# Nginx Reverse Proxy Configuration Script for PDL
# 
# This script configures Nginx as a reverse proxy for PDL,
# allowing access via custom domain with SSL support.
################################################################################

set -euo pipefail

# Cores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Function for logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run this script as root (sudo)"
    exit 1
fi

# Function to validate domain
validate_domain() {
    local domain="$1"
    # Basic domain validation
    if [[ ! "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$ ]]; then
        return 1
    fi
    return 0
}

# Function to ensure include line is present in nginx.conf
configure_nginx_conf() {
    local NGINX_CONF="/etc/nginx/nginx.conf"
    local INCLUDE_LINE="    include /etc/nginx/sites-enabled/*;"

    # Create backup if it doesn't exist
    if [ ! -f "${NGINX_CONF}.bak" ]; then
        cp "$NGINX_CONF" "${NGINX_CONF}.bak"
        log_info "nginx.conf backup created."
    fi

    if ! grep -qF "$INCLUDE_LINE" "$NGINX_CONF"; then
        # Insert include inside http block
        sed -i "/http {/{
            :a
            n
            /}/!ba
            i\\
$INCLUDE_LINE
        }" "$NGINX_CONF"
        log_success "Line to include sites-enabled added to nginx.conf"
    else
        log_info "Line to include sites-enabled already present in nginx.conf"
    fi
}

# Request domain from user
echo "========================================================="
echo "  🔧 Nginx Reverse Proxy Configuration for PDL"
echo "========================================================="
echo

DOMAIN=""
while [ -z "$DOMAIN" ]; do
    read -p "Enter the domain (e.g., pdl.example.com): " DOMAIN
    DOMAIN=$(echo "$DOMAIN" | tr '[:upper:]' '[:lower:]' | xargs)
    
    if [ -z "$DOMAIN" ]; then
        log_error "Domain cannot be empty."
        continue
    fi
    
    if ! validate_domain "$DOMAIN"; then
        log_error "Invalid domain. Please enter a valid domain."
        DOMAIN=""
        continue
    fi
done

log_success "Domain configured: $DOMAIN"

# Ask about SSL
echo
read -p "Do you want to configure SSL with Let's Encrypt? (y/n): " SETUP_SSL
SETUP_SSL=$(echo "$SETUP_SSL" | tr '[:upper:]' '[:lower:]')

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    log_info "Installing Nginx..."
    apt-get update -qq
    apt-get install -y nginx
    log_success "Nginx installed."
else
    log_info "Nginx is already installed."
fi

# Ensure directories exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Configure nginx.conf to include sites-enabled
configure_nginx_conf

# Install Certbot and Nginx plugin for SSL if necessary
if [[ "$SETUP_SSL" =~ ^[yY]$ ]]; then
    NEED_INSTALL=false
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        NEED_INSTALL=true
        log_info "Certbot not found. Will be installed."
    fi
    
    # Check if certbot nginx plugin is installed
    if ! dpkg -l | grep -q "^ii.*python3-certbot-nginx"; then
        NEED_INSTALL=true
        log_info "Certbot Nginx plugin not found. Will be installed."
    fi
    
    if [ "$NEED_INSTALL" = true ]; then
        log_info "Installing Certbot and Nginx plugin..."
        apt-get update -qq
        apt-get install -y certbot python3-certbot-nginx
        log_success "Certbot and Nginx plugin installed."
    else
        log_info "Certbot and Nginx plugin are already installed."
    fi
fi

# Create Nginx configuration for reverse proxy
log_info "Creating Nginx configuration..."

if [[ "$SETUP_SSL" =~ ^[yY]$ ]]; then
    # Initial HTTP-only configuration (SSL will be added by Certbot)
    cat > /etc/nginx/sites-available/lineage-proxy << EOF
# HTTP - Initial configuration (SSL will be added by Certbot)
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Limite o tamanho de upload para 50 MB
    client_max_body_size 50M;

    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Proxy settings
    location / {
        proxy_pass http://localhost:6085;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF
else
    # Configuration without SSL (HTTP only)
    cat > /etc/nginx/sites-available/lineage-proxy << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Limit upload size to 50 MB
    client_max_body_size 50M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://localhost:6085;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF
fi

# Create symbolic link to enable the site
ln -sf /etc/nginx/sites-available/lineage-proxy /etc/nginx/sites-enabled/lineage-proxy
log_success "Site configuration enabled."

# Remove default Nginx configuration if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
    log_info "Default configuration removed."
fi

# Test Nginx configuration
log_info "Testing Nginx configuration..."
if nginx -t; then
    log_success "Nginx configuration is valid."
else
    log_error "Invalid Nginx configuration. Aborting."
    exit 1
fi

# Restart Nginx
log_info "Restarting Nginx..."
systemctl restart nginx
log_success "Nginx restarted."

# Configure SSL if requested
if [[ "$SETUP_SSL" =~ ^[yY]$ ]]; then
    echo
    log_info "Configuring SSL with Let's Encrypt..."
    log_warning "Make sure domain ${DOMAIN} points to this server."
    read -p "Press Enter to continue with SSL configuration..."
    
    if certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --register-unsafely-without-email; then
        log_success "SSL successfully configured!"
        systemctl reload nginx
    else
        log_warning "Failed to configure SSL automatically."
        log_info "You can configure it manually by running:"
        echo "  sudo certbot --nginx -d ${DOMAIN}"
    fi
fi

echo
log_success "Nginx configuration completed!"
echo
log_info "Configuration summary:"
echo "  - Domain: ${DOMAIN}"
echo "  - Proxy: http://localhost:6085"
if [[ "$SETUP_SSL" =~ ^[yY]$ ]]; then
    echo "  - SSL: Configured (if successful)"
    echo "  - Access: https://${DOMAIN}"
else
    echo "  - SSL: Not configured"
    echo "  - Access: http://${DOMAIN}"
    echo
    log_info "To configure SSL later, run:"
    echo "  sudo certbot --nginx -d ${DOMAIN}"
fi
echo
