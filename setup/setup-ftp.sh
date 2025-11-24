#!/bin/bash

################################################################################
# Script de Configuração do Servidor FTP para Launcher
# 
# Este script configura um servidor FTP (vsftpd) para permitir que o admin
# do host possa hospedar os arquivos do launcher do servidor.
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

# Diretório padrão para FTP
DEFAULT_FTP_DIR="/var/www/launcher"
FTP_DIR=""
FTP_USER="launcher"
FTP_PASSWORD=""

echo "========================================================="
echo "  📁 Configuração do Servidor FTP para Launcher"
echo "========================================================="
echo

# Solicitar diretório FTP
while [ -z "$FTP_DIR" ]; do
    read -p "Digite o diretório para os arquivos do launcher (padrão: ${DEFAULT_FTP_DIR}): " FTP_DIR
    FTP_DIR=$(echo "$FTP_DIR" | xargs)
    
    if [ -z "$FTP_DIR" ]; then
        FTP_DIR="$DEFAULT_FTP_DIR"
    fi
    
    # Validar diretório (não pode ser vazio e deve ser caminho absoluto)
    if [[ ! "$FTP_DIR" =~ ^/ ]]; then
        log_error "O diretório deve ser um caminho absoluto (começando com /)"
        FTP_DIR=""
        continue
    fi
done

log_success "Diretório configurado: $FTP_DIR"

# Solicitar usuário FTP
echo
read -p "Digite o nome do usuário FTP (padrão: ${FTP_USER}): " INPUT_USER
INPUT_USER=$(echo "$INPUT_USER" | xargs)
if [ -n "$INPUT_USER" ]; then
    FTP_USER="$INPUT_USER"
fi

# Validar nome de usuário
if [[ ! "$FTP_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    log_error "Nome de usuário inválido. Use apenas letras minúsculas, números, hífens e underscores."
    exit 1
fi

log_success "Usuário configurado: $FTP_USER"

# Solicitar senha FTP
echo
while [ -z "$FTP_PASSWORD" ]; do
    read -sp "Digite a senha para o usuário FTP: " FTP_PASSWORD
    echo
    if [ -z "$FTP_PASSWORD" ]; then
        log_error "Senha não pode estar vazia."
        continue
    fi
    
    if [ ${#FTP_PASSWORD} -lt 6 ]; then
        log_error "Senha deve ter pelo menos 6 caracteres."
        FTP_PASSWORD=""
        continue
    fi
    
    read -sp "Confirme a senha: " FTP_PASSWORD_CONFIRM
    echo
    
    if [ "$FTP_PASSWORD" != "$FTP_PASSWORD_CONFIRM" ]; then
        log_error "As senhas não coincidem."
        FTP_PASSWORD=""
        continue
    fi
done

log_success "Senha configurada."

# Instalar vsftpd se não estiver instalado
log_info "Verificando instalação do vsftpd..."
if ! command -v vsftpd &> /dev/null; then
    log_info "Instalando vsftpd..."
    apt-get update -qq
    apt-get install -y vsftpd
    log_success "vsftpd instalado."
else
    log_info "vsftpd já está instalado."
fi

# Criar diretório FTP se não existir
log_info "Criando diretório FTP..."
mkdir -p "$FTP_DIR"
chmod 755 "$FTP_DIR"
log_success "Diretório criado: $FTP_DIR"

# Criar usuário FTP se não existir
log_info "Configurando usuário FTP..."
if id "$FTP_USER" &>/dev/null; then
    log_warning "Usuário $FTP_USER já existe. Atualizando senha..."
    echo "$FTP_USER:$FTP_PASSWORD" | chpasswd
else
    # Criar usuário sem shell de login e com diretório home
    useradd -d "$FTP_DIR" -s /bin/bash -m "$FTP_USER" 2>/dev/null || {
        log_warning "Usuário pode já existir. Configurando senha..."
    }
    echo "$FTP_USER:$FTP_PASSWORD" | chpasswd
    log_success "Usuário $FTP_USER criado."
fi

# Configurar permissões do diretório
chown -R "$FTP_USER:$FTP_USER" "$FTP_DIR"
chmod 755 "$FTP_DIR"
log_success "Permissões configuradas."

# Fazer backup da configuração do vsftpd
VSFTPD_CONF="/etc/vsftpd.conf"
if [ ! -f "${VSFTPD_CONF}.bak" ]; then
    cp "$VSFTPD_CONF" "${VSFTPD_CONF}.bak"
    log_info "Backup da configuração do vsftpd criado."
fi

# Configurar vsftpd
log_info "Configurando vsftpd..."

# Criar configuração do vsftpd
cat > "$VSFTPD_CONF" << EOF
# Configuração do vsftpd para Launcher
# Backup original salvo em: ${VSFTPD_CONF}.bak

# Permitir acesso anônimo (desabilitado)
anonymous_enable=NO

# Permitir acesso local
local_enable=YES

# Permitir escrita
write_enable=YES

# Máscara de permissões locais
local_umask=022

# Permitir upload anônimo (desabilitado)
anon_upload_enable=NO

# Permitir criação de diretórios
anon_mkdir_write_enable=NO

# Mostrar mensagem de boas-vindas
dirmessage_enable=YES

# Log de transferências
xferlog_enable=YES

# Porta de dados (passiva)
connect_from_port_20=YES

# Modo passivo
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=50000

# Permitir chroot para usuários locais
chroot_local_user=YES

# Permitir que usuários locais façam upload
allow_writeable_chroot=YES

# Habilitar SSL/TLS (opcional, desabilitado por padrão)
ssl_enable=NO

# Configurações de segurança
secure_chroot_dir=/var/run/vsftpd/empty
pam_service_name=vsftpd
rsa_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
rsa_private_key_file=/etc/ssl/private/ssl-cert-snakeoil.key

# Habilitar IPv4
listen=YES
listen_ipv6=NO

# Timeout
idle_session_timeout=600
data_connection_timeout=120

# Máximo de conexões
max_clients=50
max_per_ip=5

# Banner
ftpd_banner=Welcome to Launcher FTP Server

# Habilitar ASCII
ascii_upload_enable=YES
ascii_download_enable=YES
EOF

log_success "Configuração do vsftpd criada."

# Criar diretório para chroot se não existir
mkdir -p /var/run/vsftpd/empty
chmod 755 /var/run/vsftpd/empty

# Habilitar e iniciar serviço
log_info "Habilitando serviço vsftpd..."
systemctl enable vsftpd
systemctl restart vsftpd

# Verificar se o serviço está rodando
if systemctl is-active --quiet vsftpd; then
    log_success "Serviço vsftpd está rodando."
else
    log_error "Falha ao iniciar serviço vsftpd."
    log_info "Verifique os logs com: journalctl -u vsftpd -n 50"
    exit 1
fi

# Configurar firewall (se ufw estiver ativo)
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    log_info "Configurando firewall (ufw)..."
    ufw allow 21/tcp comment "FTP"
    ufw allow 40000:50000/tcp comment "FTP Passive"
    log_success "Regras do firewall configuradas."
fi

echo
log_success "Configuração do FTP concluída!"
echo
log_info "Resumo da configuração:"
echo "  - Diretório FTP: ${FTP_DIR}"
echo "  - Usuário: ${FTP_USER}"
echo "  - Porta: 21"
echo "  - Portas passivas: 40000-50000"
echo
log_info "Para testar a conexão FTP:"
echo "  ftp://${FTP_USER}@$(hostname -I | awk '{print $1}')"
echo
log_info "Próximo passo:"
echo "  Execute o script setup-nginx-launcher.sh para configurar o Nginx com index of"
echo

