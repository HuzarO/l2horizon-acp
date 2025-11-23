#!/bin/bash

################################################################################
# Script de Instalação do Nginx - Painel Definitivo Lineage (PDL)
# 
# Este script instala e configura o Nginx do repositório oficial.
# Suporta instalação de versão stable ou mainline.
#
# Uso:
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

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
}

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    log_error "Por favor, execute este script como root (sudo)"
    exit 1
fi

# Função para detectar versão do Ubuntu
detect_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" = "ubuntu" ]; then
            echo "$VERSION_CODENAME"
        else
            log_warning "Sistema não é Ubuntu. Tentando continuar..."
            if command -v lsb_release &> /dev/null; then
                lsb_release -cs 2>/dev/null || echo "unknown"
            else
                echo "unknown"
            fi
        fi
    else
        log_warning "Não foi possível detectar a versão do sistema."
        echo "unknown"
    fi
}

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para verificar se Nginx está instalado
nginx_installed() {
    command_exists nginx && nginx -v &>/dev/null
}

# Função para obter versão atual do Nginx
get_nginx_version() {
    if nginx_installed; then
        nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+' || echo "unknown"
    else
        echo "not installed"
    fi
}

# Função para instalar dependências
install_dependencies() {
    log_info "Instalando dependências necessárias..."
    
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
    
    log_success "Dependências instaladas."
}

# Função para configurar repositório do Nginx
setup_nginx_repo() {
    local nginx_version="${1:-mainline}"
    local ubuntu_codename="$2"
    
    log_info "Configurando repositório do Nginx ($nginx_version)..."
    
    # Verificar se a chave já existe
    if [ ! -f /usr/share/keyrings/nginx-archive-keyring.gpg ]; then
        log_info "Importando chave GPG do Nginx..."
        curl -fsSL https://nginx.org/keys/nginx_signing.key | \
            gpg --dearmor -o /usr/share/keyrings/nginx-archive-keyring.gpg 2>/dev/null || {
            log_error "Falha ao importar chave GPG do Nginx."
            exit 1
        }
        log_success "Chave GPG importada."
    else
        log_debug "Chave GPG já existe."
    fi
    
    # Determinar branch do repositório
    local repo_branch="mainline"
    if [ "$nginx_version" = "stable" ]; then
        repo_branch="nginx"
    fi
    
    # Adicionar repositório
    local repo_file="/etc/apt/sources.list.d/nginx.list"
    local repo_line="deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] https://nginx.org/packages/${repo_branch}/ubuntu ${ubuntu_codename} nginx"
    
    if [ ! -f "$repo_file" ] || ! grep -qF "$repo_line" "$repo_file" 2>/dev/null; then
        echo "$repo_line" | tee "$repo_file" >/dev/null
        log_success "Repositório do Nginx configurado ($nginx_version)."
    else
        log_debug "Repositório já está configurado."
    fi
    
    # Atualizar lista de pacotes
    log_info "Atualizando lista de pacotes..."
    apt-get update -qq
}

# Função para instalar Nginx
install_nginx() {
    local current_version
    current_version=$(get_nginx_version)
    
    if [ "$current_version" != "not installed" ]; then
        log_warning "Nginx já está instalado (versão: $current_version)"
        read -p "Deseja reinstalar? (s/n): " reinstall
        
        if [[ ! "$reinstall" =~ ^[sS]$ ]]; then
            log_info "Instalação cancelada."
            return 0
        fi
        
        log_info "Removendo versão antiga do Nginx..."
        apt-get remove -y nginx nginx-common nginx-full nginx-core 2>/dev/null || true
        log_success "Versão antiga removida."
    fi
    
    log_info "Instalando Nginx..."
    apt-get install -y nginx >/dev/null 2>&1 || {
        log_error "Falha ao instalar Nginx."
        exit 1
    }
    
    local new_version
    new_version=$(get_nginx_version)
    log_success "Nginx instalado com sucesso (versão: $new_version)."
}

# Função para configurar diretórios
setup_directories() {
    log_info "Configurando diretórios do Nginx..."
    
    # Criar diretórios necessários
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    mkdir -p /var/www/html/.well-known/acme-challenge
    
    # Configurar permissões
    chown -R www-data:www-data /var/www/html/.well-known 2>/dev/null || true
    chmod -R 755 /var/www/html/.well-known
    
    log_success "Diretórios configurados."
}

# Função para configurar nginx.conf
configure_nginx_conf() {
    local NGINX_CONF="/etc/nginx/nginx.conf"
    local INCLUDE_LINE="    include /etc/nginx/sites-enabled/*;"
    local CLIENT_MAX_BODY_SIZE="    client_max_body_size 50M;"
    
    if [ ! -f "$NGINX_CONF" ]; then
        log_error "Arquivo nginx.conf não encontrado: $NGINX_CONF"
        return 1
    fi
    
    log_info "Configurando nginx.conf..."
    
    # Criar backup se não existir
    if [ ! -f "${NGINX_CONF}.bak" ]; then
        cp "$NGINX_CONF" "${NGINX_CONF}.bak"
        log_debug "Backup do nginx.conf criado."
    fi
    
    # Adicionar client_max_body_size se não existir
    if ! grep -qF "client_max_body_size" "$NGINX_CONF"; then
        # Insere client_max_body_size dentro do bloco http
        sed -i "/http {/a\\
$CLIENT_MAX_BODY_SIZE
" "$NGINX_CONF"
        log_success "client_max_body_size 50M adicionado no nginx.conf"
    else
        log_debug "client_max_body_size já presente no nginx.conf"
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
        log_debug "Linha para incluir sites-enabled já presente no nginx.conf"
    fi
}

# Função para configurar default-deny
setup_default_deny() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local deny_conf="${script_dir}/nginx-default-deny.conf"
    
    if [ ! -f "$deny_conf" ]; then
        log_warning "Arquivo nginx-default-deny.conf não encontrado em: $deny_conf"
        log_info "Pulando configuração de default-deny."
        return 0
    fi
    
    log_info "Configurando default-deny..."
    
    cp "$deny_conf" /etc/nginx/sites-available/default-deny
    ln -sf /etc/nginx/sites-available/default-deny /etc/nginx/sites-enabled/default-deny
    
    log_success "Configuração default-deny habilitada."
}

# Função para testar configuração
test_nginx_config() {
    log_info "Testando configuração do Nginx..."
    
    if nginx -t >/dev/null 2>&1; then
        log_success "Configuração do Nginx está válida."
        return 0
    else
        log_error "Configuração do Nginx inválida!"
        log_info "Detalhes do erro:"
        nginx -t
        return 1
    fi
}

# Função para iniciar e habilitar serviço
start_nginx_service() {
    log_info "Iniciando serviço do Nginx..."
    
    # Habilitar serviço
    systemctl enable nginx >/dev/null 2>&1 || {
        log_warning "Falha ao habilitar serviço (pode já estar habilitado)."
    }
    
    # Reiniciar serviço
    systemctl restart nginx >/dev/null 2>&1 || {
        log_error "Falha ao reiniciar serviço do Nginx."
        return 1
    }
    
    # Verificar status
    if systemctl is-active --quiet nginx; then
        log_success "Serviço do Nginx está rodando."
    else
        log_error "Serviço do Nginx não está rodando!"
        systemctl status nginx --no-pager
        return 1
    fi
}

# Função principal
main() {
    local nginx_version="${1:-mainline}"
    
    # Validar versão
    if [[ ! "$nginx_version" =~ ^(stable|mainline)$ ]]; then
        log_error "Versão inválida: $nginx_version"
        log_info "Use: stable ou mainline"
        exit 1
    fi
    
    clear
    echo "========================================================="
    echo "  🔧 Instalação do Nginx para PDL"
    echo "========================================================="
    echo
    
    # Detectar versão do Ubuntu
    local ubuntu_codename
    ubuntu_codename=$(detect_ubuntu_version)
    
    if [ "$ubuntu_codename" = "unknown" ]; then
        log_warning "Não foi possível detectar a versão do Ubuntu."
        read -p "Digite o codename do Ubuntu (ex: jammy, focal): " ubuntu_codename
        if [ -z "$ubuntu_codename" ]; then
            log_error "Codename do Ubuntu é obrigatório."
            exit 1
        fi
    else
        log_info "Versão do Ubuntu detectada: $ubuntu_codename"
    fi
    
    # Verificar versão atual
    local current_version
    current_version=$(get_nginx_version)
    if [ "$current_version" != "not installed" ]; then
        log_info "Versão atual do Nginx: $current_version"
    fi
    
    echo
    log_info "Versão do Nginx a instalar: $nginx_version"
    read -p "Deseja continuar? (s/n): " continue_install
    
    if [[ ! "$continue_install" =~ ^[sS]$ ]]; then
        log_info "Instalação cancelada."
        exit 0
    fi
    
    echo
    
    # Instalar dependências
    install_dependencies
    
    # Configurar repositório
    setup_nginx_repo "$nginx_version" "$ubuntu_codename"
    
    # Instalar Nginx
    install_nginx
    
    # Configurar diretórios
    setup_directories
    
    # Configurar nginx.conf
    configure_nginx_conf
    
    # Configurar default-deny
    setup_default_deny
    
    # Testar configuração
    if ! test_nginx_config; then
        log_error "Falha na configuração. Corrija os erros antes de continuar."
        exit 1
    fi
    
    # Iniciar serviço
    if ! start_nginx_service; then
        log_error "Falha ao iniciar serviço do Nginx."
        exit 1
    fi
    
    # Mostrar informações finais
    echo
    log_success "Nginx instalado e configurado com sucesso!"
    echo
    log_info "Informações:"
    echo "  - Versão: $(get_nginx_version)"
    echo "  - Status: $(systemctl is-active nginx)"
    echo "  - Configuração: /etc/nginx/nginx.conf"
    echo "  - Sites disponíveis: /etc/nginx/sites-available/"
    echo "  - Sites habilitados: /etc/nginx/sites-enabled/"
    echo
    log_info "Comandos úteis:"
    echo "  - Verificar versão: nginx -v"
    echo "  - Testar configuração: nginx -t"
    echo "  - Iniciar: systemctl start nginx"
    echo "  - Parar: systemctl stop nginx"
    echo "  - Reiniciar: systemctl restart nginx"
    echo "  - Recarregar (sem downtime): systemctl reload nginx"
    echo "  - Ver status: systemctl status nginx"
    echo
    log_info "Próximos passos:"
    echo "  - Configure o proxy reverso: sudo bash setup/nginx-proxy.sh"
    echo "  - Instale o Certbot para SSL: sudo apt install certbot python3-certbot-nginx"
    echo
}

# Executar função principal
main "$@"
