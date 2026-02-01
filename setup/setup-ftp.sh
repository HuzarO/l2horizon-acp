#!/bin/bash

################################################################################
# FTP Server Setup Script for Launcher
# 
# This script sets up an FTP server (vsftpd) to allow the host admin
# to host the server launcher files.
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

# Default directory for FTP
DEFAULT_FTP_DIR="/var/www/launcher"
FTP_DIR=""
FTP_USER="launcher"
FTP_PASSWORD=""

echo "========================================================="
echo "  📁 FTP Server Setup for Launcher"
echo "========================================================="
echo

# Request FTP directory
while [ -z "$FTP_DIR" ]; do
    read -p "Enter the directory for launcher files (default: ${DEFAULT_FTP_DIR}): " FTP_DIR
    FTP_DIR=$(echo "$FTP_DIR" | xargs)
    
    if [ -z "$FTP_DIR" ]; then
        FTP_DIR="$DEFAULT_FTP_DIR"
    fi
    
    # Validate directory (cannot be empty and must be absolute path)
    if [[ ! "$FTP_DIR" =~ ^/ ]]; then
        log_error "Directory must be an absolute path (starting with /)"
        FTP_DIR=""
        continue
    fi
done

log_success "Directory configured: $FTP_DIR"

# Request FTP user
echo
read -p "Enter the FTP username (default: ${FTP_USER}): " INPUT_USER
INPUT_USER=$(echo "$INPUT_USER" | xargs)
if [ -n "$INPUT_USER" ]; then
    FTP_USER="$INPUT_USER"
fi

# Validate username
if [[ ! "$FTP_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    log_error "Invalid username. Use only lowercase letters, numbers, hyphens and underscores."
    exit 1
fi

log_success "User configured: $FTP_USER"

# Request FTP password
echo
while [ -z "$FTP_PASSWORD" ]; do
    read -sp "Enter the password for the FTP user: " FTP_PASSWORD
    echo
    if [ -z "$FTP_PASSWORD" ]; then
        log_error "Password cannot be empty."
        continue
    fi
    
    if [ ${#FTP_PASSWORD} -lt 6 ]; then
        log_error "Password must have at least 6 characters."
        FTP_PASSWORD=""
        continue
    fi
    
    read -sp "Confirm password: " FTP_PASSWORD_CONFIRM
    echo
    
    if [ "$FTP_PASSWORD" != "$FTP_PASSWORD_CONFIRM" ]; then
        log_error "Passwords do not match."
        FTP_PASSWORD=""
        continue
    fi
done

log_success "Password configured."

# Install vsftpd if not installed
log_info "Checking vsftpd installation..."
if ! command -v vsftpd &> /dev/null; then
    log_info "Installing vsftpd..."
    apt-get update -qq
    apt-get install -y vsftpd
    log_success "vsftpd installed."
else
    log_info "vsftpd is already installed."
fi

# Create FTP directory if it doesn't exist
log_info "Creating FTP directory..."
mkdir -p "$FTP_DIR"
chmod 755 "$FTP_DIR"
log_success "Directory created: $FTP_DIR"

# Create FTP user if it doesn't exist
log_info "Configuring FTP user..."
if id "$FTP_USER" &>/dev/null; then
    log_warning "User $FTP_USER already exists. Updating password..."
    echo "$FTP_USER:$FTP_PASSWORD" | chpasswd
else
    # Create user without login shell and with home directory
    useradd -d "$FTP_DIR" -s /bin/bash -m "$FTP_USER" 2>/dev/null || {
        log_warning "User may already exist. Configuring password..."
    }
    echo "$FTP_USER:$FTP_PASSWORD" | chpasswd
    log_success "User $FTP_USER created."
fi

# Configure directory permissions
chown -R "$FTP_USER:$FTP_USER" "$FTP_DIR"
chmod 755 "$FTP_DIR"
log_success "Permissions configured."

# Backup vsftpd configuration
VSFTPD_CONF="/etc/vsftpd.conf"
if [ ! -f "${VSFTPD_CONF}.bak" ]; then
    cp "$VSFTPD_CONF" "${VSFTPD_CONF}.bak"
    log_info "vsftpd configuration backup created."
fi

# Configure vsftpd
log_info "Configuring vsftpd..."

# Create vsftpd configuration
cat > "$VSFTPD_CONF" << EOF
# vsftpd configuration for Launcher
# Original backup saved at: ${VSFTPD_CONF}.bak

# Allow anonymous access (disabled)
anonymous_enable=NO

# Allow local access
local_enable=YES

# Allow writing
write_enable=YES

# Local permissions mask
local_umask=022

# Allow anonymous upload (disabled)
anon_upload_enable=NO

# Allow directory creation
anon_mkdir_write_enable=NO

# Show welcome message
dirmessage_enable=YES

# Transfer log
xferlog_enable=YES

# Data port (passive)
connect_from_port_20=YES

# Passive mode
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=50000

# Allow chroot for local users
chroot_local_user=YES

# Allow local users to upload
allow_writeable_chroot=YES

# Enable SSL/TLS (optional, disabled by default)
ssl_enable=NO

# Security settings
secure_chroot_dir=/var/run/vsftpd/empty
pam_service_name=vsftpd
rsa_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
rsa_private_key_file=/etc/ssl/private/ssl-cert-snakeoil.key

# Enable IPv4
listen=YES
listen_ipv6=NO

# Timeout
idle_session_timeout=600
data_connection_timeout=120

# Maximum connections
max_clients=50
max_per_ip=5

# Banner
ftpd_banner=Welcome to Launcher FTP Server

# Enable ASCII
ascii_upload_enable=YES
ascii_download_enable=YES
EOF

log_success "vsftpd configuration created."

# Create directory for chroot if it doesn't exist
mkdir -p /var/run/vsftpd/empty
chmod 755 /var/run/vsftpd/empty

# Enable and start service
log_info "Enabling vsftpd service..."
systemctl enable vsftpd
systemctl restart vsftpd

# Check if service is running
if systemctl is-active --quiet vsftpd; then
    log_success "vsftpd service is running."
else
    log_error "Failed to start vsftpd service."
    log_info "Check logs with: journalctl -u vsftpd -n 50"
    exit 1
fi

# Configure firewall (if ufw is active)
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    log_info "Configuring firewall (ufw)..."
    ufw allow 21/tcp comment "FTP"
    ufw allow 40000:50000/tcp comment "FTP Passive"
    log_success "Firewall rules configured."
fi

echo
log_success "FTP configuration completed!"
echo
log_info "Configuration summary:"
echo "  - FTP Directory: ${FTP_DIR}"
echo "  - User: ${FTP_USER}"
echo "  - Port: 21"
echo "  - Passive ports: 40000-50000"
echo
log_info "To test the FTP connection:"
echo "  ftp://${FTP_USER}@$(hostname -I | awk '{print $1}')"
echo
log_info "Next step:"
echo "  Run the setup-nginx-launcher.sh script to configure Nginx with directory listing"
echo

