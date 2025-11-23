#!/bin/bash

################################################################################
# Painel Definitivo Lineage (PDL) - Script de Instalação
# 
# Este script automatiza a instalação completa do PDL usando os scripts
# da pasta setup/. Quando os scripts do setup forem atualizados, este
# script não precisa ser alterado, pois sempre usa os scripts mais recentes.
#
# Repositório: https://github.com/D3NKYT0/lineage
# Autor: Daniel Amaral
################################################################################

set -euo pipefail

# Cores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Diretórios
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SETUP_DIR="${SCRIPT_DIR}/setup"
readonly INSTALL_DIR="${SCRIPT_DIR}/.install_status"

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

# Preservar install.sh original para evitar problemas com git
# Esta função garante que o arquivo não seja modificado durante a execução
# Restaura o arquivo do repositório se houver mudanças (normalmente line endings)
preserve_install_sh() {
    local install_sh_path="${SCRIPT_DIR}/install.sh"
    if [ -f "$install_sh_path" ] && [ -d "${SCRIPT_DIR}/.git" ]; then
        # Verificar se há mudanças não commitadas no install.sh
        if ! git -C "${SCRIPT_DIR}" diff --quiet "$install_sh_path" 2>/dev/null; then
            # Há mudanças (provavelmente line endings), restaurar do git
            log_warning "Detectadas mudanças no install.sh (provavelmente line endings)."
            log_info "Restaurando do repositório para evitar conflitos com git pull..."
            if git -C "${SCRIPT_DIR}" checkout -- "$install_sh_path" 2>/dev/null; then
                chmod +x "$install_sh_path" 2>/dev/null || true
                log_success "install.sh restaurado."
            else
                log_warning "Não foi possível restaurar automaticamente. Execute: git checkout -- install.sh"
            fi
        fi
    fi
}

# Função para verificar se o comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para verificar se está rodando como root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "⚠️  Executando como root detectado."
        log_info "Nota: Em servidores, é comum executar como root."
        log_info "O script continuará normalmente. Alguns comandos podem não precisar de sudo."
        echo
    fi
}

# Função para verificar pré-requisitos
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    if ! command_exists git; then
        log_error "Git não está instalado. Por favor, instale o Git primeiro."
        exit 1
    fi
    
    if [ ! -d "${SETUP_DIR}" ]; then
        log_error "Pasta setup/ não encontrada!"
        log_info "Certifique-se de que você está executando este script na raiz do projeto."
        exit 1
    fi
    
    # Verificar se os scripts necessários existem
    local required_scripts=("setup.sh" "build.sh")
    for script in "${required_scripts[@]}"; do
        if [ ! -f "${SETUP_DIR}/${script}" ]; then
            log_error "Script necessário não encontrado: ${SETUP_DIR}/${script}"
            exit 1
        fi
    done
    
    log_success "Pré-requisitos verificados."
}

# Função para detectar versão do Ubuntu
detect_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" = "ubuntu" ]; then
            echo "$VERSION_CODENAME"
        else
            log_warning "Sistema não é Ubuntu. Algumas funcionalidades podem não funcionar."
            echo "unknown"
        fi
    else
        log_warning "Não foi possível detectar a versão do sistema."
        echo "unknown"
    fi
}

# Função para verificar se é um repositório git
is_git_repository() {
    [ -d "${SCRIPT_DIR}/.git" ]
}

# Função para atualizar repositório (git stash + git pull)
update_repository() {
    if ! is_git_repository; then
        log_error "Este diretório não é um repositório git."
        return 1
    fi
    
    log_info "Atualizando repositório..."
    
    cd "${SCRIPT_DIR}" || {
        log_error "Não foi possível acessar o diretório do script."
        return 1
    }
    
    # Verificar se há mudanças locais antes de fazer stash
    if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
        log_info "Fazendo stash das mudanças locais..."
        if git stash push -m "Stash automático antes de atualizar - $(date +%Y-%m-%d\ %H:%M:%S)"; then
            log_success "Mudanças locais salvas no stash."
        else
            log_warning "Falha ao fazer stash. Continuando mesmo assim..."
        fi
    else
        log_info "Nenhuma mudança local para fazer stash."
    fi
    
    # Fazer pull das atualizações
    log_info "Atualizando do repositório remoto..."
    if git pull; then
        log_success "Repositório atualizado com sucesso."
        return 0
    else
        log_error "Falha ao atualizar repositório."
        # Tentar restaurar stash se houve mudanças
        if git stash list | grep -q .; then
            log_info "Tentando restaurar mudanças do stash..."
            git stash pop >/dev/null 2>&1 || true
        fi
        return 1
    fi
}

# Função para clonar repositório se necessário
clone_repository() {
    if [ ! -f "${SCRIPT_DIR}/manage.py" ]; then
        log_info "Repositório não encontrado. Clonando do GitHub..."
        
        local repo_url="https://github.com/D3NKYT0/lineage.git"
        local clone_dir="${SCRIPT_DIR}/lineage"
        
        if [ -d "${clone_dir}" ]; then
            log_warning "Diretório ${clone_dir} já existe. Pulando clone."
        else
            git clone "${repo_url}" "${clone_dir}" || {
                log_error "Falha ao clonar repositório."
                exit 1
            }
            log_success "Repositório clonado com sucesso."
        fi
        
        # Se clonou em subdiretório, informar usuário
        if [ -d "${clone_dir}" ] && [ ! -f "${SCRIPT_DIR}/manage.py" ]; then
            log_info "Repositório clonado em: ${clone_dir}"
            log_info "Execute este script de dentro do diretório clonado."
            exit 0
        fi
    else
        log_success "Repositório já existe."
    fi
}

# Função para mostrar menu de scripts disponíveis
show_scripts_menu() {
    echo
    log_info "Scripts disponíveis na pasta setup/:"
    echo
    echo "  📦 setup.sh           - Instalação inicial completa (Docker, Python, etc.)"
    echo "  🔨 build.sh           - Build e deploy do projeto"
    echo "  💾 backup.sh          - Backup do banco de dados"
    echo "  🌐 nginx-proxy.sh      - Configurar proxy reverso com domínio"
    echo "  🔧 install-nginx.sh    - Instalar Nginx do repositório oficial"
    echo "  ⚙️  generate-env.sh    - Gerar arquivo .env interativamente"
    echo
}

# Função para executar script específico
run_setup_script() {
    local script_name="$1"
    local script_path="${SETUP_DIR}/${script_name}"
    
    if [ ! -f "$script_path" ]; then
        log_error "Script não encontrado: $script_path"
        return 1
    fi
    
    log_info "Executando: $script_name"
    log_info "=========================================="
    
    # Verificar se precisa de sudo
    case "$script_name" in
        nginx-proxy.sh|install-nginx.sh)
            if [ "$EUID" -ne 0 ]; then
                log_info "Este script requer privilégios de root."
                log_info "Executando com sudo..."
                sudo bash "$script_path" || {
                    log_error "Falha ao executar $script_name"
                    return 1
                }
            else
                bash "$script_path" || {
                    log_error "Falha ao executar $script_name"
                    return 1
                }
            fi
            ;;
        *)
            bash "$script_path" || {
                log_error "Falha ao executar $script_name"
                return 1
            }
            ;;
    esac
    
    log_success "Script $script_name executado com sucesso."
}

# Função principal de instalação
main() {
    local action="${1:-install}"
    
    # Preservar install.sh ANTES de qualquer coisa para evitar problemas com git
    preserve_install_sh
    
    clear
    
    echo "========================================================="
    echo "  🚀 Painel Definitivo Lineage (PDL) - Instalador"
    echo "========================================================="
    echo
    
    case "$action" in
        install|"")
            echo "Este script irá:"
            echo "  1. Verificar pré-requisitos"
            echo "  2. Executar setup.sh (instalação inicial)"
            echo "  3. Executar build.sh (build e deploy)"
            echo
            echo "Repositório: https://github.com/D3NKYT0/lineage"
            echo
            ;;
        menu)
            show_scripts_menu
            echo
            log_info "Escolha uma opção:"
            echo "  1) Instalação completa (setup.sh + build.sh)"
            echo "  2) Apenas setup.sh"
            echo "  3) Apenas build.sh"
            if is_git_repository; then
                echo "  4) Atualizar repositório (git pull)"
                echo "  5) Backup do banco de dados"
                echo "  6) Configurar proxy reverso (nginx-proxy.sh)"
                echo "  7) Instalar Nginx (install-nginx.sh)"
                echo "  8) Gerar arquivo .env (generate-env.sh)"
                echo "  9) Listar scripts disponíveis"
                echo "  10) Sair"
                echo
                read -p "Opção: " menu_option
                
                case "$menu_option" in
                    1) action="install" ;;
                    2) action="setup" ;;
                    3) action="build" ;;
                    4) action="update" ;;
                    5) action="backup" ;;
                    6) action="nginx-proxy" ;;
                    7) action="install-nginx" ;;
                    8) action="generate-env" ;;
                    9) show_scripts_menu; exit 0 ;;
                    10) exit 0 ;;
                    *) log_error "Opção inválida."; exit 1 ;;
                esac
            else
                echo "  4) Backup do banco de dados"
                echo "  5) Configurar proxy reverso (nginx-proxy.sh)"
                echo "  6) Instalar Nginx (install-nginx.sh)"
                echo "  7) Gerar arquivo .env (generate-env.sh)"
                echo "  8) Listar scripts disponíveis"
                echo "  9) Sair"
                echo
                read -p "Opção: " menu_option
                
                case "$menu_option" in
                    1) action="install" ;;
                    2) action="setup" ;;
                    3) action="build" ;;
                    4) action="backup" ;;
                    5) action="nginx-proxy" ;;
                    6) action="install-nginx" ;;
                    7) action="generate-env" ;;
                    8) show_scripts_menu; exit 0 ;;
                    9) exit 0 ;;
                    *) log_error "Opção inválida."; exit 1 ;;
                esac
            fi
            ;;
        setup)
            log_info "Executando apenas setup.sh..."
            check_root
            check_prerequisites
            clone_repository
            cd "${SCRIPT_DIR}"
            run_setup_script "setup.sh"
            exit 0
            ;;
        build)
            log_info "Executando apenas build.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "Pasta setup/ não encontrada!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "build.sh"
            exit 0
            ;;
        update)
            log_info "Atualizando repositório..."
            if ! is_git_repository; then
                log_error "Este diretório não é um repositório git."
                exit 1
            fi
            if update_repository; then
                log_success "Repositório atualizado com sucesso!"
            else
                log_error "Falha ao atualizar repositório."
                exit 1
            fi
            exit 0
            ;;
        backup)
            log_info "Executando backup.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "Pasta setup/ não encontrada!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "backup.sh" "${@:2}"
            exit 0
            ;;
        nginx-proxy)
            log_info "Executando nginx-proxy.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "Pasta setup/ não encontrada!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "nginx-proxy.sh"
            exit 0
            ;;
        install-nginx)
            log_info "Executando install-nginx.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "Pasta setup/ não encontrada!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "install-nginx.sh" "${@:2}"
            exit 0
            ;;
        generate-env)
            log_info "Executando generate-env.sh..."
            if [ ! -d "${SETUP_DIR}" ]; then
                log_error "Pasta setup/ não encontrada!"
                exit 1
            fi
            cd "${SCRIPT_DIR}"
            run_setup_script "generate-env.sh"
            exit 0
            ;;
        list|scripts)
            show_scripts_menu
            exit 0
            ;;
        help|--help|-h)
            echo "Uso: $0 [comando]"
            echo
            echo "Comandos:"
            echo "  install          - Instalação completa (setup.sh + build.sh) [padrão]"
            echo "  menu             - Menu interativo para escolher script"
            echo "  setup            - Executar apenas setup.sh"
            echo "  build            - Executar apenas build.sh"
            echo "  update           - Atualizar repositório (git stash + git pull)"
            echo "  backup [args]    - Executar backup.sh (aceita argumentos: list, restore)"
            echo "  nginx-proxy      - Configurar proxy reverso"
            echo "  install-nginx    - Instalar Nginx (aceita: stable, mainline)"
            echo "  generate-env     - Gerar arquivo .env interativamente"
            echo "  list             - Listar todos os scripts disponíveis"
            echo "  help             - Mostrar esta ajuda"
            echo
            echo "Exemplos:"
            echo "  $0                    # Instalação completa"
            echo "  $0 menu                # Menu interativo"
            echo "  $0 update              # Atualizar repositório"
            echo "  $0 backup list         # Listar backups"
            echo "  $0 install-nginx stable  # Instalar Nginx stable"
            echo
            exit 0
            ;;
        *)
            log_error "Comando desconhecido: $action"
            echo "Use '$0 help' para ver os comandos disponíveis."
            exit 1
            ;;
    esac
    
    # Continuar com instalação completa se action ainda for "install"
    if [ "$action" = "install" ]; then
        # Verificar se está rodando como root (apenas aviso, não bloqueia)
        check_root
    
        # Verificar pré-requisitos
        check_prerequisites
        
        # Detectar versão do Ubuntu
        local ubuntu_version
        ubuntu_version=$(detect_ubuntu_version)
        log_info "Versão detectada: ${ubuntu_version}"
        
        # Clonar repositório se necessário
        clone_repository
        
        # Criar diretório de status
        mkdir -p "${INSTALL_DIR}"
        
        # Verificar se já foi instalado
        if [ -f "${INSTALL_DIR}/.install_done" ]; then
            log_warning "Instalação já foi concluída anteriormente."
            echo
            read -p "Deseja rodar apenas o build (b), refazer instalação completa (r) ou sair (s)? (b/r/s): " OPCAO
            
            case "${OPCAO}" in
                b|B)
                    log_info "Executando apenas build.sh..."
                    cd "${SCRIPT_DIR}"
                    bash "${SETUP_DIR}/build.sh"
                    exit 0
                    ;;
                r|R)
                    log_info "Refazendo instalação completa..."
                    rm -rf "${INSTALL_DIR}"
                    mkdir -p "${INSTALL_DIR}"
                    ;;
                s|S)
                    log_info "Saindo..."
                    exit 0
                    ;;
                *)
                    log_error "Opção inválida."
                    exit 1
                    ;;
            esac
        fi
        
        # Confirmar instalação
        echo
        read -p "Deseja continuar com a instalação? (s/n): " CONTINUE
        
        if [[ ! "${CONTINUE}" =~ ^[sS]$ ]]; then
            log_info "Instalação cancelada."
            exit 0
        fi
        
        # Executar setup.sh
        log_info "Executando setup.sh..."
        log_info "=========================================="
        cd "${SCRIPT_DIR}"
        run_setup_script "setup.sh"
        
        # Executar build.sh
        log_info "=========================================="
        log_info "Executando build.sh..."
        log_info "=========================================="
        cd "${SCRIPT_DIR}"
        run_setup_script "build.sh"
        
        # Marcar instalação como concluída
        touch "${INSTALL_DIR}/.install_done"
        
        echo
        log_success "Instalação concluída com sucesso!"
        echo
        log_info "Próximos passos:"
        echo "  - Acesse: http://localhost:6085"
        echo "  - Para atualizar: bash setup/build.sh"
        echo "  - Para parar: docker compose down"
        echo
        log_info "Scripts adicionais disponíveis:"
        echo "  - Backup: $0 backup [list|restore]"
        echo "  - Proxy reverso: $0 nginx-proxy"
        echo "  - Instalar Nginx: $0 install-nginx [stable|mainline]"
        echo
        log_info "Para ver todos os scripts: $0 list"
        echo
    fi
}

# Executar função principal
main "$@"

