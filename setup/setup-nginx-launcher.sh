#!/bin/bash

################################################################################
# Nginx Setup Script for Launcher (Directory Listing)
# 
# This script configures Nginx to serve launcher files
# with directory listing enabled.
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

# Request information
echo "========================================================="
echo "  🌐 Nginx Setup for Launcher (Directory Listing)"
echo "========================================================="
echo

# Request domain
DOMAIN=""
while [ -z "$DOMAIN" ]; do
    read -p "Enter the domain for the launcher (e.g., launcher.example.com): " DOMAIN
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

# Request FTP directory
echo
DEFAULT_FTP_DIR="/var/www/launcher"
FTP_DIR=""
while [ -z "$FTP_DIR" ]; do
    read -p "Enter the launcher files directory (default: ${DEFAULT_FTP_DIR}): " FTP_DIR
    FTP_DIR=$(echo "$FTP_DIR" | xargs)
    
    if [ -z "$FTP_DIR" ]; then
        FTP_DIR="$DEFAULT_FTP_DIR"
    fi
    
    # Validate if directory exists
    if [ ! -d "$FTP_DIR" ]; then
        log_warning "Directory does not exist: $FTP_DIR"
        read -p "Do you want to create this directory? (y/n): " CREATE_DIR
        if [[ "$CREATE_DIR" =~ ^[yY]$ ]]; then
            mkdir -p "$FTP_DIR"
            chmod 755 "$FTP_DIR"
            log_success "Directory created: $FTP_DIR"
        else
            log_error "Directory does not exist. Aborting."
            exit 1
        fi
    fi
    
    # Validate if it's an absolute path
    if [[ ! "$FTP_DIR" =~ ^/ ]]; then
        log_error "Directory must be an absolute path (starting with /)"
        FTP_DIR=""
        continue
    fi
done

log_success "Directory configured: $FTP_DIR"

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    log_error "Nginx is not installed."
    log_info "Run first: sudo bash setup/install-nginx.sh"
    exit 1
fi

log_info "Nginx is installed."

# Ensure directories exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Configure nginx.conf to include sites-enabled
configure_nginx_conf

# Ask about SSL
echo
read -p "Do you want to configure SSL with Let's Encrypt? (y/n): " SETUP_SSL
SETUP_SSL=$(echo "$SETUP_SSL" | tr '[:upper:]' '[:lower:]')

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

# Create Nginx configuration with directory listing
log_info "Creating Nginx configuration..."

if [[ "$SETUP_SSL" =~ ^[yY]$ ]]; then
    # Initial HTTP-only configuration (SSL will be added by Certbot)
    cat > /etc/nginx/sites-available/launcher << EOF
# HTTP - Initial configuration (SSL will be added by Certbot)
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Root directory
    root ${FTP_DIR};
    index index.html index.htm;

    # Enable directory listing
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    autoindex_format html;

    # Limit upload size to 100 MB (for large launcher files)
    client_max_body_size 100M;

    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Main configuration with directory listing
    location / {
        try_files \$uri \$uri/ =404;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # Disable directory listing in specific subdirectories (optional)
    # location /private/ {
    #     autoindex off;
    # }

    # Logs
    access_log /var/log/nginx/launcher_access.log;
    error_log /var/log/nginx/launcher_error.log;
}
EOF
else
    # Configuration without SSL (HTTP only)
    cat > /etc/nginx/sites-available/launcher << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Root directory
    root ${FTP_DIR};
    index index.html index.htm;

    # Enable directory listing
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    autoindex_format html;

    # Limit upload size to 100 MB (for large launcher files)
    client_max_body_size 100M;

    # Main configuration with directory listing
    location / {
        try_files \$uri \$uri/ =404;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # Disable directory listing in specific subdirectories (optional)
    # location /private/ {
    #     autoindex off;
    # }

    # Logs
    access_log /var/log/nginx/launcher_access.log;
    error_log /var/log/nginx/launcher_error.log;
}
EOF
fi

# Create symbolic link to enable the site
ln -sf /etc/nginx/sites-available/launcher /etc/nginx/sites-enabled/launcher
log_success "Site configuration enabled."

# Test Nginx configuration
log_info "Testing Nginx configuration..."
if nginx -t; then
    log_success "✓ Nginx configuration is valid."
else
    log_error "✗ Invalid Nginx configuration. Aborting."
    log_info "Check the errors above and fix the configuration."
    exit 1
fi

# Restart Nginx
log_info "Restarting Nginx..."
if systemctl restart nginx; then
    log_success "✓ Nginx restarted successfully."
else
    log_error "✗ Failed to restart Nginx."
    exit 1
fi

# Check if Nginx is running
if systemctl is-active --quiet nginx; then
    log_success "✓ Nginx service is running."
else
    log_error "✗ Nginx service is not running."
    log_info "Check logs with: journalctl -u nginx -n 50"
    exit 1
fi

# Configure SSL if requested
if [[ "$SETUP_SSL" =~ ^[yY]$ ]]; then
    echo
    log_info "Configuring SSL with Let's Encrypt..."
    log_warning "Make sure domain ${DOMAIN} points to this server."
    read -p "Press Enter to continue with SSL configuration..."
    
    if certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --register-unsafely-without-email; then
        log_success "SSL successfully configured!"
        systemctl reload nginx
        
        # Check again after SSL
        if nginx -t; then
            log_success "✓ Nginx configuration validated after SSL."
        else
            log_error "✗ Configuration error after SSL."
            exit 1
        fi
    else
        log_warning "Failed to configure SSL automatically."
        log_info "You can configure it manually by running:"
        echo "  sudo certbot --nginx -d ${DOMAIN}"
    fi
fi

# Final validation
echo
log_info "Performing final configuration validation..."

# Check if configuration file exists
if [ ! -f /etc/nginx/sites-available/launcher ]; then
    log_error "✗ Configuration file not found."
    exit 1
fi
log_success "✓ Configuration file exists."

# Check if symbolic link exists
if [ ! -L /etc/nginx/sites-enabled/launcher ]; then
    log_error "✗ Symbolic link not found."
    exit 1
fi
log_success "✓ Symbolic link exists."

# Check if directory exists and has correct permissions
if [ ! -d "$FTP_DIR" ]; then
    log_error "✗ FTP directory does not exist: $FTP_DIR"
    exit 1
fi
log_success "✓ FTP directory exists: $FTP_DIR"

# Check directory permissions
if [ ! -r "$FTP_DIR" ]; then
    log_warning "⚠ Directory does not have read permission. Adjusting..."
    chmod 755 "$FTP_DIR"
fi
log_success "✓ Directory permissions verified."

# Test Nginx configuration again
if nginx -t 2>&1 | grep -q "test is successful"; then
    log_success "✓ Nginx configuration validated successfully."
else
    log_error "✗ Final Nginx validation failed."
    nginx -t
    exit 1
fi

# Check if service is responding
if systemctl is-active --quiet nginx; then
    log_success "✓ Nginx service is active and running."
else
    log_error "✗ Nginx service is not active."
    exit 1
fi

echo
log_success "Nginx configuration for Launcher completed!"
echo
log_info "Configuration summary:"
echo "  - Domain: ${DOMAIN}"
echo "  - Directory: ${FTP_DIR}"
echo "  - Directory listing: Enabled"
echo "  - Maximum upload: 100MB"
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
log_info "To test:"
echo "  curl -I http://${DOMAIN}"
echo "  or access in browser: http://${DOMAIN}"
echo

