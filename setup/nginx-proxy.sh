#!/bin/bash

################################################################################
# Script de Configuração do Nginx Proxy Reverso para PDL
# 
# Este script configura o Nginx como proxy reverso para o PDL,
# permitindo acesso via domínio personalizado com suporte a SSL.
################################################################################

set -euo pipefail

# Cores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
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

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    log_error "Por favor, execute este script como root (sudo)"
    exit 1
fi

# Função para validar domínio
validate_domain() {
    local domain="$1"
    # Validação básica de domínio
    if [[ ! "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$ ]]; then
        return 1
    fi
    return 0
}

# Função para garantir que a linha de include esteja presente no nginx.conf
configure_nginx_conf() {
    local NGINX_CONF="/etc/nginx/nginx.conf"
    local INCLUDE_LINE="    include /etc/nginx/sites-enabled/*;"

    # Cria backup se não existir
    if [ ! -f "${NGINX_CONF}.bak" ]; then
        cp "$NGINX_CONF" "${NGINX_CONF}.bak"
        log_info "Backup do nginx.conf criado."
    fi

    if ! grep -qF "$INCLUDE_LINE" "$NGINX_CONF"; then
        # Insere o include dentro do bloco http
        sed -i "/http {/{
            :a
            n
            /}/!ba
            i\\
$INCLUDE_LINE
        }" "$NGINX_CONF"
        log_success "Linha para incluir sites-enabled adicionada no nginx.conf"
    else
        log_info "Linha para incluir sites-enabled já presente no nginx.conf"
    fi
}

# Solicitar domínio do usuário
echo "========================================================="
echo "  🔧 Configuração do Nginx Proxy Reverso para PDL"
echo "========================================================="
echo

DOMAIN=""
while [ -z "$DOMAIN" ]; do
    read -p "Digite o domínio (ex: pdl.exemplo.com): " DOMAIN
    DOMAIN=$(echo "$DOMAIN" | tr '[:upper:]' '[:lower:]' | xargs)
    
    if [ -z "$DOMAIN" ]; then
        log_error "Domínio não pode estar vazio."
        continue
    fi
    
    if ! validate_domain "$DOMAIN"; then
        log_error "Domínio inválido. Por favor, digite um domínio válido."
        DOMAIN=""
        continue
    fi
done

log_success "Domínio configurado: $DOMAIN"

# Perguntar sobre SSL
echo
read -p "Deseja configurar SSL com Let's Encrypt? (s/n): " SETUP_SSL
SETUP_SSL=$(echo "$SETUP_SSL" | tr '[:upper:]' '[:lower:]')

# Instala o Nginx se não estiver instalado
if ! command -v nginx &> /dev/null; then
    log_info "Instalando Nginx..."
    apt-get update -qq
    apt-get install -y nginx
    log_success "Nginx instalado."
else
    log_info "Nginx já está instalado."
fi

# Garante que os diretórios existam
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Configura o nginx.conf para incluir sites-enabled
configure_nginx_conf

# Instala o Certbot e plugin Nginx para SSL se necessário
if [[ "$SETUP_SSL" =~ ^[sS]$ ]]; then
    NEED_INSTALL=false
    
    # Verifica se certbot está instalado
    if ! command -v certbot &> /dev/null; then
        NEED_INSTALL=true
        log_info "Certbot não encontrado. Será instalado."
    fi
    
    # Verifica se o plugin nginx do certbot está instalado
    if ! dpkg -l | grep -q "^ii.*python3-certbot-nginx"; then
        NEED_INSTALL=true
        log_info "Plugin Nginx do Certbot não encontrado. Será instalado."
    fi
    
    if [ "$NEED_INSTALL" = true ]; then
        log_info "Instalando Certbot e plugin Nginx..."
        apt-get update -qq
        apt-get install -y certbot python3-certbot-nginx
        log_success "Certbot e plugin Nginx instalados."
    else
        log_info "Certbot e plugin Nginx já estão instalados."
    fi
fi

# Cria a configuração do Nginx para proxy reverso
log_info "Criando configuração do Nginx..."

if [[ "$SETUP_SSL" =~ ^[sS]$ ]]; then
    # Configuração inicial apenas HTTP (SSL será adicionado pelo Certbot)
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
    # Configuração sem SSL (apenas HTTP)
    cat > /etc/nginx/sites-available/lineage-proxy << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Limite o tamanho de upload para 50 MB
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

# Cria link simbólico para habilitar o site
ln -sf /etc/nginx/sites-available/lineage-proxy /etc/nginx/sites-enabled/lineage-proxy
log_success "Configuração do site habilitada."

# Remove a configuração padrão do Nginx, se existir
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
    log_info "Configuração padrão removida."
fi

# Testa a configuração do Nginx
log_info "Testando configuração do Nginx..."
if nginx -t; then
    log_success "Configuração do Nginx está válida."
else
    log_error "Configuração do Nginx inválida. Abortando."
    exit 1
fi

# Reinicia o Nginx
log_info "Reiniciando Nginx..."
systemctl restart nginx
log_success "Nginx reiniciado."

# Configurar SSL se solicitado
if [[ "$SETUP_SSL" =~ ^[sS]$ ]]; then
    echo
    log_info "Configurando SSL com Let's Encrypt..."
    log_warning "Certifique-se de que o domínio ${DOMAIN} aponta para este servidor."
    read -p "Pressione Enter para continuar com a configuração SSL..."
    
    if certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --register-unsafely-without-email; then
        log_success "SSL configurado com sucesso!"
        systemctl reload nginx
    else
        log_warning "Falha ao configurar SSL automaticamente."
        log_info "Você pode configurar manualmente executando:"
        echo "  sudo certbot --nginx -d ${DOMAIN}"
    fi
fi

echo
log_success "Configuração do Nginx concluída!"
echo
log_info "Resumo da configuração:"
echo "  - Domínio: ${DOMAIN}"
echo "  - Proxy: http://localhost:6085"
if [[ "$SETUP_SSL" =~ ^[sS]$ ]]; then
    echo "  - SSL: Configurado (se bem-sucedido)"
    echo "  - Acesso: https://${DOMAIN}"
else
    echo "  - SSL: Não configurado"
    echo "  - Acesso: http://${DOMAIN}"
    echo
    log_info "Para configurar SSL posteriormente, execute:"
    echo "  sudo certbot --nginx -d ${DOMAIN}"
fi
echo
