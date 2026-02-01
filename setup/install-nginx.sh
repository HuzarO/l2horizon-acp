#!/bin/bash

################################################################################
# Nginx Installation Script - Painel Definitivo Lineage (PDL)
# 
# This script installs and configures Nginx from the official repository.
# Supports stable or mainline version installation.
#
# Usage:
#   sudo bash setup/install-nginx.sh [stable|mainline]
################################################################################

set -euo pipefail

# Cores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
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

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run this script as root (sudo)"
    exit 1
fi

# Function to detect Ubuntu version
detect_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" = "ubuntu" ]; then
            echo "$VERSION_CODENAME"
        else
            log_warning "System is not Ubuntu. Trying to continue..."
            if command -v lsb_release &> /dev/null; then
                lsb_release -cs 2>/dev/null || echo "unknown"
            else
                echo "unknown"
            fi
        fi
    else
        log_warning "Unable to detect system version."
        echo "unknown"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Nginx is installed
nginx_installed() {
    command_exists nginx && nginx -v &>/dev/null
}

# Function to get current Nginx version
get_nginx_version() {
    if nginx_installed; then
        nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+' || echo "unknown"
    else
        echo "not installed"
    fi
}

# Function to install dependencies
install_dependencies() {
    log_info "Installing required dependencies..."
    
    apt-get update -qq
    apt-get install -y \
        curl \
        gnupg2 \
        ca-certificates \
        lsb-release \
        ubuntu-keyring \
        apt-transport-https \
        software-properties-common \
        >/dev/null 2>&1
    
    log_success "Dependencies installed."
}

# Function to configure Nginx repository
setup_nginx_repo() {
    local nginx_version="${1:-mainline}"
    local ubuntu_codename="$2"
    
    log_info "Configuring Nginx repository ($nginx_version)..."
    
    # Check if key already exists
    if [ ! -f /usr/share/keyrings/nginx-archive-keyring.gpg ]; then
        log_info "Importing Nginx GPG key..."
        curl -fsSL https://nginx.org/keys/nginx_signing.key | \
            gpg --dearmor -o /usr/share/keyrings/nginx-archive-keyring.gpg 2>/dev/null || {
            log_error "Failed to import Nginx GPG key."
            exit 1
        }
        log_success "GPG key imported."
    else
        log_debug "GPG key already exists."
    fi
    
    # Determine repository branch
    local repo_branch="mainline"
    if [ "$nginx_version" = "stable" ]; then
        repo_branch="nginx"
    fi
    
    # Add repository
    local repo_file="/etc/apt/sources.list.d/nginx.list"
    local repo_line="deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] https://nginx.org/packages/${repo_branch}/ubuntu ${ubuntu_codename} nginx"
    
    if [ ! -f "$repo_file" ] || ! grep -qF "$repo_line" "$repo_file" 2>/dev/null; then
        echo "$repo_line" | tee "$repo_file" >/dev/null
        log_success "Nginx repository configured ($nginx_version)."
    else
        log_debug "Repository already configured."
    fi
    
    # Update package list
    log_info "Updating package list..."
    apt-get update -qq
}

# Function to install Nginx
install_nginx() {
    local current_version
    current_version=$(get_nginx_version)
    
    if [ "$current_version" != "not installed" ]; then
        log_warning "Nginx is already installed (version: $current_version)"
        read -p "Do you want to reinstall? (y/n): " reinstall
        
        if [[ ! "$reinstall" =~ ^[yY]$ ]]; then
            log_info "Installation cancelled."
            return 0
        fi
        
        log_info "Removing old Nginx version..."
        apt-get remove -y nginx nginx-common nginx-full nginx-core 2>/dev/null || true
        log_success "Old version removed."
    fi
    
    log_info "Installing Nginx..."
    apt-get install -y nginx >/dev/null 2>&1 || {
        log_error "Failed to install Nginx."
        exit 1
    }
    
    local new_version
    new_version=$(get_nginx_version)
    log_success "Nginx successfully installed (version: $new_version)."
}

# Function to configure directories
setup_directories() {
    log_info "Configuring Nginx directories..."
    
    # Create necessary directories
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    mkdir -p /var/www/html/.well-known/acme-challenge
    
    # Configure permissions
    chown -R www-data:www-data /var/www/html/.well-known 2>/dev/null || true
    chmod -R 755 /var/www/html/.well-known
    
    log_success "Directories configured."
}

# Function to configure nginx.conf
configure_nginx_conf() {
    local NGINX_CONF="/etc/nginx/nginx.conf"
    local INCLUDE_LINE="    include /etc/nginx/sites-enabled/*;"
    local CLIENT_MAX_BODY_SIZE="    client_max_body_size 50M;"
    
    if [ ! -f "$NGINX_CONF" ]; then
        log_error "nginx.conf file not found: $NGINX_CONF"
        return 1
    fi
    
    log_info "Configuring nginx.conf..."
    
    # Create backup if it doesn't exist
    if [ ! -f "${NGINX_CONF}.bak" ]; then
        cp "$NGINX_CONF" "${NGINX_CONF}.bak"
        log_debug "nginx.conf backup created."
    fi
    
    # Add client_max_body_size if it doesn't exist
    if ! grep -qF "client_max_body_size" "$NGINX_CONF"; then
        # Insert client_max_body_size inside http block
        sed -i "/http {/a\\
$CLIENT_MAX_BODY_SIZE
" "$NGINX_CONF"
        log_success "client_max_body_size 50M added to nginx.conf"
    else
        log_debug "client_max_body_size already present in nginx.conf"
    fi
    
    if ! grep -qF "$INCLUDE_LINE" "$NGINX_CONF"; then
        # Insert the include inside http block
        sed -i "/http {/{
            :a
            n
            /}/!ba
            i\\
$INCLUDE_LINE
        }" "$NGINX_CONF"
        log_success "Line to include sites-enabled added to nginx.conf"
    else
        log_debug "Line to include sites-enabled already present in nginx.conf"
    fi
}

# Function to configure default-deny
setup_default_deny() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local deny_conf="${script_dir}/nginx-default-deny.conf"
    
    if [ ! -f "$deny_conf" ]; then
        log_warning "nginx-default-deny.conf file not found at: $deny_conf"
        log_info "Skipping default-deny configuration."
        return 0
    fi
    
    log_info "Configuring default-deny..."
    
    cp "$deny_conf" /etc/nginx/sites-available/default-deny
    ln -sf /etc/nginx/sites-available/default-deny /etc/nginx/sites-enabled/default-deny
    
    log_success "default-deny configuration enabled."
}

# Function to test configuration
test_nginx_config() {
    log_info "Testing Nginx configuration..."
    
    if nginx -t >/dev/null 2>&1; then
        log_success "Nginx configuration is valid."
        return 0
    else
        log_error "Invalid Nginx configuration!"
        log_info "Error details:"
        nginx -t
        return 1
    fi
}

# Function to start and enable service
start_nginx_service() {
    log_info "Starting Nginx service..."
    
    # Enable service
    systemctl enable nginx >/dev/null 2>&1 || {
        log_warning "Failed to enable service (may already be enabled)."
    }
    
    # Restart service
    systemctl restart nginx >/dev/null 2>&1 || {
        log_error "Failed to restart Nginx service."
        return 1
    }
    
    # Check status
    if systemctl is-active --quiet nginx; then
        log_success "Nginx service is running."
    else
        log_error "Nginx service is not running!"
        systemctl status nginx --no-pager
        return 1
    fi
}

# Main function
main() {
    local nginx_version="${1:-mainline}"
    
    # Validate version
    if [[ ! "$nginx_version" =~ ^(stable|mainline)$ ]]; then
        log_error "Invalid version: $nginx_version"
        log_info "Use: stable or mainline"
        exit 1
    fi
    
    clear
    echo "========================================================="
    echo "  🔧 Nginx Installation for PDL"
    echo "========================================================="
    echo
    
    # Detect Ubuntu version
    local ubuntu_codename
    ubuntu_codename=$(detect_ubuntu_version)
    
    if [ "$ubuntu_codename" = "unknown" ]; then
        log_warning "Unable to detect Ubuntu version."
        read -p "Enter Ubuntu codename (e.g., jammy, focal): " ubuntu_codename
        if [ -z "$ubuntu_codename" ]; then
            log_error "Ubuntu codename is required."
            exit 1
        fi
    else
        log_info "Ubuntu version detected: $ubuntu_codename"
    fi
    
    # Check current version
    local current_version
    current_version=$(get_nginx_version)
    if [ "$current_version" != "not installed" ]; then
        log_info "Current Nginx version: $current_version"
    fi
    
    echo
    log_info "Nginx version to install: $nginx_version"
    read -p "Do you want to continue? (y/n): " continue_install
    
    if [[ ! "$continue_install" =~ ^[yY]$ ]]; then
        log_info "Installation cancelled."
        exit 0
    fi
    
    echo
    
    # Install dependencies
    install_dependencies
    
    # Configure repository
    setup_nginx_repo "$nginx_version" "$ubuntu_codename"
    
    # Install Nginx
    install_nginx
    
    # Configure directories
    setup_directories
    
    # Configure nginx.conf
    configure_nginx_conf
    
    # Configure default-deny
    setup_default_deny
    
    # Test configuration
    if ! test_nginx_config; then
        log_error "Configuration failed. Fix errors before continuing."
        exit 1
    fi
    
    # Start service
    if ! start_nginx_service; then
        log_error "Failed to start Nginx service."
        exit 1
    fi
    
    # Show final information
    echo
    log_success "Nginx successfully installed and configured!"
    echo
    log_info "Information:"
    echo "  - Version: $(get_nginx_version)"
    echo "  - Status: $(systemctl is-active nginx)"
    echo "  - Configuration: /etc/nginx/nginx.conf"
    echo "  - Sites available: /etc/nginx/sites-available/"
    echo "  - Sites enabled: /etc/nginx/sites-enabled/"
    echo
    log_info "Useful commands:"
    echo "  - Check version: nginx -v"
    echo "  - Test configuration: nginx -t"
    echo "  - Start: systemctl start nginx"
    echo "  - Stop: systemctl stop nginx"
    echo "  - Restart: systemctl restart nginx"
    echo "  - Reload (no downtime): systemctl reload nginx"
    echo "  - View status: systemctl status nginx"
    echo
    log_info "Next steps:"
    echo "  - Configure reverse proxy: sudo bash setup/nginx-proxy.sh"
    echo "  - Install Certbot for SSL: sudo apt install certbot python3-certbot-nginx"
    echo
}

# Execute main function
main "$@"
