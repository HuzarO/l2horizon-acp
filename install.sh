#!/bin/bash

################################################################################
# Definitive Lineage Panel (PDL) - Installation Script
# 
# This script automates the complete PDL installation using scripts
# from the setup/ folder. When setup scripts are updated, this
# script doesn't need to be changed, as it always uses the latest scripts.
#
# Repository: https://github.com/D3NKYT0/lineage
# Author: Daniel Amaral
################################################################################

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Directories
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SETUP_DIR="${SCRIPT_DIR}/setup"
readonly INSTALL_DIR="${SCRIPT_DIR}/.install_status"

# Log function
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

# Preserve original install.sh to avoid git issues
# This function ensures the file isn't modified during execution
# Restores the file from repository if there are changes (usually line endings)
preserve_install_sh() {
    local install_sh_path="${SCRIPT_DIR}/install.sh"
    if [ -f "$install_sh_path" ] && [ -d "${SCRIPT_DIR}/.git" ]; then
        # Check if there are uncommitted changes in install.sh
        if ! git -C "${SCRIPT_DIR}" diff --quiet "$install_sh_path" 2>/dev/null; then
            # There are changes (probably line endings), restore from git
            log_warning "Changes detected in install.sh (probably line endings)."
            log_info "Restoring from repository to avoid conflicts with git pull..."
            if git -C "${SCRIPT_DIR}" checkout -- "$install_sh_path" 2>/dev/null; then
                chmod +x "$install_sh_path" 2>/dev/null || true
                log_success "install.sh restored."
            else
                log_warning "Could not restore automatically. Run: git checkout -- install.sh"
            fi
        fi
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "⚠️  Running as root detected."
        log_info "Note: On servers, it's common to run as root."
        log_info "The script will continue normally. Some commands may not need sudo."
        echo
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command_exists git; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    if [ ! -d "${SETUP_DIR}" ]; then
        log_error "setup/ folder not found!"
        log_info "Make sure you're running this script from the project root."
        exit 1
    fi
    
    # Check if required scripts exist
    local required_scripts=("setup.sh" "build.sh")
    for script in "${required_scripts[@]}"; do
        if [ ! -f "${SETUP_DIR}/${script}" ]; then
            log_error "Required script not found: ${SETUP_DIR}/${script}"
            exit 1
        fi
    done
    
    log_success "Prerequisites verified."
}

# Function to detect Ubuntu version
detect_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" = "ubuntu" ]; then
            echo "$VERSION_CODENAME"
        else
            log_warning "System is not Ubuntu. Some features may not work."
            echo "unknown"
        fi
    else
        log_warning "Could not detect system version."
        echo "unknown"
    fi
}

# Function to detect old installations (made with previous scripts)
detect_existing_installation() {
    local project_dir="${SCRIPT_DIR}"
    
    # If status file already exists, it's a new installation
    if [ -f "${INSTALL_DIR}/.install_done" ]; then
        return 0  # Installation detected
    fi
    
    # Check if status directory exists with files from old script
    # Old script created: system_ready, docker_ready, repo_cloned, python_ready, env_created, htpasswd_created, fernet_key_generated, build_executed, superuser_created
    if [ -d "$INSTALL_DIR" ]; then
        local old_script_markers=("system_ready" "docker_ready" "repo_cloned" "python_ready" "env_created" "htpasswd_created" "fernet_key_generated" "build_executed" "superuser_created")
        for marker in "${old_script_markers[@]}"; do
            if [ -f "${INSTALL_DIR}/${marker}" ]; then
                log_info "Detected status file from old script: ${marker}"
                log_info "Old installation detected (previous script executed)."
                return 0  # Installation detected
            fi
        done
        
        # If any file exists in status directory, consider installed
        if [ "$(find "$INSTALL_DIR" -type f 2>/dev/null | wc -l)" -gt 0 ]; then
            log_info "Detected status directory with files (old installation)."
            return 0  # Installation detected
        fi
    fi
    
    # Check if .env exists with ENCRYPTION_KEY configured (not placeholder)
    local env_file="${project_dir}/.env"
    if [ -d "${project_dir}/lineage" ]; then
        env_file="${project_dir}/lineage/.env"
    fi
    
    if [ -f "$env_file" ]; then
        local encryption_key=$(grep -E "^ENCRYPTION_KEY\s*=" "$env_file" 2>/dev/null | head -1 | sed -E "s/^ENCRYPTION_KEY\s*=\s*['\"]?([^'\"]+)['\"]?.*$/\1/" | tr -d '[:space:]')
        local default_key="iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac="
        
        # If ENCRYPTION_KEY exists and is not the default/placeholder, it's an old installation
        if [ -n "$encryption_key" ] && [ "$encryption_key" != "$default_key" ]; then
            log_info "Detected existing ENCRYPTION_KEY in .env (old installation)."
            return 0  # Installation detected
        fi
    fi
    
    # Check if Docker containers are running
    if command_exists docker; then
        local running_containers=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "(site_http|site_wsgi|postgres|celery)" | wc -l)
        if [ "$running_containers" -gt 0 ]; then
            log_info "Detected Docker containers running (old installation)."
            return 0  # Installation detected
        fi
    fi
    
    # Check if manage.py exists (configured project)
    if [ -f "${project_dir}/manage.py" ] || [ -f "${project_dir}/lineage/manage.py" ]; then
        # If .env exists with important variables, consider installed
        if [ -f "$env_file" ]; then
            local has_secret_key=$(grep -qE "^SECRET_KEY\s*=" "$env_file" 2>/dev/null && echo "yes" || echo "no")
            local has_db_config=$(grep -qE "^DB_ENGINE\s*=" "$env_file" 2>/dev/null && echo "yes" || echo "no")
            
            if [ "$has_secret_key" = "yes" ] && [ "$has_db_config" = "yes" ]; then
                log_info "Detected configured project with complete .env (old installation)."
                return 0  # Installation detected
            fi
        fi
    fi
    
    # Check if lineage directory exists with configured structure (old script cloned to lineage/)
    if [ -d "${project_dir}/lineage" ]; then
        if [ -f "${project_dir}/lineage/manage.py" ] && [ -d "${project_dir}/lineage/.venv" ]; then
            log_info "Detected lineage project with configured virtual environment (old installation)."
            return 0  # Installation detected
        fi
    fi
    
    return 1  # Not an existing installation
}

# Function to preserve existing ENCRYPTION_KEY
preserve_encryption_key() {
    local env_file="${SCRIPT_DIR}/.env"
    
    # Old script cloned to lineage/, so check both locations
    if [ ! -f "$env_file" ] && [ -d "${SCRIPT_DIR}/lineage" ]; then
        env_file="${SCRIPT_DIR}/lineage/.env"
    fi
    
    if [ ! -f "$env_file" ]; then
        return 0  # No .env, no need to preserve
    fi
    
    # Extract current ENCRYPTION_KEY (if exists)
    local current_key=$(grep -E "^ENCRYPTION_KEY\s*=" "$env_file" 2>/dev/null | head -1 | sed -E "s/^ENCRYPTION_KEY\s*=\s*['\"]?([^'\"]+)['\"]?.*$/\1/" | tr -d '[:space:]')
    local default_key="iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac="
    
    # If key exists and is not placeholder, preserve it
    if [ -n "$current_key" ] && [ "$current_key" != "$default_key" ]; then
        log_warning "⚠️  Existing ENCRYPTION_KEY detected in: $env_file"
        log_warning "Key: ${current_key:0:20}..."
        log_warning "This key will be preserved to maintain encrypted data."
        log_warning "⚠️  IMPORTANT: No script will overwrite this key."
        
        # Create marker file to ensure key is not replaced
        mkdir -p "$INSTALL_DIR"
        echo "$current_key" > "${INSTALL_DIR}/.encryption_key_preserved"
        echo "$env_file" > "${INSTALL_DIR}/.encryption_key_location"
        return 0
    fi
    
    return 1  # No key to preserve
}

# Function to restore preserved ENCRYPTION_KEY if it was modified
restore_encryption_key() {
    local preserved_key_file="${INSTALL_DIR}/.encryption_key_preserved"
    local preserved_location_file="${INSTALL_DIR}/.encryption_key_location"
    
    # If there's no preserved key, no need to restore
    if [ ! -f "$preserved_key_file" ]; then
        return 0
    fi
    
    local preserved_key=$(cat "$preserved_key_file" | tr -d '[:space:]')
    if [ -z "$preserved_key" ]; then
        return 0  # Empty preserved key, don't restore
    fi
    
    # Determine .env location (where it was originally or where it should be now)
    local env_file="${SCRIPT_DIR}/.env"
    if [ -f "$preserved_location_file" ]; then
        local original_location=$(cat "$preserved_location_file")
        if [ -f "$original_location" ]; then
            env_file="$original_location"
        fi
    fi
    
    # Also check in lineage/.env (old script)
    if [ ! -f "$env_file" ] && [ -f "${SCRIPT_DIR}/lineage/.env" ]; then
        env_file="${SCRIPT_DIR}/lineage/.env"
    fi
    
    if [ ! -f "$env_file" ]; then
        return 0  # .env file not found, don't restore
    fi
    
    # Extract current ENCRYPTION_KEY from .env
    local current_key=$(grep -E "^ENCRYPTION_KEY\s*=" "$env_file" 2>/dev/null | head -1 | sed -E "s/^ENCRYPTION_KEY\s*=\s*['\"]?([^'\"]+)['\"]?.*$/\1/" | tr -d '[:space:]')
    local default_key="iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac="
    
    # If current key is different from preserved (and it's not just placeholder being replaced)
    if [ "$current_key" != "$preserved_key" ]; then
        # If preserved key is not placeholder, restore it
        if [ "$preserved_key" != "$default_key" ]; then
            log_warning "⚠️  ENCRYPTION_KEY was modified, restoring preserved key in: $env_file"
            
            # Backup before restoring
            if [ -f "$env_file" ]; then
                cp "$env_file" "${env_file}.before_key_restore.bkp" 2>/dev/null || true
            fi
            
            # Restore preserved key
            if grep -qE "^ENCRYPTION_KEY\s*=" "$env_file" 2>/dev/null; then
                # Replace existing line (supports different formats)
                sed -i "s|^ENCRYPTION_KEY\s*=.*|ENCRYPTION_KEY = '$preserved_key'|" "$env_file" 2>/dev/null || \
                sed -i "s|^ENCRYPTION_KEY\s*=.*|ENCRYPTION_KEY='$preserved_key'|" "$env_file" 2>/dev/null || \
                sed -i "/^ENCRYPTION_KEY\s*=/c\ENCRYPTION_KEY='$preserved_key'" "$env_file" 2>/dev/null || true
            else
                # Add if doesn't exist
                echo "" >> "$env_file"
                echo "ENCRYPTION_KEY = '$preserved_key'" >> "$env_file"
            fi
            
            log_success "✓ ENCRYPTION_KEY restored successfully."
            log_warning "⚠️  Backup created: ${env_file}.before_key_restore.bkp"
        fi
    else
        log_info "✓ ENCRYPTION_KEY preserved correctly in: $env_file"
    fi
}

# Function to check if it's a git repository
is_git_repository() {
    [ -d "${SCRIPT_DIR}/.git" ]
}

# Function to update repository (git stash + git pull)
update_repository() {
    if ! is_git_repository; then
        log_error "This directory is not a git repository."
        return 1
    fi
    
    log_info "Updating repository..."
    
    cd "${SCRIPT_DIR}" || {
        log_error "Could not access script directory."
        return 1
    }
    
    # Check if there are local changes before stashing
    if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
        log_info "Stashing local changes..."
        if git stash push -m "Automatic stash before update - $(date +%Y-%m-%d\ %H:%M:%S)"; then
            log_success "Local changes saved in stash."
        else
            log_warning "Failed to stash. Continuing anyway..."
        fi
    else
        log_info "No local changes to stash."
    fi
    
    # Pull updates
    log_info "Updating from remote repository..."
    if git pull; then
        log_success "Repository updated successfully."
        return 0
    else
        log_error "Failed to update repository."
        # Try to restore stash if there were changes
        if git stash list | grep -q .; then
            log_info "Trying to restore changes from stash..."
            git stash pop >/dev/null 2>&1 || true
        fi
        return 1
    fi
}

# Function to clone repository if necessary
clone_repository() {
    # Check if we are inside a repository (manage.py in root or subdirectory)
    if [ -f "${SCRIPT_DIR}/manage.py" ] || [ -f "${SCRIPT_DIR}/lineage/manage.py" ] || [ -d "${SCRIPT_DIR}/.git" ]; then
        log_success "Repository already exists."
        return 0
    fi
    
    log_info "Repository not found. Cloning from GitHub..."
    
    local repo_url="https://github.com/D3NKYT0/lineage.git"
    local clone_dir="${SCRIPT_DIR}/lineage"
    
    if [ -d "${clone_dir}" ]; then
        log_warning "Directory ${clone_dir} already exists. Skipping clone."
        log_info "If this is the project repository, you can continue."
    else
        git clone "${repo_url}" "${clone_dir}" || {
            log_error "Failed to clone repository."
            exit 1
        }
        log_success "Repository cloned successfully."
    fi
    
    # Verify if repository was cloned correctly
    if [ -d "${clone_dir}" ] && [ -f "${clone_dir}/manage.py" ]; then
        log_success "Repository found in: ${clone_dir}"
        # No longer exits here - allows installation to continue
    elif [ -d "${clone_dir}" ] && [ ! -f "${SCRIPT_DIR}/manage.py" ] && [ ! -f "${clone_dir}/manage.py" ]; then
        log_warning "Directory ${clone_dir} exists but doesn't seem to be the complete repository."
        log_info "Make sure you're running this script from the project root."
    fi
}

# Function to show menu of available scripts
show_scripts_menu() {
    echo
    log_info "Available scripts in setup/ folder:"
    echo
    echo "  📦 setup.sh                - Complete initial installation (Docker, Python, etc.)"
    echo "  🔨 build.sh                - Project build and deploy"
    echo "  💾 backup.sh               - Database backup"
    echo "  🌐 nginx-proxy.sh           - Configure reverse proxy with domain"
    echo "  🔧 install-nginx.sh         - Install Nginx from official repository"
    echo "  ⚙️  generate-env.sh         - Generate .env file interactively"
    echo "  📁 setup-ftp.sh             - Configure FTP server for launcher"
    echo "  🌐 setup-nginx-launcher.sh  - Configure Nginx with index of for launcher"
    echo
}

# Function to run specific script
run_setup_script() {
    local script_name="$1"
    local script_path="${SETUP_DIR}/${script_name}"
    
    if [ ! -f "$script_path" ]; then
        log_error "Script not found: $script_path"
        return 1
    fi
    
    log_info "Running: $script_name"
    log_info "=========================================="
    
    # Check if it needs sudo
    case "$script_name" in
        nginx-proxy.sh|install-nginx.sh|setup-ftp.sh|setup-nginx-launcher.sh)
            if [ "$EUID" -ne 0 ]; then
                log_info "This script requires root privileges."
                log_info "Running with sudo..."
                sudo bash "$script_path" || {
                    log_error "Failed to execute $script_name"
                    return 1
                }
            else
                bash "$script_path" || {
                    log_error "Failed to execute $script_name"
                    return 1
                }
            fi
            ;;
        *)
            bash "$script_path" || {
                log_error "Failed to execute $script_name"
                return 1
            }
            ;;
    esac
    
    log_success "Script $script_name executed successfully."
}

# Main installation function
main() {
    local action="${1:-install}"
    
    # Preserve install.sh BEFORE anything to avoid git issues
    preserve_install_sh
    
    clear
    
    echo "========================================================="
    echo "  🚀 Definitive Lineage Panel (PDL) - Installer"
    echo "========================================================="
    echo
    
    case "$action" in
        install|"")
            echo "This script will:"
            echo "  1. Check prerequisites"
            echo "  2. Run setup.sh (initial installation + build and deploy)"
            echo
            echo "Repository: https://github.com/D3NKYT0/lineage"
            echo
            ;;
        menu)
            show_scripts_menu
            echo
            log_info "Choose an option:"
            echo "  1) Complete installation (setup.sh + build.sh)"
            echo "  2) Only setup.sh"
            echo "  3) Only build.sh"
            if is_git_repository; then
                echo "  4) Update repository (git pull)"
                echo "  5) Database backup"
                echo "  6) Configure reverse proxy (nginx-proxy.sh)"
                echo "  7) Install Nginx (install-nginx.sh)"
                echo "  8) Generate .env file (generate-env.sh)"
                echo "  9) Configure FTP for launcher (setup-ftp.sh)"
                echo "  10) Configure Nginx for launcher (setup-nginx-launcher.sh)"
                echo "  11) List available scripts"
                echo "  12) Exit"
                echo
                read -p "Option: " menu_option
                
                case "$menu_option" in
                    1) action="install" ;;
                    2) action="setup" ;;
                    3) action="build" ;;
                    4) action="update" ;;
                    5) action="backup" ;;
                    6) action="nginx-proxy" ;;
                    7) action="install-nginx" ;;
                    8) action="generate-env" ;;
                    9) action="setup-ftp" ;;
                    10) action="setup-nginx-launcher" ;;
                    11) show_scripts_menu; exit 0 ;;
                    12) exit 0 ;;
                    *) log_error "Invalid option."; exit 1 ;;
                esac
            else
                echo "  4) Database backup"
                echo "  5) Configure reverse proxy (nginx-proxy.sh)"
                echo "  6) Install Nginx (install-nginx.sh)"
                echo "  7) Generate .env file (generate-env.sh)"
                echo "  8) Configure FTP for launcher (setup-ftp.sh)"
                echo "  9) Configure Nginx for launcher (setup-nginx-launcher.sh)"
                echo "  10) List available scripts"
                echo "  11) Exit"
                echo
                read -p "Option: " menu_option
                
                case "$menu_option" in
                    1) action="install" ;;
                    2) action="setup" ;;
                    3) action="build" ;;
                    4) action="backup" ;;
                    5) action="nginx-proxy" ;;
                    6) action="install-nginx" ;;
                    7) action="generate-env" ;;
                    8) action="setup-ftp" ;;
                    9) action="setup-nginx-launcher" ;;
                    10) show_scripts_menu; exit 0 ;;
                    11) exit 0 ;;
                    *) log_error "Invalid option."; exit 1 ;;
                esac
            fi
            ;;
        setup)
            log_info "Running only setup.sh..."
            check_root
            check_prerequisites
            clone_repository
            cd "${SCRIPT_DIR}"
            run_setup_script "setup.sh"
            exit 0
            ;;
        build)
            log_info "Running only build.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "build.sh"
            exit 0
            ;;
        update)
            log_info "Updating repository..."
            if ! is_git_repository; then
                log_error "This directory is not a git repository."
                exit 1
            fi
            if update_repository; then
                log_success "Repository updated successfully!"
            else
                log_error "Failed to update repository."
                exit 1
            fi
            exit 0
            ;;
        backup)
            log_info "Executando backup.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "backup.sh" "${@:2}"
            exit 0
            ;;
        nginx-proxy)
            log_info "Running nginx-proxy.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "nginx-proxy.sh"
            exit 0
            ;;
        install-nginx)
            log_info "Running install-nginx.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "install-nginx.sh" "${@:2}"
            exit 0
            ;;
        generate-env)
            log_info "Running generate-env.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "generate-env.sh"
            exit 0
            ;;
        setup-ftp)
            log_info "Running setup-ftp.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "setup-ftp.sh"
            exit 0
            ;;
        setup-nginx-launcher)
            log_info "Running setup-nginx-launcher.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "setup/ folder not found!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "setup-nginx-launcher.sh"
            exit 0
            ;;
        list|scripts)
            show_scripts_menu
            exit 0
            ;;
        help|--help|-h)
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  install          - Complete installation (setup.sh + build.sh) [default]"
            echo "  menu             - Interactive menu to choose script"
            echo "  setup            - Run only setup.sh"
            echo "  build            - Run only build.sh"
            echo "  update           - Update repository (git stash + git pull)"
            echo "  backup [args]         - Run backup.sh (accepts arguments: list, restore)"
            echo "  nginx-proxy           - Configure reverse proxy"
            echo "  install-nginx         - Install Nginx (accepts: stable, mainline)"
            echo "  generate-env          - Generate .env file interactively"
            echo "  setup-ftp             - Configure FTP server for launcher"
            echo "  setup-nginx-launcher  - Configure Nginx with index of for launcher"
            echo "  list                  - List all available scripts"
            echo "  help                  - Show this help"
            echo
            echo "Examples:"
            echo "  $0                    # Complete installation"
            echo "  $0 menu                # Interactive menu"
            echo "  $0 update              # Update repository"
            echo "  $0 backup list         # List backups"
            echo "  $0 install-nginx stable  # Install Nginx stable"
            echo
            exit 0
            ;;
        *)
            log_error "Unknown command: $action"
            echo "Use '$0 help' to see available commands."
            exit 1
            ;;
    esac
    
    # Continue with complete installation if action is still "install"
    if [ "$action" = "install" ]; then
        # Check if running as root (just a warning, doesn't block)
        check_root
    
        # Check prerequisites
        check_prerequisites
        
        # Detect Ubuntu version
        local ubuntu_version
        ubuntu_version=$(detect_ubuntu_version)
        log_info "Detected version: ${ubuntu_version}"
        
        # Clone repository if necessary
        clone_repository
        
        # Create status directory
        mkdir -p "${INSTALL_DIR}"
        
        # Preserve ENCRYPTION_KEY BEFORE any verification
        log_info "Checking existing installations and preserving settings..."
        preserve_encryption_key || true  # Continues even if no key found
        
        # Check if already installed (including old installations)
        local is_existing=false
        if detect_existing_installation || [ -f "${INSTALL_DIR}/.install_done" ]; then
            is_existing=true
        fi
        
        if [ "$is_existing" = "true" ]; then
            log_warning "⚠️  Existing installation detected!"
            log_info "Detected that the system was previously installed."
            echo
            
            # Check if ENCRYPTION_KEY is preserved
            if [ -f "${INSTALL_DIR}/.encryption_key_preserved" ]; then
                log_success "✓ ENCRYPTION_KEY will be preserved (encrypted data will be maintained)."
            fi
            
            echo
            log_info "What do you want to do?"
            echo "  (b) Run only build (update code without reinstalling)"
            echo "  (r) Redo complete installation (WARNING: may overwrite settings)"
            echo "  (s) Exit"
            echo
            read -p "Choose (b/r/s): " OPCAO </dev/tty || read OPCAO
            
            case "${OPCAO}" in
                b|B)
                    log_info "Executando apenas build.sh..."
                    cd "${SCRIPT_DIR}"
                    bash "${SETUP_DIR}/build.sh"
                    exit 0
                    ;;
                r|R)
                    log_warning "⚠️  WARNING: You chose to redo complete installation."
                    log_warning "This may overwrite existing settings."
                    echo
                    read -p "Are you SURE you want to continue? (type 'YES' to confirm): " CONFIRM
                    if [ "$CONFIRM" != "YES" ]; then
                        log_info "Operation cancelled."
                        exit 0
                    fi
                    log_info "Redoing complete installation..."
                    # DO NOT remove key preservation file if it exists
                    if [ -f "${INSTALL_DIR}/.encryption_key_preserved" ]; then
                        local preserved_key=$(cat "${INSTALL_DIR}/.encryption_key_preserved")
                        rm -rf "${INSTALL_DIR}"
                        mkdir -p "${INSTALL_DIR}"
                        echo "$preserved_key" > "${INSTALL_DIR}/.encryption_key_preserved"
                        log_info "ENCRYPTION_KEY preserved even with reinstallation."
                    else
                        rm -rf "${INSTALL_DIR}"
                        mkdir -p "${INSTALL_DIR}"
                    fi
                    ;;
                s|S)
                    log_info "Exiting..."
                    exit 0
                    ;;
                *)
                    log_error "Invalid option."
                    exit 1
                    ;;
            esac
        fi
        
        # Confirm installation
        echo
        read -p "Do you want to continue with installation? (y/n): " CONTINUE
        
        if [[ ! "${CONTINUE}" =~ ^[yY]$ ]]; then
            log_info "Installation cancelled."
            exit 0
        fi
        
        # Run setup.sh (which already runs build.sh internally)
        log_info "Running setup.sh..."
        log_info "=========================================="
        cd "${SCRIPT_DIR}"
        run_setup_script "setup.sh"
        
        # Restore preserved ENCRYPTION_KEY if necessary (protection against overwrite)
        restore_encryption_key
        
        # Mark installation as complete
        touch "${INSTALL_DIR}/.install_done"
        
        echo
        log_success "Installation completed successfully!"
        echo
        log_info "Next steps:"
        echo "  - Access: http://localhost:6085"
        echo "  - To update: bash setup/build.sh"
        echo "  - To stop: docker compose down"
        echo
        log_info "Additional scripts available:"
        echo "  - Backup: $0 backup [list|restore]"
        echo "  - Reverse proxy: $0 nginx-proxy"
        echo "  - Install Nginx: $0 install-nginx [stable|mainline]"
        echo "  - Configure FTP: $0 setup-ftp"
        echo "  - Configure Nginx Launcher: $0 setup-nginx-launcher"
        echo
        log_info "To see all scripts: $0 list"
        echo
    fi
}

# Run main function
main "$@"

