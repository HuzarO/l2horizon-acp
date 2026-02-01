#!/bin/bash

################################################################################
# Database Backup Script - Painel Definitivo Lineage (PDL)
# 
# This script performs backup of the PDL PostgreSQL database.
# Supports automatic backup and backup restoration.
#
# Usage:
#   bash setup/backup.sh              # Create backup
#   bash setup/backup.sh restore      # Restore backup
#   bash setup/backup.sh list         # List available backups
################################################################################

set -euo pipefail

# Colors for output
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

# Directories and configurations
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MAX_BACKUPS=${MAX_BACKUPS:-7}  # Can be overridden by environment variable

# Detect Docker Compose command
detect_docker_compose() {
    if command -v docker-compose &> /dev/null && docker-compose version &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        log_error "Docker Compose not found!"
        exit 1
    fi
}

DOCKER_COMPOSE=$(detect_docker_compose)

# Function to load variables from .env
load_env_vars() {
    local env_file="${PROJECT_DIR}/.env"
    
    if [ ! -f "$env_file" ]; then
        log_error ".env file not found at: $env_file"
        log_info "Using default values (may not work)."
        CONTAINER_NAME="postgres"
        DB_NAME="db_name"
        DB_USER="db_user"
        return
    fi
    
    # Load variables from .env
    set -a
    source "$env_file" 2>/dev/null || true
    set +a
    
    # Set default values if they don't exist
    CONTAINER_NAME="${DB_CONTAINER_NAME:-postgres}"
    DB_NAME="${DB_NAME:-db_name}"
    DB_USER="${DB_USERNAME:-db_user}"
    DB_PASS="${DB_PASS:-db_pass}"
    
    log_debug "Loaded configurations:"
    log_debug "  Container: $CONTAINER_NAME"
    log_debug "  Database: $DB_NAME"
    log_debug "  User: $DB_USER"
}

# Function to check if container is running
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_error "Container '${CONTAINER_NAME}' is not running!"
        log_info "Start the container with: $DOCKER_COMPOSE up -d postgres"
        return 1
    fi
    
    # Check if PostgreSQL is ready
    log_info "Checking if PostgreSQL is ready..."
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" > /dev/null 2>&1; then
            log_success "PostgreSQL is ready."
            return 0
        fi
        log_debug "Attempt $attempt/$max_attempts - PostgreSQL not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL is not responding after $max_attempts attempts."
    return 1
}

# Function to create backup
create_backup() {
    log_info "Starting database backup..."
    
    # Load variables
    load_env_vars
    
    # Check container
    if ! check_container; then
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup filename
    BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"
    
    log_info "Creating backup: $(basename "$BACKUP_FILE")"
    log_debug "Container: $CONTAINER_NAME"
    log_debug "Database: $DB_NAME"
    log_debug "User: $DB_USER"
    
    # Perform backup
    if docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -F c -b -v -f "/tmp/backup_${TIMESTAMP}.dump" "${DB_NAME}" 2>/dev/null; then
        # Copy backup from container and compress
        docker cp "${CONTAINER_NAME}:/tmp/backup_${TIMESTAMP}.dump" - | gzip > "$BACKUP_FILE"
        docker exec "${CONTAINER_NAME}" rm -f "/tmp/backup_${TIMESTAMP}.dump" 2>/dev/null || true
        
        # Check if backup was created and has valid size
        if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
            local backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
            log_success "Backup created successfully!"
            log_info "  File: $(basename "$BACKUP_FILE")"
            log_info "  Size: $backup_size"
            log_info "  Location: $BACKUP_DIR"
        else
            log_error "Backup created but file is empty or doesn't exist!"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    else
        # Fallback: alternative method with direct pg_dump
        log_warning "Custom backup method failed, trying alternative method..."
        if docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "$BACKUP_FILE"; then
            if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
                local backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
                log_success "Backup created successfully (alternative method)!"
                log_info "  File: $(basename "$BACKUP_FILE")"
                log_info "  Size: $backup_size"
            else
                log_error "Backup failed!"
                rm -f "$BACKUP_FILE"
                exit 1
            fi
        else
            log_error "Failed to create backup!"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    fi
    
    # Clean old backups
    cleanup_old_backups
    
    echo
    log_success "Backup completed successfully!"
}

# Function to clean old backups
cleanup_old_backups() {
    if [ ! -d "$BACKUP_DIR" ]; then
        return
    fi
    
    local backup_count
    backup_count=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        local remove_count=$((backup_count - MAX_BACKUPS))
        log_info "Removing $remove_count old backup(s) (keeping the $MAX_BACKUPS most recent)..."
        
        find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | \
            sort -r | tail -n "$remove_count" | while read -r old_backup; do
            log_debug "Removing: $(basename "$old_backup")"
            rm -f "$old_backup"
        done
        
        log_success "Cleanup completed. Kept $MAX_BACKUPS most recent backup(s)."
    else
        log_debug "Total backups: $backup_count (limit: $MAX_BACKUPS). No cleanup needed."
    fi
}

# Function to list backups
list_backups() {
    log_info "Listing available backups..."
    echo
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null)" ]; then
        log_warning "No backups found at: $BACKUP_DIR"
        return
    fi
    
    local count=1
    echo -e "${CYAN}#${NC}  ${CYAN}Date/Time${NC}              ${CYAN}Size${NC}    ${CYAN}File${NC}"
    echo "─────────────────────────────────────────────────────────────────────"
    
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | \
        sort -r | while read -r backup_file; do
        local file_size=$(du -h "$backup_file" | cut -f1)
        local file_name=$(basename "$backup_file")
        local file_date=$(stat -c %y "$backup_file" 2>/dev/null | cut -d'.' -f1 || echo "N/A")
        
        printf "%-3s %-20s %-10s %s\n" "$count" "$file_date" "$file_size" "$file_name"
        count=$((count + 1))
    done
    
    echo
    log_info "Total backups: $(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | wc -l)"
}

# Function to restore backup
restore_backup() {
    log_info "Backup restore mode"
    echo
    
    # List available backups
    list_backups
    echo
    
    # Request backup file
    read -p "Enter the backup file name to restore (or number): " backup_input
    
    local backup_file=""
    
    # Check if it's a number
    if [[ "$backup_input" =~ ^[0-9]+$ ]]; then
        local selected=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | sort -r | sed -n "${backup_input}p")
        if [ -n "$selected" ] && [ -f "$selected" ]; then
            backup_file="$selected"
        else
            log_error "Invalid number!"
            exit 1
        fi
    else
        # Check if it's full path or just filename
        if [ -f "$backup_input" ]; then
            backup_file="$backup_input"
        elif [ -f "${BACKUP_DIR}/${backup_input}" ]; then
            backup_file="${BACKUP_DIR}/${backup_input}"
        else
            log_error "File not found: $backup_input"
            exit 1
        fi
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found!"
        exit 1
    fi
    
    log_warning "WARNING: This operation will OVERWRITE the current database!"
    read -p "Are you sure you want to continue? (type 'YES' to confirm): " confirm
    
    if [ "$confirm" != "YES" ]; then
        log_info "Restore cancelled."
        exit 0
    fi
    
    # Load variables
    load_env_vars
    
    # Check container
    if ! check_container; then
        exit 1
    fi
    
    log_info "Restoring backup: $(basename "$backup_file")"
    
    # Check backup type (custom dump or SQL)
    if [[ "$backup_file" == *.dump.gz ]] || gunzip -t "$backup_file" 2>/dev/null && gunzip -c "$backup_file" | file - | grep -q "PostgreSQL"; then
        # Custom format backup
        log_info "Detected custom format backup (pg_restore)..."
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_NAME}" pg_restore -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists --verbose 2>&1 | grep -v "NOTICE" || {
            log_error "Failed to restore backup!"
            exit 1
        }
    else
        # SQL backup (text)
        log_info "Detected SQL format backup (psql)..."
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1 || {
            log_error "Failed to restore backup!"
            exit 1
        }
    fi
    
    log_success "Backup restored successfully!"
    log_warning "Restart containers if necessary: $DOCKER_COMPOSE restart"
}

# Main function
main() {
    local action="${1:-backup}"
    
    case "$action" in
        backup|"")
            create_backup
            ;;
        restore)
            restore_backup
            ;;
        list)
            list_backups
            ;;
        help|--help|-h)
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  backup   - Create database backup (default)"
            echo "  restore  - Restore a backup"
            echo "  list     - List available backups"
            echo "  help     - Show this help"
            echo
            echo "Environment variables:"
            echo "  MAX_BACKUPS - Maximum number of backups to keep (default: 7)"
            echo
            ;;
        *)
            log_error "Unknown command: $action"
            echo "Use '$0 help' to see available commands."
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
