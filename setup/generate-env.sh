#!/bin/bash

################################################################################
# Script de Geração do Arquivo .env - Painel Definitivo Lineage (PDL)
# 
# Este script gera o arquivo .env de forma interativa, permitindo escolher
# quais categorias opcionais incluir.
#
# Uso:
#   bash setup/generate-env.sh
################################################################################

set -euo pipefail

# Cores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Função para log
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

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Se estamos dentro de um diretório lineage, ajustar
if [ -d "${PROJECT_DIR}/lineage" ] && [ -f "${PROJECT_DIR}/lineage/manage.py" ]; then
    PROJECT_DIR="${PROJECT_DIR}/lineage"
fi

ENV_FILE="${PROJECT_DIR}/.env"

# Função para gerar chave Fernet
generate_fernet_key() {
    python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
}

# Função para gerar SECRET_KEY
generate_secret_key() {
    python3 - <<EOF
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
}

# Função para perguntar sim/não
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

# Função para perguntar valor
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

# Função para adicionar seção ao .env
add_section() {
    local section_name="$1"
    echo "" >> "$ENV_FILE"
    echo "# =========================== $section_name ===========================" >> "$ENV_FILE"
}

# Função para adicionar variável ao .env
add_var() {
    local key="$1"
    local value="$2"
    echo "${key}=${value}" >> "$ENV_FILE"
}

# Função para gerar variáveis obrigatórias
generate_required() {
    log_info "Gerando variáveis obrigatórias..."
    
    add_section "REQUIRED CONFIGURATION"
    
    # DEBUG
    if ask_yes_no "Habilitar modo DEBUG?" "n"; then
        add_var "DEBUG" "True"
    else
        add_var "DEBUG" "False"
    fi
    
    # SECRET_KEY
    log_info "Gerando SECRET_KEY..."
    SECRET_KEY=$(generate_secret_key 2>/dev/null || echo "41&l85x\$t8g5!wgvzxw9_v%jbph2msibr3x7jww5%1u8w*3ax")
    add_var "SECRET_KEY" "$SECRET_KEY"
    
    # Database
    add_section "DATABASE CONFIGURATION"
    DB_ENGINE=$(ask_value "Tipo de banco de dados (postgresql/mysql/sqlite3)" "postgresql")
    add_var "DB_ENGINE" "$DB_ENGINE"
    
    if [ "$DB_ENGINE" != "sqlite3" ]; then
        DB_HOST=$(ask_value "Host do banco de dados" "postgres")
        DB_NAME=$(ask_value "Nome do banco de dados" "db_name")
        DB_USERNAME=$(ask_value "Usuário do banco de dados" "db_user")
        DB_PASS=$(ask_value "Senha do banco de dados" "db_pass")
        DB_PORT=$(ask_value "Porta do banco de dados" "5432")
        
        add_var "DB_HOST" "$DB_HOST"
        add_var "DB_NAME" "$DB_NAME"
        add_var "DB_USERNAME" "$DB_USERNAME"
        add_var "DB_PASS" "$DB_PASS"
        add_var "DB_PORT" "$DB_PORT"
    fi
    
    # Redis e Cache
    add_section "REDIS AND CACHE"
    add_var "DJANGO_CACHE_REDIS_URI" "redis://redis:6379/0"
    add_var "CELERY_BROKER_URI" "redis://redis:6379/1"
    add_var "CELERY_BACKEND_URI" "redis://redis:6379/1"
    add_var "CHANNELS_BACKEND" "redis://redis:6379/2"
    
    # Auditor
    if ask_yes_no "Habilitar auditor middleware?" "y"; then
        add_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "True"
    else
        add_var "CONFIG_AUDITOR_MIDDLEWARE_ENABLE" "False"
    fi
    
    # Hostname
    add_section "HOSTNAME CONFIGURATION"
    RENDER_EXTERNAL_HOSTNAME=$(ask_value "Hostname externo" "pdl.denky.dev.br")
    RENDER_EXTERNAL_FRONTEND=$(ask_value "Frontend externo" "$RENDER_EXTERNAL_HOSTNAME")
    add_var "RENDER_EXTERNAL_HOSTNAME" "$RENDER_EXTERNAL_HOSTNAME"
    add_var "RENDER_EXTERNAL_FRONTEND" "$RENDER_EXTERNAL_FRONTEND"
    
    # Encryption
    log_info "Gerando ENCRYPTION_KEY..."
    ENCRYPTION_KEY=$(generate_fernet_key 2>/dev/null || echo "iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac=")
    add_var "ENCRYPTION_KEY" "'$ENCRYPTION_KEY'"
    add_var "DATA_UPLOAD_MAX_MEMORY_SIZE" "31457280"
    
    # hCaptcha
    add_section "HCAPTCHA CONFIGURATION"
    CONFIG_HCAPTCHA_SITE_KEY=$(ask_value "hCaptcha Site Key" "bcf40348-fa88-4570-a752-2asdasde0b2bc")
    CONFIG_HCAPTCHA_SECRET_KEY=$(ask_value "hCaptcha Secret Key" "ES_dc688fdasdasdadasdas4e918093asddsddsafa3f1b")
    add_var "CONFIG_HCAPTCHA_SITE_KEY" "$CONFIG_HCAPTCHA_SITE_KEY"
    add_var "CONFIG_HCAPTCHA_SECRET_KEY" "$CONFIG_HCAPTCHA_SECRET_KEY"
    add_var "CONFIG_LOGIN_MAX_ATTEMPTS" "3"
    add_var "CONFIG_HCAPTCHA_FAIL_OPEN" "False"
    
    # Lineage Query Module
    add_section "LINEAGE QUERY MODULE"
    LINEAGE_QUERY_MODULE=$(ask_value "Módulo de query do Lineage" "dreamv3")
    add_var "LINEAGE_QUERY_MODULE" "$LINEAGE_QUERY_MODULE"
    
    # Localization
    add_section "LOCALIZATION"
    CONFIG_LANGUAGE_CODE=$(ask_value "Código do idioma (pt/en/es)" "pt")
    CONFIG_TIME_ZONE=$(ask_value "Fuso horário" "America/Recife")
    CONFIG_DECIMAL_SEPARATOR=$(ask_value "Separador decimal" ",")
    CONFIG_USE_THOUSAND_SEPARATOR=$(ask_value "Usar separador de milhar? (True/False)" "True")
    CONFIG_DATETIME_FORMAT=$(ask_value "Formato de data/hora" "d/m/Y H:i:s")
    CONFIG_DATE_FORMAT=$(ask_value "Formato de data" "d/m/Y")
    CONFIG_TIME_FORMAT=$(ask_value "Formato de hora" "H:i:s")
    CONFIG_GMT_OFFSET=$(ask_value "Offset GMT" "-3")
    
    add_var "CONFIG_LANGUAGE_CODE" "\"$CONFIG_LANGUAGE_CODE\""
    add_var "CONFIG_TIME_ZONE" "\"$CONFIG_TIME_ZONE\""
    add_var "CONFIG_DECIMAL_SEPARATOR" "'$CONFIG_DECIMAL_SEPARATOR'"
    add_var "CONFIG_USE_THOUSAND_SEPARATOR" "$CONFIG_USE_THOUSAND_SEPARATOR"
    add_var "CONFIG_DATETIME_FORMAT" "'$CONFIG_DATETIME_FORMAT'"
    add_var "CONFIG_DATE_FORMAT" "'$CONFIG_DATE_FORMAT'"
    add_var "CONFIG_TIME_FORMAT" "'$CONFIG_TIME_FORMAT'"
    add_var "CONFIG_GMT_OFFSET" "$CONFIG_GMT_OFFSET"
    
    # Project Info
    add_section "PROJECT INFORMATION"
    PROJECT_TITLE=$(ask_value "Título do projeto" "Lineage 2 PDL")
    PROJECT_AUTHOR=$(ask_value "Autor do projeto" "Lineage 2 PDL")
    PROJECT_DESCRIPTION=$(ask_value "Descrição do projeto" "O PDL é um painel que nasceu com a missão de oferecer ferramentas poderosas para administradores de servidores privados de Lineage 2.")
    PROJECT_KEYWORDS=$(ask_value "Palavras-chave" "lineage l2 painel servidor")
    PROJECT_URL=$(ask_value "URL do projeto" "https://pdl.denky.dev.br")
    PROJECT_LOGO_URL=$(ask_value "URL do logo" "/static/assets/img/logo_painel.png")
    PROJECT_FAVICON_ICO=$(ask_value "URL do favicon .ico" "/static/assets/img/ico.jpg")
    PROJECT_FAVICON_MANIFEST=$(ask_value "URL do manifest" "/static/assets/img/favicon/site.webmanifest")
    PROJECT_THEME_COLOR=$(ask_value "Cor do tema" "#ffffff")
    
    add_var "PROJECT_TITLE" "$PROJECT_TITLE"
    add_var "PROJECT_AUTHOR" "$PROJECT_AUTHOR"
    add_var "PROJECT_DESCRIPTION" "$PROJECT_DESCRIPTION"
    add_var "PROJECT_KEYWORDS" "$PROJECT_KEYWORDS"
    add_var "PROJECT_URL" "$PROJECT_URL"
    add_var "PROJECT_LOGO_URL" "$PROJECT_LOGO_URL"
    add_var "PROJECT_FAVICON_ICO" "$PROJECT_FAVICON_ICO"
    add_var "PROJECT_FAVICON_MANIFEST" "$PROJECT_FAVICON_MANIFEST"
    add_var "PROJECT_THEME_COLOR" "$PROJECT_THEME_COLOR"
    
    # Social Media Links
    add_section "SOCIAL MEDIA LINKS"
    PROJECT_DISCORD_URL=$(ask_value "URL do Discord" "https://discord.gg/seu-link-aqui")
    PROJECT_YOUTUBE_URL=$(ask_value "URL do YouTube" "https://www.youtube.com/@seu-canal")
    PROJECT_FACEBOOK_URL=$(ask_value "URL do Facebook" "https://www.facebook.com/sua-pagina")
    PROJECT_INSTAGRAM_URL=$(ask_value "URL do Instagram" "https://www.instagram.com/seu-perfil")
    
    add_var "PROJECT_DISCORD_URL" "'$PROJECT_DISCORD_URL'"
    add_var "PROJECT_YOUTUBE_URL" "'$PROJECT_YOUTUBE_URL'"
    add_var "PROJECT_FACEBOOK_URL" "'$PROJECT_FACEBOOK_URL'"
    add_var "PROJECT_INSTAGRAM_URL" "'$PROJECT_INSTAGRAM_URL'"
    
    # Basic Flags
    add_section "BASIC FLAGS"
    add_var "RUNNING_IN_DOCKER" "True"
    add_var "SLOGAN" "True"
    add_var "LINEAGE_DB_ENABLED" "False"
    add_var "SHOW_THEME_ERRORS_TO_USERS" "True"
}

# Função para gerar configuração de Email
generate_email_config() {
    add_section "EMAIL CONFIGURATION"
    
    if ask_yes_no "Habilitar envio de emails?" "n"; then
        add_var "CONFIG_EMAIL_ENABLE" "True"
        CONFIG_EMAIL_USE_TLS=$(ask_yes_no "Usar TLS?" "y" && echo "True" || echo "False")
        CONFIG_EMAIL_HOST=$(ask_value "Servidor SMTP" "smtp.domain.com")
        CONFIG_EMAIL_PORT=$(ask_value "Porta SMTP" "587")
        CONFIG_EMAIL_HOST_USER=$(ask_value "Usuário do email" "mail@mail.dev.br")
        CONFIG_EMAIL_HOST_PASSWORD=$(ask_value "Senha do email" "password")
        CONFIG_DEFAULT_FROM_EMAIL=$(ask_value "Email remetente padrão" "$CONFIG_EMAIL_HOST_USER")
        
        add_var "CONFIG_EMAIL_USE_TLS" "$CONFIG_EMAIL_USE_TLS"
        add_var "CONFIG_EMAIL_HOST" "$CONFIG_EMAIL_HOST"
        add_var "CONFIG_EMAIL_PORT" "$CONFIG_EMAIL_PORT"
        add_var "CONFIG_EMAIL_HOST_USER" "$CONFIG_EMAIL_HOST_USER"
        add_var "CONFIG_EMAIL_HOST_PASSWORD" "$CONFIG_EMAIL_HOST_PASSWORD"
        add_var "CONFIG_DEFAULT_FROM_EMAIL" "$CONFIG_DEFAULT_FROM_EMAIL"
    else
        add_var "CONFIG_EMAIL_ENABLE" "False"
        add_var "CONFIG_EMAIL_USE_TLS" "True"
        add_var "CONFIG_EMAIL_HOST" "smtp.domain.com"
        add_var "CONFIG_EMAIL_PORT" "587"
        add_var "CONFIG_EMAIL_HOST_USER" "mail@mail.dev.br"
        add_var "CONFIG_EMAIL_HOST_PASSWORD" "password"
        add_var "CONFIG_DEFAULT_FROM_EMAIL" "mail@mail.dev.br"
    fi
}

# Função para gerar configuração do Lineage DB
generate_lineage_db_config() {
    add_section "LINEAGE DATABASE CONFIGURATION"
    
    LINEAGE_DB_NAME=$(ask_value "Nome do banco Lineage" "l2jdb")
    LINEAGE_DB_USER=$(ask_value "Usuário do banco Lineage" "l2user")
    LINEAGE_DB_PASSWORD=$(ask_value "Senha do banco Lineage" "suaSenhaAqui")
    LINEAGE_DB_HOST=$(ask_value "Host do banco Lineage" "192.168.1.100")
    LINEAGE_DB_PORT=$(ask_value "Porta do banco Lineage" "3306")
    
    add_var "LINEAGE_DB_NAME" "$LINEAGE_DB_NAME"
    add_var "LINEAGE_DB_USER" "$LINEAGE_DB_USER"
    add_var "LINEAGE_DB_PASSWORD" "$LINEAGE_DB_PASSWORD"
    add_var "LINEAGE_DB_HOST" "$LINEAGE_DB_HOST"
    add_var "LINEAGE_DB_PORT" "$LINEAGE_DB_PORT"
}

# Função para gerar configuração do AWS S3
generate_s3_config() {
    add_section "AWS S3 CONFIGURATION"
    
    if ask_yes_no "Usar AWS S3 para armazenamento?" "n"; then
        add_var "USE_S3" "True"
        AWS_ACCESS_KEY_ID=$(ask_value "AWS Access Key ID" "your_aws_access_key_id")
        AWS_SECRET_ACCESS_KEY=$(ask_value "AWS Secret Access Key" "your_aws_secret_access_key")
        AWS_STORAGE_BUCKET_NAME=$(ask_value "Nome do bucket S3" "your-bucket-name")
        AWS_S3_REGION_NAME=$(ask_value "Região do S3" "us-east-1")
        AWS_S3_CUSTOM_DOMAIN=$(ask_value "Domínio customizado do S3" "${AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com")
        
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

# Função para gerar configuração de Pagamentos
generate_payments_config() {
    add_section "PAYMENT CONFIGURATION"
    
    # Mercado Pago
    echo
    log_info "Configuração do Mercado Pago:"
    if ask_yes_no "Habilitar pagamentos via Mercado Pago?" "n"; then
        add_var "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" "True"
        CONFIG_MERCADO_PAGO_ACCESS_TOKEN=$(ask_value "Mercado Pago Access Token" "APP_USR-0000000000000000-000000-00000000000000000000000000000000-000000000")
        CONFIG_MERCADO_PAGO_PUBLIC_KEY=$(ask_value "Mercado Pago Public Key" "APP_USR-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        CONFIG_MERCADO_PAGO_CLIENT_ID=$(ask_value "Mercado Pago Client ID" "0000000000000000")
        CONFIG_MERCADO_PAGO_CLIENT_SECRET=$(ask_value "Mercado Pago Client Secret" "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        CONFIG_MERCADO_PAGO_SIGNATURE=$(ask_value "Mercado Pago Signature" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        
        add_var "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" "\"$CONFIG_MERCADO_PAGO_ACCESS_TOKEN\""
        add_var "CONFIG_MERCADO_PAGO_PUBLIC_KEY" "\"$CONFIG_MERCADO_PAGO_PUBLIC_KEY\""
        add_var "CONFIG_MERCADO_PAGO_CLIENT_ID" "\"$CONFIG_MERCADO_PAGO_CLIENT_ID\""
        add_var "CONFIG_MERCADO_PAGO_CLIENT_SECRET" "\"$CONFIG_MERCADO_PAGO_CLIENT_SECRET\""
        add_var "CONFIG_MERCADO_PAGO_SIGNATURE" "\"$CONFIG_MERCADO_PAGO_SIGNATURE\""
    else
        add_var "CONFIG_MERCADO_PAGO_ACTIVATE_PAYMENTS" "False"
        add_var "CONFIG_MERCADO_PAGO_ACCESS_TOKEN" "\"APP_USR-0000000000000000-000000-00000000000000000000000000000000-000000000\""
        add_var "CONFIG_MERCADO_PAGO_PUBLIC_KEY" "\"APP_USR-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\""
        add_var "CONFIG_MERCADO_PAGO_CLIENT_ID" "\"0000000000000000\""
        add_var "CONFIG_MERCADO_PAGO_CLIENT_SECRET" "\"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\""
        add_var "CONFIG_MERCADO_PAGO_SIGNATURE" "\"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\""
    fi
    
    # Stripe
    echo
    log_info "Configuração do Stripe:"
    if ask_yes_no "Habilitar pagamentos via Stripe?" "n"; then
        add_var "CONFIG_STRIPE_ACTIVATE_PAYMENTS" "True"
        CONFIG_STRIPE_SECRET_KEY=$(ask_value "Stripe Secret Key" "sk_test_51RK0cORmyaPSbmPDEMjN0DaasdasdadadasdafgagdhhfasdfsfnbgRrtdKRwHRakfrQub9SQ5jQEUNvTfrcFxbw00gsqFR09W")
        CONFIG_STRIPE_WEBHOOK_SECRET=$(ask_value "Stripe Webhook Secret" "whsec_5dzjceF7LgeYzasdasdasdZpSuPq")
        
        add_var "CONFIG_STRIPE_SECRET_KEY" "'$CONFIG_STRIPE_SECRET_KEY'"
        add_var "CONFIG_STRIPE_WEBHOOK_SECRET" "'$CONFIG_STRIPE_WEBHOOK_SECRET'"
    else
        add_var "CONFIG_STRIPE_ACTIVATE_PAYMENTS" "False"
        add_var "CONFIG_STRIPE_SECRET_KEY" "'sk_test_51RK0cORmyaPSbmPDEMjN0DaasdasdadadasdafgagdhhfasdfsfnbgRrtdKRwHRakfrQub9SQ5jQEUNvTfrcFxbw00gsqFR09W'"
        add_var "CONFIG_STRIPE_WEBHOOK_SECRET" "'whsec_5dzjceF7LgeYzasdasdasdZpSuPq'"
    fi
}

# Função para gerar configuração de Social Login
generate_social_login_config() {
    add_section "SOCIAL LOGIN CONFIGURATION"
    
    if ask_yes_no "Habilitar login social?" "n"; then
        add_var "SOCIAL_LOGIN_ENABLED" "True"
        
        # Google
        if ask_yes_no "Habilitar login com Google?" "n"; then
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
        if ask_yes_no "Habilitar login com GitHub?" "n"; then
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
        if ask_yes_no "Habilitar login com Discord?" "n"; then
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
        
        if ask_yes_no "Mostrar seção de login social na interface?" "n"; then
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

# Função para gerar configuração de Server Status
generate_server_status_config() {
    add_section "SERVER STATUS CONFIGURATION"
    
    GAME_SERVER_IP=$(ask_value "IP do servidor de jogo" "192.168.1.100")
    GAME_SERVER_PORT=$(ask_value "Porta do servidor de jogo" "7777")
    LOGIN_SERVER_PORT=$(ask_value "Porta do servidor de login" "2106")
    SERVER_STATUS_TIMEOUT=$(ask_value "Timeout para verificação (segundos)" "1")
    FORCE_GAME_SERVER_STATUS=$(ask_value "Forçar status do servidor (auto/on/off)" "auto")
    FORCE_LOGIN_SERVER_STATUS=$(ask_value "Forçar status do login (auto/on/off)" "auto")
    
    add_var "GAME_SERVER_IP" "$GAME_SERVER_IP"
    add_var "GAME_SERVER_PORT" "$GAME_SERVER_PORT"
    add_var "LOGIN_SERVER_PORT" "$LOGIN_SERVER_PORT"
    add_var "SERVER_STATUS_TIMEOUT" "$SERVER_STATUS_TIMEOUT"
    add_var "FORCE_GAME_SERVER_STATUS" "$FORCE_GAME_SERVER_STATUS"
    add_var "FORCE_LOGIN_SERVER_STATUS" "$FORCE_LOGIN_SERVER_STATUS"
}

# Função para gerar configuração de Fake Players
generate_fake_players_config() {
    add_section "FAKE PLAYERS CONFIGURATION"
    
    FAKE_PLAYERS_FACTOR=$(ask_value "Multiplicador de jogadores (ex: 1.2 = +20%)" "1.0")
    FAKE_PLAYERS_MIN=$(ask_value "Valor mínimo de jogadores (0 para ignorar)" "0")
    FAKE_PLAYERS_MAX=$(ask_value "Valor máximo de jogadores (0 para ignorar)" "0")
    
    add_var "FAKE_PLAYERS_FACTOR" "$FAKE_PLAYERS_FACTOR"
    add_var "FAKE_PLAYERS_MIN" "$FAKE_PLAYERS_MIN"
    add_var "FAKE_PLAYERS_MAX" "$FAKE_PLAYERS_MAX"
}

# Função para gerar configuração de VAPID (Web Push)
generate_vapid_config() {
    add_section "VAPID CONFIGURATION (WEB PUSH)"
    
    if ask_yes_no "Configurar VAPID para Web Push?" "n"; then
        log_info "Gerando chaves VAPID..."
        # Nota: Em produção, você deve gerar chaves VAPID reais
        VAPID_PRIVATE_KEY=$(ask_value "VAPID Private Key" "7FDbpSlMB1UrNLWWgtTg5QGs9wC3-d1I6z7PdgplWP4")
        VAPID_PUBLIC_KEY=$(ask_value "VAPID Public Key" "BBQIgwfHEkr1LOgtUFwxm_bbb-h6tRMjxa7GCpVYKBsLdBQ-dkKPmkTidKKedNyWfaPgqQl1tV36yo7AyAhQ0J8")
        add_var "VAPID_PRIVATE_KEY" "$VAPID_PRIVATE_KEY"
        add_var "VAPID_PUBLIC_KEY" "$VAPID_PUBLIC_KEY"
    else
        add_var "VAPID_PRIVATE_KEY" "7FDbpSlMB1UrNLWWgtTg5QGs9wC3-d1I6z7PdgplWP4"
        add_var "VAPID_PUBLIC_KEY" "BBQIgwfHEkr1LOgtUFwxm_bbb-h6tRMjxa7GCpVYKBsLdBQ-dkKPmkTidKKedNyWfaPgqQl1tV36yo7AyAhQ0J8"
    fi
}

# Função principal
main() {
    clear
    
    echo "========================================================="
    echo "  ⚙️  Gerador de Arquivo .env - PDL"
    echo "========================================================="
    echo
    
    # Verificar se estamos no diretório correto
    if [ ! -f "${PROJECT_DIR}/manage.py" ] && [ ! -f "${PROJECT_DIR}/../manage.py" ]; then
        log_error "Não foi possível encontrar o diretório do projeto Django."
        log_info "Execute este script da raiz do projeto ou de dentro do diretório 'lineage'."
        exit 1
    fi
    
    # Ajustar PROJECT_DIR se necessário
    if [ ! -f "${PROJECT_DIR}/manage.py" ] && [ -f "${PROJECT_DIR}/../manage.py" ]; then
        PROJECT_DIR="${PROJECT_DIR}/.."
        ENV_FILE="${PROJECT_DIR}/.env"
    fi
    
    # Verificar se .env já existe
    if [ -f "$ENV_FILE" ]; then
        log_warning "Arquivo .env já existe: $ENV_FILE"
        if ! ask_yes_no "Deseja sobrescrever?" "n"; then
            log_info "Operação cancelada."
            exit 0
        fi
        log_info "Fazendo backup do .env existente..."
        cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Criar arquivo .env vazio
    > "$ENV_FILE"
    
    log_info "Gerando variáveis obrigatórias..."
    generate_required
    
    echo
    log_info "Agora vamos configurar as categorias opcionais:"
    echo
    
    # Email
    if ask_yes_no "Incluir configuração de Email?" "n"; then
        generate_email_config
    fi
    
    # Lineage DB
    if ask_yes_no "Incluir configuração do Banco de Dados Lineage?" "n"; then
        generate_lineage_db_config
    fi
    
    # AWS S3
    if ask_yes_no "Incluir configuração do AWS S3?" "n"; then
        generate_s3_config
    fi
    
    # Pagamentos
    if ask_yes_no "Incluir configuração de Pagamentos (Mercado Pago/Stripe)?" "n"; then
        generate_payments_config
    fi
    
    # Social Login
    if ask_yes_no "Incluir configuração de Login Social?" "n"; then
        generate_social_login_config
    fi
    
    # Server Status
    if ask_yes_no "Incluir configuração de Status do Servidor?" "n"; then
        generate_server_status_config
    fi
    
    # Fake Players
    if ask_yes_no "Incluir configuração de Jogadores Falsos?" "n"; then
        generate_fake_players_config
    fi
    
    # VAPID
    if ask_yes_no "Incluir configuração de VAPID (Web Push)?" "n"; then
        generate_vapid_config
    fi
    
    echo
    log_success "Arquivo .env gerado com sucesso!"
    log_info "Localização: $ENV_FILE"
    echo
    log_warning "IMPORTANTE: Revise o arquivo .env e ajuste os valores conforme necessário!"
    echo
}

# Executar função principal
main "$@"

