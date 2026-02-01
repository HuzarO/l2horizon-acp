#!/bin/bash

################################################################################
# .env File Generation Script - Painel Definitivo Lineage (PDL)
# 
# This script generates the .env file interactively, allowing you to choose
# which optional categories to include.
#
# Usage:
#   bash setup/generate-env.sh
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

# Function to create backup of .env before modifications (with incremental numbering)
backup_env_file() {
    local env_file="${1:-$ENV_FILE}"
    
    if [ ! -f "$env_file" ]; then
        return 0  # If the file doesn't exist, no need to backup
    fi
    
    # Find the next available backup number
    local backup_num=1
    local backup_file="${env_file}.bkp"
    
    while [ -f "$backup_file" ]; do
        backup_num=$((backup_num + 1))
        backup_file="${env_file}.bkp${backup_num}"
    done
    
    # Create the backup
    cp "$env_file" "$backup_file" 2>/dev/null || {
        log_error "Failed to create backup of .env at $backup_file"
        return 1
    }
    
    log_success "Backup of .env created: $backup_file"
    return 0
}

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# If we're inside a lineage directory, adjust
if [ -d "${PROJECT_DIR}/lineage" ] && [ -f "${PROJECT_DIR}/lineage/manage.py" ]; then
    PROJECT_DIR="${PROJECT_DIR}/lineage"
fi

ENV_FILE="${PROJECT_DIR}/.env"

# Function to generate Fernet key
generate_fernet_key() {
    python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
}

# Function to generate SECRET_KEY
generate_secret_key() {
    python3 - <<EOF
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
}

# Function to ask yes/no
ask_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    local answer
    
    if [ "$default" = "y" ]; then
        prompt="${prompt} (S/n): "
    else
        prompt="${prompt} (s/N): "
    fi
    
    read -p "$prompt" answer
    answer=$(echo "$answer" | tr '[:upper:]' '[:lower:]')
    
    if [ -z "$answer" ]; then
        answer="$default"
    fi
    
    if [[ "$answer" =~ ^[sSyY]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to ask for value
ask_value() {
    local prompt="$1"
    local default="$2"
    local value
    
    if [ -n "$default" ]; then
        read -p "$prompt [${default}]: " value
        echo "${value:-$default}"
    else
        read -p "$prompt: " value
        echo "$value"
    fi
}

# Function to read existing value from .env
get_existing_value() {
    local key="$1"
    local env_file="${2:-$ENV_FILE}"
    
    if [ ! -f "$env_file" ]; then
        return 1
    fi
    
    # Search for the variable in the file, removing quotes and spaces (accepts optional spaces around =)
    local value=$(grep -E "^${key}\s*=" "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2- | sed "s/^[[:space:]]*//;s/[[:space:]]*$//" | sed "s/^['\"]//;s/['\"]$//")
    
    if [ -n "$value" ]; then
        echo "$value"
        return 0
    fi
    
    return 1
}

# Function to check if variable exists in .env
var_exists() {
    local key="$1"
    local env_file="${2:-$ENV_FILE}"
    
    if [ ! -f "$env_file" ]; then
        return 1
    fi
    
    grep -qE "^${key}\s*=" "$env_file" 2>/dev/null
}

# Function to add section to .env
add_section() {
    local section_name="$1"
    echo "" >> "$ENV_FILE"
    echo "# =========================== $section_name ===========================" >> "$ENV_FILE"
}

# Function to add variable to .env
add_var() {
    local key="$1"
    local value="$2"
    
    # Create backup before adding (only once per session)
    if [ -z "${_BACKUP_CREATED:-}" ]; then
        backup_env_file "$ENV_FILE"
        _BACKUP_CREATED=1
    fi
    
    echo "${key}=${value}" >> "$ENV_FILE"
}

# Function to update or add variable in .env
update_var() {
    local key="$1"
    local value="$2"
    local env_file="${3:-$ENV_FILE}"
    
    # Create backup before updating (only once per session)
    if [ -z "${_BACKUP_CREATED:-}" ]; then
        backup_env_file "$env_file"
        _BACKUP_CREATED=1
    fi
    
    if var_exists "$key" "$env_file"; then
        # Update existing variable (preserves original line if possible, accepts optional spaces)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS uses a different version of sed
            sed -i '' "s|^${key}\s*=.*|${key}=${value}|" "$env_file"
        else
            sed -i "s|^${key}\s*=.*|${key}=${value}|" "$env_file"
        fi
    else
        # Add new variable
        echo "${key}=${value}" >> "$env_file"
    fi
}

# Function to generate required variables
generate_required() {
    local edit_mode="${1:-false}"
    log_info "Generating required variables..."
    
    if [ "$edit_mode" = "false" ]; then
        add_section "REQUIRED CONFIGURATION"
    fi
    
    # DEBUG
    local existing_debug=$(get_existing_value "DEBUG" 2>/dev/null || echo "")
    local debug_default="${existing_debug:-False}"
    if [ "$edit_mode" = "true" ] && [ -n "$existing_debug" ]; then
        if ask_yes_no "Enable DEBUG mode? (current: $existing_debug)" "$(echo "$existing_debug" | tr '[:upper:]' '[:lower:]')"; then
            update_var "DEBUG" "True"
        else
            update_var "DEBUG" "False"
        fi
    else
        if ask_yes_no "Enable DEBUG mode?" "$(echo "$debug_default" | tr '[:upper:]' '[:lower:]')"; then
            if [ "$edit_mode" = "true" ]; then
                update_var "DEBUG" "True"
            else
                add_var "DEBUG" "True"
            fi
        else
            if [ "$edit_mode" = "true" ]; then
                update_var "DEBUG" "False"
            else
                add_var "DEBUG" "False"
            fi
        fi
    fi
    
    # SECRET_KEY
    local existing_secret=$(get_existing_value "SECRET_KEY" 2>/dev/null || echo "")
    if [ -z "$existing_secret" ] || [ "$edit_mode" = "false" ]; then
        log_info "Generating SECRET_KEY..."
        SECRET_KEY=$(generate_secret_key 2>/dev/null || echo "41&l85x\$t8g5!wgvzxw9_v%jbph2msibr3x7jww5%1u8w*3ax")
        if [ "$edit_mode" = "true" ]; then
            update_var "SECRET_KEY" "$SECRET_KEY"
        else
            add_var "SECRET_KEY" "$SECRET_KEY"
        fi
    else
        log_info "SECRET_KEY already exists, keeping current value."
        if [ "$edit_mode" = "true" ]; then
            # Don't update, keep existing
            :
        fi
    fi
    
    # Database
    if [ "$edit_mode" = "false" ]; then
        add_section "DATABASE CONFIGURATION"
    fi
    local existing_db_engine=$(get_existing_value "DB_ENGINE" 2>/dev/null || echo "postgresql")
    DB_ENGINE=$(ask_value "Tipo de banco de dados (postgresql/mysql/sqlite3)" "$existing_db_engine")
    if [ "$edit_mode" = "true" ]; then
        update_var "DB_ENGINE" "$DB_ENGINE"
    else
        add_var "DB_ENGINE" "$DB_ENGINE"
    fi
    
    if [ "$DB_ENGINE" != "sqlite3" ]; then
        local existing_db_host=$(get_existing_value "DB_HOST" 2>/dev/null || echo "postgres")
        local existing_db_name=$(get_existing_value "DB_NAME" 2>/dev/null || echo "db_name")
        local existing_db_user=$(get_existing_value "DB_USERNAME" 2>/dev/null || echo "db_user")
        local existing_db_pass=$(get_existing_value "DB_PASS" 2>/dev/null || echo "db_pass")
        local existing_db_port=$(get_existing_value "DB_PORT" 2>/dev/null || echo "5432")
        
        DB_HOST=$(ask_value "Database host" "$existing_db_host")
        DB_NAME=$(ask_value "Database name" "$existing_db_name")
        DB_USERNAME=$(ask_value "Database user" "$existing_db_user")
        DB_PASS=$(ask_value "Database password" "$existing_db_pass")
        DB_PORT=$(ask_value "Database port" "$existing_db_port")
        
        if [ "$edit_mode" = "true" ]; then
            update_var "DB_HOST" "$DB_HOST"
            update_var "DB_NAME" "$DB_NAME"
            update_var "DB_USERNAME" "$DB_USERNAME"
            update_var "DB_PASS" "$DB_PASS"
            update_var "DB_PORT" "$DB_PORT"
        else
            add_var "DB_HOST" "$DB_HOST"
            add_var "DB_NAME" "$DB_NAME"
            add_var "DB_USERNAME" "$DB_USERNAME"
            add_var "DB_PASS" "$DB_PASS"
            add_var "DB_PORT" "$DB_PORT"
        fi
    fi
    
    # Redis e Cache
    if [ "$edit_mode" = "false" ]; then
        add_section "REDIS AND CACHE"
    fi
    local existing_cache=$(get_existing_value "DJANGO_CACHE_REDIS_URI" 2>/dev/null || echo "redis://redis:6379/0")
    local existing_broker=$(get_existing_value "CELERY_BROKER_URI" 2>/dev/null || echo "redis://redis:6379/1")
    local existing_backend=$(get_existing_value "CELERY_BACKEND_URI" 2>/dev/null || echo "redis://redis:6379/1")
    local existing_channels=$(get_existing_value "CHANNELS_BACKEND" 2>/dev/null || echo "redis://redis:6379/2")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "DJANGO_CACHE_REDIS_URI" "$existing_cache"
        update_var "CELERY_BROKER_URI" "$existing_broker"
        update_var "CELERY_BACKEND_URI" "$existing_backend"
        update_var "CHANNELS_BACKEND" "$existing_channels"
    else
        add_var "DJANGO_CACHE_REDIS_URI" "$existing_cache"
        add_var "CELERY_BROKER_URI" "$existing_broker"
        add_var "CELERY_BACKEND_URI" "$existing_backend"
        add_var "CHANNELS_BACKEND" "$existing_channels"
    fi
    
    # Auditor
    local existing_auditor=$(get_existing_value "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" 2>/dev/null || echo "True")
    local auditor_default=$(echo "$existing_auditor" | tr '[:upper:]' '[:lower:]')
    if [ "$edit_mode" = "true" ] && [ -n "$existing_auditor" ]; then
        if ask_yes_no "Enable auditor middleware? (current: $existing_auditor)" "$auditor_default"; then
            update_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "True"
        else
            update_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "False"
        fi
    else
        if ask_yes_no "Enable auditor middleware?" "$auditor_default"; then
            if [ "$edit_mode" = "true" ]; then
                update_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "True"
            else
                add_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "True"
            fi
        else
            if [ "$edit_mode" = "true" ]; then
                update_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "False"
            else
                add_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "False"
            fi
        fi
    fi
    
    # Hostname
    if [ "$edit_mode" = "false" ]; then
        add_section "HOSTNAME CONFIGURATION"
    fi
    local existing_hostname=$(get_existing_value "RENDER_EXTERNAL_HOSTNAME" 2>/dev/null || echo "pdl.denky.dev.br")
    local existing_frontend=$(get_existing_value "RENDER_EXTERNAL_FRONTEND" 2>/dev/null || echo "$existing_hostname")
    RENDER_EXTERNAL_HOSTNAME=$(ask_value "External hostname" "$existing_hostname")
    RENDER_EXTERNAL_FRONTEND=$(ask_value "External frontend" "$existing_frontend")
    if [ "$edit_mode" = "true" ]; then
        update_var "RENDER_EXTERNAL_HOSTNAME" "$RENDER_EXTERNAL_HOSTNAME"
        update_var "RENDER_EXTERNAL_FRONTEND" "$RENDER_EXTERNAL_FRONTEND"
    else
        add_var "RENDER_EXTERNAL_HOSTNAME" "$RENDER_EXTERNAL_HOSTNAME"
        add_var "RENDER_EXTERNAL_FRONTEND" "$RENDER_EXTERNAL_FRONTEND"
    fi
    
    # Encryption
    # IMPORTANT: DO NOT overwrite existing keys to avoid breaking encrypted data
    local existing_encryption=$(get_existing_value "ENCRYPTION_KEY" 2>/dev/null || echo "")
    local default_key="iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac="
    
    if [ -z "$existing_encryption" ]; then
        # If it doesn't exist, generate a new one
        log_info "Generating ENCRYPTION_KEY..."
        ENCRYPTION_KEY=$(generate_fernet_key 2>/dev/null || echo "$default_key")
        if [ "$edit_mode" = "true" ]; then
            update_var "ENCRYPTION_KEY" "'$ENCRYPTION_KEY'"
        else
            add_var "ENCRYPTION_KEY" "'$ENCRYPTION_KEY'"
        fi
    elif [ "$existing_encryption" = "$default_key" ]; then
        # If it's the default/placeholder key, replace it (first installation only)
        log_warning "ENCRYPTION_KEY is the default/placeholder key. Generating new key..."
        ENCRYPTION_KEY=$(generate_fernet_key 2>/dev/null || echo "$default_key")
        if [ "$edit_mode" = "true" ]; then
            update_var "ENCRYPTION_KEY" "'$ENCRYPTION_KEY'"
            log_warning "WARNING: If there is encrypted data with the old key, it cannot be decrypted!"
        else
            add_var "ENCRYPTION_KEY" "'$ENCRYPTION_KEY'"
        fi
    else
        # If it already exists and is not the default key, keep it (CRITICAL: do not overwrite!)
        log_info "ENCRYPTION_KEY already exists, keeping current value (will not be changed to preserve encrypted data)."
    fi
    local existing_upload_size=$(get_existing_value "DATA_UPLOAD_MAX_MEMORY_SIZE" 2>/dev/null || echo "31457280")
    if [ "$edit_mode" = "true" ]; then
        update_var "DATA_UPLOAD_MAX_MEMORY_SIZE" "$existing_upload_size"
    else
        add_var "DATA_UPLOAD_MAX_MEMORY_SIZE" "$existing_upload_size"
    fi
    
    # hCaptcha
    if [ "$edit_mode" = "false" ]; then
        add_section "HCAPTCHA CONFIGURATION"
    fi
    local existing_hcaptcha_site=$(get_existing_value "CONFIG_HCAPTCHA_SITE_KEY" 2>/dev/null || echo "bcf40348-fa88-4570-a752-2asdasde0b2bc")
    local existing_hcaptcha_secret=$(get_existing_value "CONFIG_HCAPTCHA_SECRET_KEY" 2>/dev/null || echo "ES_dc688fdasdasdadasdas4e918093asddsddsafa3f1b")
    local existing_max_attempts=$(get_existing_value "CONFIG_LOGIN_MAX_ATTEMPTS" 2>/dev/null || echo "3")
    local existing_fail_open=$(get_existing_value "CONFIG_HCAPTCHA_FAIL_OPEN" 2>/dev/null || echo "False")
    
    CONFIG_HCAPTCHA_SITE_KEY=$(ask_value "hCaptcha Site Key" "$existing_hcaptcha_site")
    CONFIG_HCAPTCHA_SECRET_KEY=$(ask_value "hCaptcha Secret Key" "$existing_hcaptcha_secret")
    CONFIG_LOGIN_MAX_ATTEMPTS=$(ask_value "Maximum number of login attempts" "$existing_max_attempts")
    CONFIG_HCAPTCHA_FAIL_OPEN=$(ask_value "hCaptcha Fail Open (True/False)" "$existing_fail_open")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "CONFIG_HCAPTCHA_SITE_KEY" "$CONFIG_HCAPTCHA_SITE_KEY"
        update_var "CONFIG_HCAPTCHA_SECRET_KEY" "$CONFIG_HCAPTCHA_SECRET_KEY"
        update_var "CONFIG_LOGIN_MAX_ATTEMPTS" "$CONFIG_LOGIN_MAX_ATTEMPTS"
        update_var "CONFIG_HCAPTCHA_FAIL_OPEN" "$CONFIG_HCAPTCHA_FAIL_OPEN"
    else
        add_var "CONFIG_HCAPTCHA_SITE_KEY" "$CONFIG_HCAPTCHA_SITE_KEY"
        add_var "CONFIG_HCAPTCHA_SECRET_KEY" "$CONFIG_HCAPTCHA_SECRET_KEY"
        add_var "CONFIG_LOGIN_MAX_ATTEMPTS" "$CONFIG_LOGIN_MAX_ATTEMPTS"
        add_var "CONFIG_HCAPTCHA_FAIL_OPEN" "$CONFIG_HCAPTCHA_FAIL_OPEN"
    fi
    
    # Lineage Query Module
    if [ "$edit_mode" = "false" ]; then
        add_section "LINEAGE QUERY MODULE"
    fi
    local existing_query_module=$(get_existing_value "LINEAGE_QUERY_MODULE" 2>/dev/null || echo "dreamv3")
    LINEAGE_QUERY_MODULE=$(ask_value "Lineage query module" "$existing_query_module")
    if [ "$edit_mode" = "true" ]; then
        update_var "LINEAGE_QUERY_MODULE" "$LINEAGE_QUERY_MODULE"
    else
        add_var "LINEAGE_QUERY_MODULE" "$LINEAGE_QUERY_MODULE"
    fi
    
    # Localization
    if [ "$edit_mode" = "false" ]; then
        add_section "LOCALIZATION"
    fi
    local existing_lang=$(get_existing_value "CONFIG_LANGUAGE_CODE" 2>/dev/null | sed 's/"//g' || echo "pt")
    local existing_tz=$(get_existing_value "CONFIG_TIME_ZONE" 2>/dev/null | sed 's/"//g' || echo "America/Recife")
    local existing_decimal=$(get_existing_value "CONFIG_DECIMAL_SEPARATOR" 2>/dev/null | sed "s/'//g" || echo ",")
    local existing_thousand=$(get_existing_value "CONFIG_USE_THOUSAND_SEPARATOR" 2>/dev/null || echo "True")
    local existing_datetime=$(get_existing_value "CONFIG_DATETIME_FORMAT" 2>/dev/null | sed "s/'//g" || echo "d/m/Y H:i:s")
    local existing_date=$(get_existing_value "CONFIG_DATE_FORMAT" 2>/dev/null | sed "s/'//g" || echo "d/m/Y")
    local existing_time=$(get_existing_value "CONFIG_TIME_FORMAT" 2>/dev/null | sed "s/'//g" || echo "H:i:s")
    local existing_gmt=$(get_existing_value "CONFIG_GMT_OFFSET" 2>/dev/null || echo "-3")
    
    CONFIG_LANGUAGE_CODE=$(ask_value "Language code (pt/en/es)" "$existing_lang")
    CONFIG_TIME_ZONE=$(ask_value "Time zone" "$existing_tz")
    CONFIG_DECIMAL_SEPARATOR=$(ask_value "Decimal separator" "$existing_decimal")
    CONFIG_USE_THOUSAND_SEPARATOR=$(ask_value "Use thousand separator? (True/False)" "$existing_thousand")
    CONFIG_DATETIME_FORMAT=$(ask_value "Date/time format" "$existing_datetime")
    CONFIG_DATE_FORMAT=$(ask_value "Date format" "$existing_date")
    CONFIG_TIME_FORMAT=$(ask_value "Time format" "$existing_time")
    CONFIG_GMT_OFFSET=$(ask_value "GMT offset" "$existing_gmt")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "CONFIG_LANGUAGE_CODE" "\"$CONFIG_LANGUAGE_CODE\""
        update_var "CONFIG_TIME_ZONE" "\"$CONFIG_TIME_ZONE\""
        update_var "CONFIG_DECIMAL_SEPARATOR" "'$CONFIG_DECIMAL_SEPARATOR'"
        update_var "CONFIG_USE_THOUSAND_SEPARATOR" "$CONFIG_USE_THOUSAND_SEPARATOR"
        update_var "CONFIG_DATETIME_FORMAT" "'$CONFIG_DATETIME_FORMAT'"
        update_var "CONFIG_DATE_FORMAT" "'$CONFIG_DATE_FORMAT'"
        update_var "CONFIG_TIME_FORMAT" "'$CONFIG_TIME_FORMAT'"
        update_var "CONFIG_GMT_OFFSET" "$CONFIG_GMT_OFFSET"
    else
        add_var "CONFIG_LANGUAGE_CODE" "\"$CONFIG_LANGUAGE_CODE\""
        add_var "CONFIG_TIME_ZONE" "\"$CONFIG_TIME_ZONE\""
        add_var "CONFIG_DECIMAL_SEPARATOR" "'$CONFIG_DECIMAL_SEPARATOR'"
        add_var "CONFIG_USE_THOUSAND_SEPARATOR" "$CONFIG_USE_THOUSAND_SEPARATOR"
        add_var "CONFIG_DATETIME_FORMAT" "'$CONFIG_DATETIME_FORMAT'"
        add_var "CONFIG_DATE_FORMAT" "'$CONFIG_DATE_FORMAT'"
        add_var "CONFIG_TIME_FORMAT" "'$CONFIG_TIME_FORMAT'"
        add_var "CONFIG_GMT_OFFSET" "$CONFIG_GMT_OFFSET"
    fi
    
    # Project Info
    if [ "$edit_mode" = "false" ]; then
        add_section "PROJECT INFORMATION"
    fi
    local existing_title=$(get_existing_value "PROJECT_TITLE" 2>/dev/null || echo "Lineage 2 PDL")
    local existing_author=$(get_existing_value "PROJECT_AUTHOR" 2>/dev/null || echo "Lineage 2 PDL")
    local existing_desc=$(get_existing_value "PROJECT_DESCRIPTION" 2>/dev/null || echo "PDL is a panel born with the mission of offering powerful tools for Lineage 2 private server administrators.")
    local existing_keywords=$(get_existing_value "PROJECT_KEYWORDS" 2>/dev/null || echo "lineage l2 panel server")
    local existing_url=$(get_existing_value "PROJECT_URL" 2>/dev/null || echo "https://pdl.denky.dev.br")
    local existing_logo=$(get_existing_value "PROJECT_LOGO_URL" 2>/dev/null || echo "/static/assets/img/logo_painel.png")
    local existing_favicon=$(get_existing_value "PROJECT_FAVICON_ICO" 2>/dev/null || echo "/static/assets/img/ico.jpg")
    local existing_manifest=$(get_existing_value "PROJECT_FAVICON_MANIFEST" 2>/dev/null || echo "/static/assets/img/favicon/site.webmanifest")
    local existing_theme=$(get_existing_value "PROJECT_THEME_COLOR" 2>/dev/null || echo "#ffffff")
    
    PROJECT_TITLE=$(ask_value "Project title" "$existing_title")
    PROJECT_AUTHOR=$(ask_value "Project author" "$existing_author")
    PROJECT_DESCRIPTION=$(ask_value "Project description" "$existing_desc")
    PROJECT_KEYWORDS=$(ask_value "Keywords" "$existing_keywords")
    PROJECT_URL=$(ask_value "Project URL" "$existing_url")
    PROJECT_LOGO_URL=$(ask_value "Logo URL" "$existing_logo")
    PROJECT_FAVICON_ICO=$(ask_value "Favicon .ico URL" "$existing_favicon")
    PROJECT_FAVICON_MANIFEST=$(ask_value "Manifest URL" "$existing_manifest")
    PROJECT_THEME_COLOR=$(ask_value "Theme color" "$existing_theme")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "PROJECT_TITLE" "$PROJECT_TITLE"
        update_var "PROJECT_AUTHOR" "$PROJECT_AUTHOR"
        update_var "PROJECT_DESCRIPTION" "$PROJECT_DESCRIPTION"
        update_var "PROJECT_KEYWORDS" "$PROJECT_KEYWORDS"
        update_var "PROJECT_URL" "$PROJECT_URL"
        update_var "PROJECT_LOGO_URL" "$PROJECT_LOGO_URL"
        update_var "PROJECT_FAVICON_ICO" "$PROJECT_FAVICON_ICO"
        update_var "PROJECT_FAVICON_MANIFEST" "$PROJECT_FAVICON_MANIFEST"
        update_var "PROJECT_THEME_COLOR" "$PROJECT_THEME_COLOR"
    else
        add_var "PROJECT_TITLE" "$PROJECT_TITLE"
        add_var "PROJECT_AUTHOR" "$PROJECT_AUTHOR"
        add_var "PROJECT_DESCRIPTION" "$PROJECT_DESCRIPTION"
        add_var "PROJECT_KEYWORDS" "$PROJECT_KEYWORDS"
        add_var "PROJECT_URL" "$PROJECT_URL"
        add_var "PROJECT_LOGO_URL" "$PROJECT_LOGO_URL"
        add_var "PROJECT_FAVICON_ICO" "$PROJECT_FAVICON_ICO"
        add_var "PROJECT_FAVICON_MANIFEST" "$PROJECT_FAVICON_MANIFEST"
        add_var "PROJECT_THEME_COLOR" "$PROJECT_THEME_COLOR"
    fi
    
    # Social Media Links
    if [ "$edit_mode" = "false" ]; then
        add_section "SOCIAL MEDIA LINKS"
    fi
    local existing_discord=$(get_existing_value "PROJECT_DISCORD_URL" 2>/dev/null | sed "s/'//g" || echo "https://discord.gg/your-link-here")
    local existing_youtube=$(get_existing_value "PROJECT_YOUTUBE_URL" 2>/dev/null | sed "s/'//g" || echo "https://www.youtube.com/@your-channel")
    local existing_facebook=$(get_existing_value "PROJECT_FACEBOOK_URL" 2>/dev/null | sed "s/'//g" || echo "https://www.facebook.com/your-page")
    local existing_instagram=$(get_existing_value "PROJECT_INSTAGRAM_URL" 2>/dev/null | sed "s/'//g" || echo "https://www.instagram.com/your-profile")
    
    PROJECT_DISCORD_URL=$(ask_value "URL do Discord" "$existing_discord")
    PROJECT_YOUTUBE_URL=$(ask_value "URL do YouTube" "$existing_youtube")
    PROJECT_FACEBOOK_URL=$(ask_value "URL do Facebook" "$existing_facebook")
    PROJECT_INSTAGRAM_URL=$(ask_value "URL do Instagram" "$existing_instagram")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "PROJECT_DISCORD_URL" "'$PROJECT_DISCORD_URL'"
        update_var "PROJECT_YOUTUBE_URL" "'$PROJECT_YOUTUBE_URL'"
        update_var "PROJECT_FACEBOOK_URL" "'$PROJECT_FACEBOOK_URL'"
        update_var "PROJECT_INSTAGRAM_URL" "'$PROJECT_INSTAGRAM_URL'"
    else
        add_var "PROJECT_DISCORD_URL" "'$PROJECT_DISCORD_URL'"
        add_var "PROJECT_YOUTUBE_URL" "'$PROJECT_YOUTUBE_URL'"
        add_var "PROJECT_FACEBOOK_URL" "'$PROJECT_FACEBOOK_URL'"
        add_var "PROJECT_INSTAGRAM_URL" "'$PROJECT_INSTAGRAM_URL'"
    fi
    
    # Basic Flags
    if [ "$edit_mode" = "false" ]; then
        add_section "BASIC FLAGS"
    fi
    local existing_docker=$(get_existing_value "RUNNING_IN_DOCKER" 2>/dev/null || echo "True")
    local existing_slogan=$(get_existing_value "SLOGAN" 2>/dev/null || echo "True")
    local existing_lineage_db=$(get_existing_value "LINEAGE_DB_ENABLED" 2>/dev/null || echo "False")
    local existing_theme_errors=$(get_existing_value "SHOW_THEME_ERRORS_TO_USERS" 2>/dev/null || echo "True")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "RUNNING_IN_DOCKER" "$existing_docker"
        update_var "SLOGAN" "$existing_slogan"
        update_var "LINEAGE_DB_ENABLED" "$existing_lineage_db"
        update_var "SHOW_THEME_ERRORS_TO_USERS" "$existing_theme_errors"
    else
        add_var "RUNNING_IN_DOCKER" "$existing_docker"
        add_var "SLOGAN" "$existing_slogan"
        add_var "LINEAGE_DB_ENABLED" "$existing_lineage_db"
        add_var "SHOW_THEME_ERRORS_TO_USERS" "$existing_theme_errors"
    fi
}

# Function to generate Email configuration
generate_email_config() {
    local edit_mode="${1:-false}"
    if [ "$edit_mode" = "false" ]; then
        add_section "EMAIL CONFIGURATION"
    fi
    
    local existing_email_enable=$(get_existing_value "CONFIG_EMAIL_ENABLE" 2>/dev/null || echo "False")
    local email_enable_default=$(echo "$existing_email_enable" | tr '[:upper:]' '[:lower:]')
    
    if ask_yes_no "Enable email sending?" "$email_enable_default"; then
        add_var "CONFIG_EMAIL_ENABLE" "True"
        local existing_tls=$(get_existing_value "CONFIG_EMAIL_USE_TLS" 2>/dev/null || echo "True")
        local existing_smtp=$(get_existing_value "CONFIG_EMAIL_HOST" 2>/dev/null || echo "smtp.domain.com")
        local existing_port=$(get_existing_value "CONFIG_EMAIL_PORT" 2>/dev/null || echo "587")
        local existing_user=$(get_existing_value "CONFIG_EMAIL_HOST_USER" 2>/dev/null || echo "mail@mail.dev.br")
        local existing_pass=$(get_existing_value "CONFIG_EMAIL_HOST_PASSWORD" 2>/dev/null || echo "password")
        local existing_from=$(get_existing_value "CONFIG_DEFAULT_FROM_EMAIL" 2>/dev/null || echo "$existing_user")
        
        CONFIG_EMAIL_USE_TLS=$(ask_yes_no "Use TLS?" "$(echo "$existing_tls" | tr '[:upper:]' '[:lower:]')" && echo "True" || echo "False")
        CONFIG_EMAIL_HOST=$(ask_value "SMTP server" "$existing_smtp")
        CONFIG_EMAIL_PORT=$(ask_value "SMTP port" "$existing_port")
        CONFIG_EMAIL_HOST_USER=$(ask_value "Email user" "$existing_user")
        CONFIG_EMAIL_HOST_PASSWORD=$(ask_value "Email password" "$existing_pass")
        CONFIG_DEFAULT_FROM_EMAIL=$(ask_value "Default sender email" "$existing_from")
        
        if [ "$edit_mode" = "true" ]; then
            update_var "CONFIG_EMAIL_USE_TLS" "$CONFIG_EMAIL_USE_TLS"
            update_var "CONFIG_EMAIL_HOST" "$CONFIG_EMAIL_HOST"
            update_var "CONFIG_EMAIL_PORT" "$CONFIG_EMAIL_PORT"
            update_var "CONFIG_EMAIL_HOST_USER" "$CONFIG_EMAIL_HOST_USER"
            update_var "CONFIG_EMAIL_HOST_PASSWORD" "$CONFIG_EMAIL_HOST_PASSWORD"
            update_var "CONFIG_DEFAULT_FROM_EMAIL" "$CONFIG_DEFAULT_FROM_EMAIL"
        else
            add_var "CONFIG_EMAIL_USE_TLS" "$CONFIG_EMAIL_USE_TLS"
            add_var "CONFIG_EMAIL_HOST" "$CONFIG_EMAIL_HOST"
            add_var "CONFIG_EMAIL_PORT" "$CONFIG_EMAIL_PORT"
            add_var "CONFIG_EMAIL_HOST_USER" "$CONFIG_EMAIL_HOST_USER"
            add_var "CONFIG_EMAIL_HOST_PASSWORD" "$CONFIG_EMAIL_HOST_PASSWORD"
            add_var "CONFIG_DEFAULT_FROM_EMAIL" "$CONFIG_DEFAULT_FROM_EMAIL"
        fi
    else
        if [ "$edit_mode" = "true" ]; then
            update_var "CONFIG_EMAIL_ENABLE" "False"
            update_var "CONFIG_EMAIL_USE_TLS" "True"
            update_var "CONFIG_EMAIL_HOST" "smtp.domain.com"
            update_var "CONFIG_EMAIL_PORT" "587"
            update_var "CONFIG_EMAIL_HOST_USER" "mail@mail.dev.br"
            update_var "CONFIG_EMAIL_HOST_PASSWORD" "password"
            update_var "CONFIG_DEFAULT_FROM_EMAIL" "mail@mail.dev.br"
        else
            add_var "CONFIG_EMAIL_ENABLE" "False"
            add_var "CONFIG_EMAIL_USE_TLS" "True"
            add_var "CONFIG_EMAIL_HOST" "smtp.domain.com"
            add_var "CONFIG_EMAIL_PORT" "587"
            add_var "CONFIG_EMAIL_HOST_USER" "mail@mail.dev.br"
            add_var "CONFIG_EMAIL_HOST_PASSWORD" "password"
            add_var "CONFIG_DEFAULT_FROM_EMAIL" "mail@mail.dev.br"
        fi
    fi
}

# Function to generate Lineage DB configuration
generate_lineage_db_config() {
    local edit_mode="${1:-false}"
    if [ "$edit_mode" = "false" ]; then
        add_section "LINEAGE DATABASE CONFIGURATION"
    fi
    
    local existing_db_name=$(get_existing_value "LINEAGE_DB_NAME" 2>/dev/null || echo "l2jdb")
    local existing_db_user=$(get_existing_value "LINEAGE_DB_USER" 2>/dev/null || echo "l2user")
    local existing_db_pass=$(get_existing_value "LINEAGE_DB_PASSWORD" 2>/dev/null || echo "yourPasswordHere")
    local existing_db_host=$(get_existing_value "LINEAGE_DB_HOST" 2>/dev/null || echo "192.168.1.100")
    local existing_db_port=$(get_existing_value "LINEAGE_DB_PORT" 2>/dev/null || echo "3306")
    
    LINEAGE_DB_NAME=$(ask_value "Lineage database name" "$existing_db_name")
    LINEAGE_DB_USER=$(ask_value "Lineage database user" "$existing_db_user")
    LINEAGE_DB_PASSWORD=$(ask_value "Lineage database password" "$existing_db_pass")
    LINEAGE_DB_HOST=$(ask_value "Lineage database host" "$existing_db_host")
    LINEAGE_DB_PORT=$(ask_value "Lineage database port" "$existing_db_port")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "LINEAGE_DB_NAME" "$LINEAGE_DB_NAME"
        update_var "LINEAGE_DB_USER" "$LINEAGE_DB_USER"
        update_var "LINEAGE_DB_PASSWORD" "$LINEAGE_DB_PASSWORD"
        update_var "LINEAGE_DB_HOST" "$LINEAGE_DB_HOST"
        update_var "LINEAGE_DB_PORT" "$LINEAGE_DB_PORT"
    else
        add_var "LINEAGE_DB_NAME" "$LINEAGE_DB_NAME"
        add_var "LINEAGE_DB_USER" "$LINEAGE_DB_USER"
        add_var "LINEAGE_DB_PASSWORD" "$LINEAGE_DB_PASSWORD"
        add_var "LINEAGE_DB_HOST" "$LINEAGE_DB_HOST"
        add_var "LINEAGE_DB_PORT" "$LINEAGE_DB_PORT"
    fi
}

# Function to generate AWS S3 configuration
generate_s3_config() {
    local edit_mode="${1:-false}"
    if [ "$edit_mode" = "false" ]; then
        add_section "AWS S3 CONFIGURATION"
    fi
    
    local existing_use_s3=$(get_existing_value "USE_S3" 2>/dev/null || echo "False")
    local s3_default=$(echo "$existing_use_s3" | tr '[:upper:]' '[:lower:]')
    
    if ask_yes_no "Use AWS S3 for storage?" "$s3_default"; then
        add_var "USE_S3" "True"
        AWS_ACCESS_KEY_ID=$(ask_value "AWS Access Key ID" "your_aws_access_key_id")
        AWS_SECRET_ACCESS_KEY=$(ask_value "AWS Secret Access Key" "your_aws_secret_access_key")
        AWS_STORAGE_BUCKET_NAME=$(ask_value "S3 bucket name" "your-bucket-name")
        AWS_S3_REGION_NAME=$(ask_value "S3 region" "us-east-1")
        AWS_S3_CUSTOM_DOMAIN=$(ask_value "S3 custom domain" "${AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com")
        
        add_var "AWS_ACCESS_KEY_ID" "$AWS_ACCESS_KEY_ID"
        add_var "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY"
        add_var "AWS_STORAGE_BUCKET_NAME" "$AWS_STORAGE_BUCKET_NAME"
        add_var "AWS_S3_REGION_NAME" "$AWS_S3_REGION_NAME"
        add_var "AWS_S3_CUSTOM_DOMAIN" "$AWS_S3_CUSTOM_DOMAIN"
    else
        add_var "USE_S3" "False"
        add_var "AWS_ACCESS_KEY_ID" "your_aws_access_key_id"
        add_var "AWS_SECRET_ACCESS_KEY" "your_aws_secret_access_key"
        add_var "AWS_STORAGE_BUCKET_NAME" "your-bucket-name"
        add_var "AWS_S3_REGION_NAME" "us-east-1"
        add_var "AWS_S3_CUSTOM_DOMAIN" "your-bucket-name.s3.amazonaws.com"
    fi
}

# Function to generate Payment configuration
generate_payments_config() {
    local edit_mode="${1:-false}"
    if [ "$edit_mode" = "false" ]; then
        add_section "PAYMENT CONFIGURATION"
    fi
    
    # Mercado Pago
    echo
    log_info "Mercado Pago configuration:"
    local existing_mp_activate=$(get_existing_value "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" 2>/dev/null || echo "False")
    local existing_mp_token=$(get_existing_value "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" 2>/dev/null | sed 's/"//g' || echo "APP_USR-0000000000000000-000000-00000000000000000000000000000000-000000000")
    local existing_mp_public=$(get_existing_value "CONFIG_MERCADO_PAGO_PUBLIC_KEY" 2>/dev/null | sed 's/"//g' || echo "APP_USR-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    local existing_mp_client=$(get_existing_value "CONFIG_MERCADO_PAGO_CLIENT_ID" 2>/dev/null | sed 's/"//g' || echo "0000000000000000")
    local existing_mp_secret=$(get_existing_value "CONFIG_MERCADO_PAGO_CLIENT_SECRET" 2>/dev/null | sed 's/"//g' || echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    local existing_mp_signature=$(get_existing_value "CONFIG_MERCADO_PAGO_SIGNATURE" 2>/dev/null | sed 's/"//g' || echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    
    local mp_activate_default=$(echo "$existing_mp_activate" | tr '[:upper:]' '[:lower:]')
    if ask_yes_no "Enable payments via Mercado Pago?" "$mp_activate_default"; then
        CONFIG_MERCADO_PAGO_ACCESS_TOKEN=$(ask_value "Mercado Pago Access Token" "$existing_mp_token")
        CONFIG_MERCADO_PAGO_PUBLIC_KEY=$(ask_value "Mercado Pago Public Key" "$existing_mp_public")
        CONFIG_MERCADO_PAGO_CLIENT_ID=$(ask_value "Mercado Pago Client ID" "$existing_mp_client")
        CONFIG_MERCADO_PAGO_CLIENT_SECRET=$(ask_value "Mercado Pago Client Secret" "$existing_mp_secret")
        CONFIG_MERCADO_PAGO_SIGNATURE=$(ask_value "Mercado Pago Signature" "$existing_mp_signature")
        
        if [ "$edit_mode" = "true" ]; then
            update_var "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" "True"
            update_var "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" "\"$CONFIG_MERCADO_PAGO_ACCESS_TOKEN\""
            update_var "CONFIG_MERCADO_PAGO_PUBLIC_KEY" "\"$CONFIG_MERCADO_PAGO_PUBLIC_KEY\""
            update_var "CONFIG_MERCADO_PAGO_CLIENT_ID" "\"$CONFIG_MERCADO_PAGO_CLIENT_ID\""
            update_var "CONFIG_MERCADO_PAGO_CLIENT_SECRET" "\"$CONFIG_MERCADO_PAGO_CLIENT_SECRET\""
            update_var "CONFIG_MERCADO_PAGO_SIGNATURE" "\"$CONFIG_MERCADO_PAGO_SIGNATURE\""
        else
            add_var "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" "True"
            add_var "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" "\"$CONFIG_MERCADO_PAGO_ACCESS_TOKEN\""
            add_var "CONFIG_MERCADO_PAGO_PUBLIC_KEY" "\"$CONFIG_MERCADO_PAGO_PUBLIC_KEY\""
            add_var "CONFIG_MERCADO_PAGO_CLIENT_ID" "\"$CONFIG_MERCADO_PAGO_CLIENT_ID\""
            add_var "CONFIG_MERCADO_PAGO_CLIENT_SECRET" "\"$CONFIG_MERCADO_PAGO_CLIENT_SECRET\""
            add_var "CONFIG_MERCADO_PAGO_SIGNATURE" "\"$CONFIG_MERCADO_PAGO_SIGNATURE\""
        fi
    else
        if [ "$edit_mode" = "true" ]; then
            update_var "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" "False"
            update_var "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" "\"$existing_mp_token\""
            update_var "CONFIG_MERCADO_PAGO_PUBLIC_KEY" "\"$existing_mp_public\""
            update_var "CONFIG_MERCADO_PAGO_CLIENT_ID" "\"$existing_mp_client\""
            update_var "CONFIG_MERCADO_PAGO_CLIENT_SECRET" "\"$existing_mp_secret\""
            update_var "CONFIG_MERCADO_PAGO_SIGNATURE" "\"$existing_mp_signature\""
        else
            add_var "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" "False"
            add_var "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" "\"APP_USR-0000000000000000-000000-00000000000000000000000000000000-000000000\""
            add_var "CONFIG_MERCADO_PAGO_PUBLIC_KEY" "\"APP_USR-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\""
            add_var "CONFIG_MERCADO_PAGO_CLIENT_ID" "\"0000000000000000\""
            add_var "CONFIG_MERCADO_PAGO_CLIENT_SECRET" "\"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\""
            add_var "CONFIG_MERCADO_PAGO_SIGNATURE" "\"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\""
        fi
    fi
    
    # Stripe
    echo
    log_info "Stripe configuration:"
    local existing_stripe_activate=$(get_existing_value "CONFIG_STRIPE_ACTIVATE_PAYMENTS" 2>/dev/null || echo "False")
    local existing_stripe_secret=$(get_existing_value "CONFIG_STRIPE_SECRET_KEY" 2>/dev/null | sed "s/'//g" || echo "sk_test_51RK0cORmyaPSbmPDEMjN0DaasdasdadadasdafgagdhhfasdfsfnbgRrtdKRwHRakfrQub9SQ5jQEUNvTfrcFxbw00gsqFR09W")
    local existing_stripe_webhook=$(get_existing_value "CONFIG_STRIPE_WEBHOOK_SECRET" 2>/dev/null | sed "s/'//g" || echo "whsec_5dzjceF7LgeYzasdasdasdZpSuPq")
    
    local stripe_activate_default=$(echo "$existing_stripe_activate" | tr '[:upper:]' '[:lower:]')
    if ask_yes_no "Enable payments via Stripe?" "$stripe_activate_default"; then
        CONFIG_STRIPE_SECRET_KEY=$(ask_value "Stripe Secret Key" "$existing_stripe_secret")
        CONFIG_STRIPE_WEBHOOK_SECRET=$(ask_value "Stripe Webhook Secret" "$existing_stripe_webhook")
        
        if [ "$edit_mode" = "true" ]; then
            update_var "CONFIG_STRIPE_ACTIVATE_PAYMENTS" "True"
            update_var "CONFIG_STRIPE_SECRET_KEY" "'$CONFIG_STRIPE_SECRET_KEY'"
            update_var "CONFIG_STRIPE_WEBHOOK_SECRET" "'$CONFIG_STRIPE_WEBHOOK_SECRET'"
        else
            add_var "CONFIG_STRIPE_ACTIVATE_PAYMENTS" "True"
            add_var "CONFIG_STRIPE_SECRET_KEY" "'$CONFIG_STRIPE_SECRET_KEY'"
            add_var "CONFIG_STRIPE_WEBHOOK_SECRET" "'$CONFIG_STRIPE_WEBHOOK_SECRET'"
        fi
    else
        if [ "$edit_mode" = "true" ]; then
            update_var "CONFIG_STRIPE_ACTIVATE_PAYMENTS" "False"
            update_var "CONFIG_STRIPE_SECRET_KEY" "'$existing_stripe_secret'"
            update_var "CONFIG_STRIPE_WEBHOOK_SECRET" "'$existing_stripe_webhook'"
        else
            add_var "CONFIG_STRIPE_ACTIVATE_PAYMENTS" "False"
            add_var "CONFIG_STRIPE_SECRET_KEY" "'sk_test_51RK0cORmyaPSbmPDEMjN0DaasdasdadadasdafgagdhhfasdfsfnbgRrtdKRwHRakfrQub9SQ5jQEUNvTfrcFxbw00gsqFR09W'"
            add_var "CONFIG_STRIPE_WEBHOOK_SECRET" "'whsec_5dzjceF7LgeYzasdasdasdZpSuPq'"
        fi
    fi
}

# Function to generate Social Login configuration
generate_social_login_config() {
    add_section "SOCIAL LOGIN CONFIGURATION"
    
    if ask_yes_no "Enable social login?" "n"; then
        add_var "SOCIAL_LOGIN_ENABLED" "True"
        
        # Google
        if ask_yes_no "Enable Google login?" "n"; then
            add_var "SOCIAL_LOGIN_GOOGLE_ENABLED" "True"
            GOOGLE_CLIENT_ID=$(ask_value "Google Client ID" "3029asdasd17179-i4lfm6078nrov5lhv9628bch2o8vlqs8.apps.googleusercontent.com")
            GOOGLE_SECRET_KEY=$(ask_value "Google Secret Key" "GOCSPX-bWw9hU6Mb3pasdasdasd")
            add_var "GOOGLE_CLIENT_ID" "$GOOGLE_CLIENT_ID"
            add_var "GOOGLE_SECRET_KEY" "$GOOGLE_SECRET_KEY"
        else
            add_var "SOCIAL_LOGIN_GOOGLE_ENABLED" "False"
            add_var "GOOGLE_CLIENT_ID" "3029asdasd17179-i4lfm6078nrov5lhv9628bch2o8vlqs8.apps.googleusercontent.com"
            add_var "GOOGLE_SECRET_KEY" "GOCSPX-bWw9hU6Mb3pasdasdasd"
        fi
        
        # GitHub
        if ask_yes_no "Enable GitHub login?" "n"; then
            add_var "SOCIAL_LOGIN_GITHUB_ENABLED" "True"
            GITHUB_CLIENT_ID=$(ask_value "GitHub Client ID" "Ov23liadadadwcXpjog38V")
            GITHUB_SECRET_KEY=$(ask_value "GitHub Secret Key" "ea0d1c77b910eadadadada65a7cbddee1bd07deb")
            add_var "GITHUB_CLINET_ID" "$GITHUB_CLIENT_ID"
            add_var "GITHUB_SECRET_KEY" "$GITHUB_SECRET_KEY"
        else
            add_var "SOCIAL_LOGIN_GITHUB_ENABLED" "False"
            add_var "GITHUB_CLINET_ID" "Ov23liadadadwcXpjog38V"
            add_var "GITHUB_SECRET_KEY" "ea0d1c77b910eadadadada65a7cbddee1bd07deb"
        fi
        
        # Discord
        if ask_yes_no "Enable Discord login?" "n"; then
            add_var "SOCIAL_LOGIN_DISCORD_ENABLED" "True"
            DISCORD_CLIENT_ID=$(ask_value "Discord Client ID" "13836455adada77550336")
            DISCORD_SECRET_KEY=$(ask_value "Discord Secret Key" "Gs9db5OmQ9dadadadadad8CtOQuLKx42fdf")
            add_var "DISCORD_CLIENT_ID" "$DISCORD_CLIENT_ID"
            add_var "DISCORD_SECRET_KEY" "$DISCORD_SECRET_KEY"
        else
            add_var "SOCIAL_LOGIN_DISCORD_ENABLED" "False"
            add_var "DISCORD_CLIENT_ID" "13836455adada77550336"
            add_var "DISCORD_SECRET_KEY" "Gs9db5OmQ9dadadadadad8CtOQuLKx42fdf"
        fi
        
        if ask_yes_no "Show social login section in interface?" "n"; then
            add_var "SOCIAL_LOGIN_SHOW_SECTION" "True"
        else
            add_var "SOCIAL_LOGIN_SHOW_SECTION" "False"
        fi
    else
        add_var "SOCIAL_LOGIN_ENABLED" "False"
        add_var "SOCIAL_LOGIN_GOOGLE_ENABLED" "False"
        add_var "SOCIAL_LOGIN_GITHUB_ENABLED" "False"
        add_var "SOCIAL_LOGIN_DISCORD_ENABLED" "False"
        add_var "SOCIAL_LOGIN_SHOW_SECTION" "False"
        add_var "GOOGLE_CLIENT_ID" "3029asdasd17179-i4lfm6078nrov5lhv9628bch2o8vlqs8.apps.googleusercontent.com"
        add_var "GOOGLE_SECRET_KEY" "GOCSPX-bWw9hU6Mb3pasdasdasd"
        add_var "GITHUB_CLINET_ID" "Ov23liadadadwcXpjog38V"
        add_var "GITHUB_SECRET_KEY" "ea0d1c77b910eadadadada65a7cbddee1bd07deb"
        add_var "DISCORD_CLIENT_ID" "13836455adada77550336"
        add_var "DISCORD_SECRET_KEY" "Gs9db5OmQ9dadadadadad8CtOQuLKx42fdf"
    fi
}

# Function to generate Server Status configuration
generate_server_status_config() {
    local edit_mode="${1:-false}"
    if [ "$edit_mode" = "false" ]; then
        add_section "SERVER STATUS CONFIGURATION"
    fi
    
    local existing_game_ip=$(get_existing_value "GAME_SERVER_IP" 2>/dev/null || echo "192.168.1.100")
    local existing_game_port=$(get_existing_value "GAME_SERVER_PORT" 2>/dev/null || echo "7777")
    local existing_login_port=$(get_existing_value "LOGIN_SERVER_PORT" 2>/dev/null || echo "2106")
    local existing_timeout=$(get_existing_value "SERVER_STATUS_TIMEOUT" 2>/dev/null || echo "1")
    local existing_force_game=$(get_existing_value "FORCE_GAME_SERVER_STATUS" 2>/dev/null || echo "auto")
    local existing_force_login=$(get_existing_value "FORCE_LOGIN_SERVER_STATUS" 2>/dev/null || echo "auto")
    
    GAME_SERVER_IP=$(ask_value "Game server IP" "$existing_game_ip")
    GAME_SERVER_PORT=$(ask_value "Game server port" "$existing_game_port")
    LOGIN_SERVER_PORT=$(ask_value "Login server port" "$existing_login_port")
    SERVER_STATUS_TIMEOUT=$(ask_value "Check timeout (seconds)" "$existing_timeout")
    FORCE_GAME_SERVER_STATUS=$(ask_value "Force server status (auto/on/off)" "$existing_force_game")
    FORCE_LOGIN_SERVER_STATUS=$(ask_value "Force login status (auto/on/off)" "$existing_force_login")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "GAME_SERVER_IP" "$GAME_SERVER_IP"
        update_var "GAME_SERVER_PORT" "$GAME_SERVER_PORT"
        update_var "LOGIN_SERVER_PORT" "$LOGIN_SERVER_PORT"
        update_var "SERVER_STATUS_TIMEOUT" "$SERVER_STATUS_TIMEOUT"
        update_var "FORCE_GAME_SERVER_STATUS" "$FORCE_GAME_SERVER_STATUS"
        update_var "FORCE_LOGIN_SERVER_STATUS" "$FORCE_LOGIN_SERVER_STATUS"
    else
        add_var "GAME_SERVER_IP" "$GAME_SERVER_IP"
        add_var "GAME_SERVER_PORT" "$GAME_SERVER_PORT"
        add_var "LOGIN_SERVER_PORT" "$LOGIN_SERVER_PORT"
        add_var "SERVER_STATUS_TIMEOUT" "$SERVER_STATUS_TIMEOUT"
        add_var "FORCE_GAME_SERVER_STATUS" "$FORCE_GAME_SERVER_STATUS"
        add_var "FORCE_LOGIN_SERVER_STATUS" "$FORCE_LOGIN_SERVER_STATUS"
    fi
}

# Function to generate Fake Players configuration
generate_fake_players_config() {
    local edit_mode="${1:-false}"
    if [ "$edit_mode" = "false" ]; then
        add_section "FAKE PLAYERS CONFIGURATION"
    fi
    
    local existing_factor=$(get_existing_value "FAKE_PLAYERS_FACTOR" 2>/dev/null || echo "1.0")
    local existing_min=$(get_existing_value "FAKE_PLAYERS_MIN" 2>/dev/null || echo "0")
    local existing_max=$(get_existing_value "FAKE_PLAYERS_MAX" 2>/dev/null || echo "0")
    
    FAKE_PLAYERS_FACTOR=$(ask_value "Player multiplier (e.g.: 1.2 = +20%)" "$existing_factor")
    FAKE_PLAYERS_MIN=$(ask_value "Minimum player value (0 to ignore)" "$existing_min")
    FAKE_PLAYERS_MAX=$(ask_value "Maximum player value (0 to ignore)" "$existing_max")
    
    if [ "$edit_mode" = "true" ]; then
        update_var "FAKE_PLAYERS_FACTOR" "$FAKE_PLAYERS_FACTOR"
        update_var "FAKE_PLAYERS_MIN" "$FAKE_PLAYERS_MIN"
        update_var "FAKE_PLAYERS_MAX" "$FAKE_PLAYERS_MAX"
    else
        add_var "FAKE_PLAYERS_FACTOR" "$FAKE_PLAYERS_FACTOR"
        add_var "FAKE_PLAYERS_MIN" "$FAKE_PLAYERS_MIN"
        add_var "FAKE_PLAYERS_MAX" "$FAKE_PLAYERS_MAX"
    fi
}

# Function to generate VAPID configuration (Web Push)
generate_vapid_config() {
    add_section "VAPID CONFIGURATION (WEB PUSH)"
    
    if ask_yes_no "Configure VAPID for Web Push?" "n"; then
        log_info "Generating VAPID keys..."
        # Note: In production, you should generate real VAPID keys
        VAPID_PRIVATE_KEY=$(ask_value "VAPID Private Key" "7FDbpSlMB1UrNLWWgtTg5QGs9wC3-d1I6z7PdgplWP4")
        VAPID_PUBLIC_KEY=$(ask_value "VAPID Public Key" "BBQIgwfHEkr1LOgtUFwxm_bbb-h6tRMjxa7GCpVYKBsLdBQ-dkKPmkTidKKedNyWfaPgqQl1tV36yo7AyAhQ0J8")
        add_var "VAPID_PRIVATE_KEY" "$VAPID_PRIVATE_KEY"
        add_var "VAPID_PUBLIC_KEY" "$VAPID_PUBLIC_KEY"
    else
        add_var "VAPID_PRIVATE_KEY" "7FDbpSlMB1UrNLWWgtTg5QGs9wC3-d1I6z7PdgplWP4"
        add_var "VAPID_PUBLIC_KEY" "BBQIgwfHEkr1LOgtUFwxm_bbb-h6tRMjxa7GCpVYKBsLdBQ-dkKPmkTidKKedNyWfaPgqQl1tV36yo7AyAhQ0J8"
    fi
}

# Main function
main() {
    clear
    
    echo "========================================================="
    echo "  ⚙️  Gerador de Arquivo .env - PDL"
    echo "========================================================="
    echo
    
    # Check if we are in the correct directory
    if [ ! -f "${PROJECT_DIR}/manage.py" ] && [ ! -f "${PROJECT_DIR}/../manage.py" ]; then
        log_error "Unable to find Django project directory."
        log_info "Run this script from the project root or from within the 'lineage' directory."
        exit 1
    fi
    
    # Adjust PROJECT_DIR if necessary
    if [ ! -f "${PROJECT_DIR}/manage.py" ] && [ -f "${PROJECT_DIR}/../manage.py" ]; then
        PROJECT_DIR="${PROJECT_DIR}/.."
        ENV_FILE="${PROJECT_DIR}/.env"
    fi
    
    # Check if .env already exists
    local edit_mode=false
    if [ -f "$ENV_FILE" ]; then
        log_warning ".env file already exists: $ENV_FILE"
        echo
        echo "Choose an option:"
        echo "  1) Edit existing file (preserves current values)"
        echo "  2) Overwrite completely (creates new file)"
        echo "  3) Cancel"
        echo
        read -p "Option (1/2/3): " OPCAO
        
        case "$OPCAO" in
            1)
                edit_mode=true
                log_info "Backing up existing .env..."
                cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
                log_success "Edit mode activated. Existing values will be preserved as default."
                ;;
            2)
                edit_mode=false
                log_info "Backing up existing .env..."
                cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
                # Create empty .env file
                > "$ENV_FILE"
                ;;
            3)
                log_info "Operation cancelled."
                exit 0
                ;;
            *)
                log_error "Invalid option."
                exit 1
                ;;
        esac
    else
        # Criar arquivo .env vazio
        > "$ENV_FILE"
    fi
    
    log_info "Generating required variables..."
    generate_required "$edit_mode"
    
    echo
    log_info "Now let's configure the optional categories:"
    echo
    
    # Email
    if ask_yes_no "Include Email configuration?" "n"; then
        generate_email_config "$edit_mode"
    fi
    
    # Lineage DB
    if ask_yes_no "Include Lineage Database configuration?" "n"; then
        generate_lineage_db_config "$edit_mode"
    fi
    
    # AWS S3
    if ask_yes_no "Include AWS S3 configuration?" "n"; then
        generate_s3_config "$edit_mode"
    fi
    
    # Pagamentos
    if ask_yes_no "Include Payment configuration (Mercado Pago/Stripe)?" "n"; then
        generate_payments_config "$edit_mode"
    fi
    
    # Social Login
    if ask_yes_no "Include Social Login configuration?" "n"; then
        generate_social_login_config "$edit_mode"
    fi
    
    # Server Status
    if ask_yes_no "Include Server Status configuration?" "n"; then
        generate_server_status_config "$edit_mode"
    fi
    
    # Fake Players
    if ask_yes_no "Include Fake Players configuration?" "n"; then
        generate_fake_players_config "$edit_mode"
    fi
    
    # VAPID
    if ask_yes_no "Include VAPID configuration (Web Push)?" "n"; then
        generate_vapid_config "$edit_mode"
    fi
    
    echo
    if [ "$edit_mode" = "true" ]; then
        log_success ".env file updated successfully!"
    else
        log_success ".env file generated successfully!"
    fi
    log_info "Location: $ENV_FILE"
    echo
    log_warning "IMPORTANT: Review the .env file and adjust values as needed!"
    echo
}

# Execute main function
main "$@"

