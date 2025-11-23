#!/bin/bash

################################################################################
# Script de Backup do Banco de Dados - Painel Definitivo Lineage (PDL)
# 
# Este script realiza backup do banco de dados PostgreSQL do PDL.
# Suporta backup automático e restauração de backups.
#
# Uso:
#   bash setup/backup.sh              # Fazer backup
#   bash setup/backup.sh restore      # Restaurar backup
#   bash setup/backup.sh list         # Listar backups disponíveis
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

# Diretórios e configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MAX_BACKUPS=${MAX_BACKUPS:-7}  # Pode ser sobrescrito por variável de ambiente

# Detectar Docker Compose command
detect_docker_compose() {
    if command -v docker-compose &> /dev/null && docker-compose version &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        log_error "Docker Compose não encontrado!"
        exit 1
    fi
}

DOCKER_COMPOSE=$(detect_docker_compose)

# Função para carregar variáveis do .env
load_env_vars() {
    local env_file="${PROJECT_DIR}/.env"
    
    if [ ! -f "$env_file" ]; then
        log_error "Arquivo .env não encontrado em: $env_file"
        log_info "Usando valores padrão (podem não funcionar)."
        CONTAINER_NAME="postgres"
        DB_NAME="db_name"
        DB_USER="db_user"
        return
    fi
    
    # Carrega variáveis do .env
    set -a
    source "$env_file" 2>/dev/null || true
    set +a
    
    # Define valores padrão se não existirem
    CONTAINER_NAME="${DB_CONTAINER_NAME:-postgres}"
    DB_NAME="${DB_NAME:-db_name}"
    DB_USER="${DB_USERNAME:-db_user}"
    DB_PASS="${DB_PASS:-db_pass}"
    
    log_debug "Configurações carregadas:"
    log_debug "  Container: $CONTAINER_NAME"
    log_debug "  Database: $DB_NAME"
    log_debug "  User: $DB_USER"
}

# Função para verificar se o container está rodando
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_error "Container '${CONTAINER_NAME}' não está rodando!"
        log_info "Inicie o container com: $DOCKER_COMPOSE up -d postgres"
        return 1
    fi
    
    # Verificar se o PostgreSQL está pronto
    log_info "Verificando se PostgreSQL está pronto..."
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" > /dev/null 2>&1; then
            log_success "PostgreSQL está pronto."
            return 0
        fi
        log_debug "Tentativa $attempt/$max_attempts - PostgreSQL ainda não está pronto..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL não está respondendo após $max_attempts tentativas."
    return 1
}

# Função para criar backup
create_backup() {
    log_info "Iniciando backup do banco de dados..."
    
    # Carregar variáveis
    load_env_vars
    
    # Verificar container
    if ! check_container; then
        exit 1
    fi
    
    # Criar diretório de backup
    mkdir -p "$BACKUP_DIR"
    
    # Nome do arquivo de backup
    BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"
    
    log_info "Criando backup: $(basename "$BACKUP_FILE")"
    log_debug "Container: $CONTAINER_NAME"
    log_debug "Database: $DB_NAME"
    log_debug "User: $DB_USER"
    
    # Realizar backup
    if docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -F c -b -v -f "/tmp/backup_${TIMESTAMP}.dump" "${DB_NAME}" 2>/dev/null; then
        # Copiar backup do container e comprimir
        docker cp "${CONTAINER_NAME}:/tmp/backup_${TIMESTAMP}.dump" - | gzip > "$BACKUP_FILE"
        docker exec "${CONTAINER_NAME}" rm -f "/tmp/backup_${TIMESTAMP}.dump" 2>/dev/null || true
        
        # Verificar se o backup foi criado e tem tamanho válido
        if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
            local backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
            log_success "Backup criado com sucesso!"
            log_info "  Arquivo: $(basename "$BACKUP_FILE")"
            log_info "  Tamanho: $backup_size"
            log_info "  Local: $BACKUP_DIR"
        else
            log_error "Backup criado mas arquivo está vazio ou não existe!"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    else
        # Fallback: método alternativo com pg_dump direto
        log_warning "Método de backup custom falhou, tentando método alternativo..."
        if docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "$BACKUP_FILE"; then
            if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
                local backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
                log_success "Backup criado com sucesso (método alternativo)!"
                log_info "  Arquivo: $(basename "$BACKUP_FILE")"
                log_info "  Tamanho: $backup_size"
            else
                log_error "Backup falhou!"
                rm -f "$BACKUP_FILE"
                exit 1
            fi
        else
            log_error "Falha ao criar backup!"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    fi
    
    # Limpar backups antigos
    cleanup_old_backups
    
    echo
    log_success "Backup concluído com sucesso!"
}

# Função para limpar backups antigos
cleanup_old_backups() {
    if [ ! -d "$BACKUP_DIR" ]; then
        return
    fi
    
    local backup_count
    backup_count=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        local remove_count=$((backup_count - MAX_BACKUPS))
        log_info "Removendo $remove_count backup(s) antigo(s) (mantendo os $MAX_BACKUPS mais recentes)..."
        
        find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | \
            sort -r | tail -n "$remove_count" | while read -r old_backup; do
            log_debug "Removendo: $(basename "$old_backup")"
            rm -f "$old_backup"
        done
        
        log_success "Limpeza concluída. Mantidos $MAX_BACKUPS backup(s) mais recente(s)."
    else
        log_debug "Total de backups: $backup_count (limite: $MAX_BACKUPS). Nenhuma limpeza necessária."
    fi
}

# Função para listar backups
list_backups() {
    log_info "Listando backups disponíveis..."
    echo
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null)" ]; then
        log_warning "Nenhum backup encontrado em: $BACKUP_DIR"
        return
    fi
    
    local count=1
    echo -e "${CYAN}#${NC}  ${CYAN}Data/Hora${NC}              ${CYAN}Tamanho${NC}    ${CYAN}Arquivo${NC}"
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
    log_info "Total de backups: $(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | wc -l)"
}

# Função para restaurar backup
restore_backup() {
    log_info "Modo de restauração de backup"
    echo
    
    # Listar backups disponíveis
    list_backups
    echo
    
    # Solicitar arquivo de backup
    read -p "Digite o nome do arquivo de backup para restaurar (ou número): " backup_input
    
    local backup_file=""
    
    # Verificar se é um número
    if [[ "$backup_input" =~ ^[0-9]+$ ]]; then
        local selected=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -o -name "backup_*.dump.gz" 2>/dev/null | sort -r | sed -n "${backup_input}p")
        if [ -n "$selected" ] && [ -f "$selected" ]; then
            backup_file="$selected"
        else
            log_error "Número inválido!"
            exit 1
        fi
    else
        # Verificar se é caminho completo ou apenas nome do arquivo
        if [ -f "$backup_input" ]; then
            backup_file="$backup_input"
        elif [ -f "${BACKUP_DIR}/${backup_input}" ]; then
            backup_file="${BACKUP_DIR}/${backup_input}"
        else
            log_error "Arquivo não encontrado: $backup_input"
            exit 1
        fi
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Arquivo de backup não encontrado!"
        exit 1
    fi
    
    log_warning "ATENÇÃO: Esta operação irá SOBRESCREVER o banco de dados atual!"
    read -p "Tem certeza que deseja continuar? (digite 'SIM' para confirmar): " confirm
    
    if [ "$confirm" != "SIM" ]; then
        log_info "Restauração cancelada."
        exit 0
    fi
    
    # Carregar variáveis
    load_env_vars
    
    # Verificar container
    if ! check_container; then
        exit 1
    fi
    
    log_info "Restaurando backup: $(basename "$backup_file")"
    
    # Verificar tipo de backup (custom dump ou SQL)
    if [[ "$backup_file" == *.dump.gz ]] || gunzip -t "$backup_file" 2>/dev/null && gunzip -c "$backup_file" | file - | grep -q "PostgreSQL"; then
        # Backup custom format
        log_info "Detectado backup em formato custom (pg_restore)..."
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_NAME}" pg_restore -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists --verbose 2>&1 | grep -v "NOTICE" || {
            log_error "Falha ao restaurar backup!"
            exit 1
        }
    else
        # Backup SQL (texto)
        log_info "Detectado backup em formato SQL (psql)..."
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1 || {
            log_error "Falha ao restaurar backup!"
            exit 1
        }
    fi
    
    log_success "Backup restaurado com sucesso!"
    log_warning "Reinicie os containers se necessário: $DOCKER_COMPOSE restart"
}

# Função principal
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
            echo "Uso: $0 [comando]"
            echo
            echo "Comandos:"
            echo "  backup   - Criar backup do banco de dados (padrão)"
            echo "  restore  - Restaurar um backup"
            echo "  list     - Listar backups disponíveis"
            echo "  help     - Mostrar esta ajuda"
            echo
            echo "Variáveis de ambiente:"
            echo "  MAX_BACKUPS - Número máximo de backups a manter (padrão: 7)"
            echo
            ;;
        *)
            log_error "Comando desconhecido: $action"
            echo "Use '$0 help' para ver os comandos disponíveis."
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"
