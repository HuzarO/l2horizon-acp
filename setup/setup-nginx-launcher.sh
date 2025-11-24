#!/bin/bash

################################################################################
# Script de Configuração do Nginx para Launcher (Index of)
# 
# Este script configura o Nginx para servir os arquivos do launcher
# com index of habilitado, permitindo listagem de diretórios.
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

# Solicitar informações
echo "========================================================="
echo "  🌐 Configuração do Nginx para Launcher (Index of)"
echo "========================================================="
echo

# Solicitar domínio
DOMAIN=""
while [ -z "$DOMAIN" ]; do
    read -p "Digite o domínio para o launcher (ex: launcher.exemplo.com): " DOMAIN
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

# Solicitar diretório FTP
echo
DEFAULT_FTP_DIR="/var/www/launcher"
FTP_DIR=""
while [ -z "$FTP_DIR" ]; do
    read -p "Digite o diretório dos arquivos do launcher (padrão: ${DEFAULT_FTP_DIR}): " FTP_DIR
    FTP_DIR=$(echo "$FTP_DIR" | xargs)
    
    if [ -z "$FTP_DIR" ]; then
        FTP_DIR="$DEFAULT_FTP_DIR"
    fi
    
    # Validar se o diretório existe
    if [ ! -d "$FTP_DIR" ]; then
        log_warning "Diretório não existe: $FTP_DIR"
        read -p "Deseja criar este diretório? (s/n): " CREATE_DIR
        if [[ "$CREATE_DIR" =~ ^[sS]$ ]]; then
            mkdir -p "$FTP_DIR"
            chmod 755 "$FTP_DIR"
            log_success "Diretório criado: $FTP_DIR"
        else
            log_error "Diretório não existe. Abortando."
            exit 1
        fi
    fi
    
    # Validar se é caminho absoluto
    if [[ ! "$FTP_DIR" =~ ^/ ]]; then
        log_error "O diretório deve ser um caminho absoluto (começando com /)"
        FTP_DIR=""
        continue
    fi
done

log_success "Diretório configurado: $FTP_DIR"

# Verificar se o Nginx está instalado
if ! command -v nginx &> /dev/null; then
    log_error "Nginx não está instalado."
    log_info "Execute primeiro: sudo bash setup/install-nginx.sh"
    exit 1
fi

log_info "Nginx está instalado."

# Garante que os diretórios existam
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Configura o nginx.conf para incluir sites-enabled
configure_nginx_conf

# Perguntar sobre SSL
echo
read -p "Deseja configurar SSL com Let's Encrypt? (s/n): " SETUP_SSL
SETUP_SSL=$(echo "$SETUP_SSL" | tr '[:upper:]' '[:lower:]')

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

# Criar a configuração do Nginx com index of
log_info "Criando configuração do Nginx..."

if [[ "$SETUP_SSL" =~ ^[sS]$ ]]; then
    # Configuração inicial apenas HTTP (SSL será adicionado pelo Certbot)
    cat > /etc/nginx/sites-available/launcher << EOF
# HTTP - Initial configuration (SSL will be added by Certbot)
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Root directory
    root ${FTP_DIR};
    index index.html index.htm;

    # Habilitar index of (listagem de diretórios)
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    autoindex_format html;

    # Limite o tamanho de upload para 100 MB (para arquivos grandes do launcher)
    client_max_body_size 100M;

    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Configuração principal com index of
    location / {
        try_files \$uri \$uri/ =404;
        
        # Headers de segurança
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # Desabilitar index of em subdiretórios específicos (opcional)
    # location /private/ {
    #     autoindex off;
    # }

    # Logs
    access_log /var/log/nginx/launcher_access.log;
    error_log /var/log/nginx/launcher_error.log;
}
EOF
else
    # Configuração sem SSL (apenas HTTP)
    cat > /etc/nginx/sites-available/launcher << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Root directory
    root ${FTP_DIR};
    index index.html index.htm;

    # Habilitar index of (listagem de diretórios)
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    autoindex_format html;

    # Limite o tamanho de upload para 100 MB (para arquivos grandes do launcher)
    client_max_body_size 100M;

    # Configuração principal com index of
    location / {
        try_files \$uri \$uri/ =404;
        
        # Headers de segurança
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # Desabilitar index of em subdiretórios específicos (opcional)
    # location /private/ {
    #     autoindex off;
    # }

    # Logs
    access_log /var/log/nginx/launcher_access.log;
    error_log /var/log/nginx/launcher_error.log;
}
EOF
fi

# Cria link simbólico para habilitar o site
ln -sf /etc/nginx/sites-available/launcher /etc/nginx/sites-enabled/launcher
log_success "Configuração do site habilitada."

# Testa a configuração do Nginx
log_info "Testando configuração do Nginx..."
if nginx -t; then
    log_success "✓ Configuração do Nginx está válida."
else
    log_error "✗ Configuração do Nginx inválida. Abortando."
    log_info "Verifique os erros acima e corrija a configuração."
    exit 1
fi

# Reinicia o Nginx
log_info "Reiniciando Nginx..."
if systemctl restart nginx; then
    log_success "✓ Nginx reiniciado com sucesso."
else
    log_error "✗ Falha ao reiniciar Nginx."
    exit 1
fi

# Verificar se o Nginx está rodando
if systemctl is-active --quiet nginx; then
    log_success "✓ Serviço Nginx está rodando."
else
    log_error "✗ Serviço Nginx não está rodando."
    log_info "Verifique os logs com: journalctl -u nginx -n 50"
    exit 1
fi

# Configurar SSL se solicitado
if [[ "$SETUP_SSL" =~ ^[sS]$ ]]; then
    echo
    log_info "Configurando SSL com Let's Encrypt..."
    log_warning "Certifique-se de que o domínio ${DOMAIN} aponta para este servidor."
    read -p "Pressione Enter para continuar com a configuração SSL..."
    
    if certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --register-unsafely-without-email; then
        log_success "SSL configurado com sucesso!"
        systemctl reload nginx
        
        # Verificar novamente após SSL
        if nginx -t; then
            log_success "✓ Configuração do Nginx validada após SSL."
        else
            log_error "✗ Erro na configuração após SSL."
            exit 1
        fi
    else
        log_warning "Falha ao configurar SSL automaticamente."
        log_info "Você pode configurar manualmente executando:"
        echo "  sudo certbot --nginx -d ${DOMAIN}"
    fi
fi

# Validação final
echo
log_info "Realizando validação final da configuração..."

# Verificar se o arquivo de configuração existe
if [ ! -f /etc/nginx/sites-available/launcher ]; then
    log_error "✗ Arquivo de configuração não encontrado."
    exit 1
fi
log_success "✓ Arquivo de configuração existe."

# Verificar se o link simbólico existe
if [ ! -L /etc/nginx/sites-enabled/launcher ]; then
    log_error "✗ Link simbólico não encontrado."
    exit 1
fi
log_success "✓ Link simbólico existe."

# Verificar se o diretório existe e tem permissões corretas
if [ ! -d "$FTP_DIR" ]; then
    log_error "✗ Diretório FTP não existe: $FTP_DIR"
    exit 1
fi
log_success "✓ Diretório FTP existe: $FTP_DIR"

# Verificar permissões do diretório
if [ ! -r "$FTP_DIR" ]; then
    log_warning "⚠ Diretório não tem permissão de leitura. Ajustando..."
    chmod 755 "$FTP_DIR"
fi
log_success "✓ Permissões do diretório verificadas."

# Testar configuração do Nginx novamente
if nginx -t 2>&1 | grep -q "test is successful"; then
    log_success "✓ Configuração do Nginx validada com sucesso."
else
    log_error "✗ Falha na validação final do Nginx."
    nginx -t
    exit 1
fi

# Verificar se o serviço está respondendo
if systemctl is-active --quiet nginx; then
    log_success "✓ Serviço Nginx está ativo e rodando."
else
    log_error "✗ Serviço Nginx não está ativo."
    exit 1
fi

echo
log_success "Configuração do Nginx para Launcher concluída!"
echo
log_info "Resumo da configuração:"
echo "  - Domínio: ${DOMAIN}"
echo "  - Diretório: ${FTP_DIR}"
echo "  - Index of: Habilitado"
echo "  - Upload máximo: 100MB"
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
log_info "Para testar:"
echo "  curl -I http://${DOMAIN}"
echo "  ou acesse no navegador: http://${DOMAIN}"
echo

