#!/bin/bash

################################################################################
# Script de Setup do Painel Definitivo Lineage (PDL)
# 
# Este script prepara o ambiente completo para o PDL, incluindo:
# - Instalação de dependências do sistema
# - Instalação do Docker e Docker Compose
# - Configuração do ambiente Python
# - Criação de arquivos de configuração
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

# Função para criar backup do .env antes de modificações
backup_env_file() {
    local env_file="${1:-.env}"
    
    if [ ! -f "$env_file" ]; then
        return 0  # Se o arquivo não existe, não precisa fazer backup
    fi
    
    # Encontrar o próximo número de backup disponível
    local backup_num=1
    local backup_file="${env_file}.bkp"
    
    while [ -f "$backup_file" ]; do
        backup_num=$((backup_num + 1))
        backup_file="${env_file}.bkp${backup_num}"
    done
    
    # Criar o backup
    cp "$env_file" "$backup_file" 2>/dev/null || {
        log_error "Falha ao criar backup do .env em $backup_file"
        return 1
    }
    
    log_success "Backup do .env criado: $backup_file"
    return 0
}

# Função para verificar se .env está completo
check_env_complete() {
    local env_file="$1"
    local required_vars=(
        "DEBUG"
        "SECRET_KEY"
        "DB_ENGINE"
        "ENCRYPTION_KEY"
        "RENDER_EXTERNAL_HOSTNAME"
        "CONFIG_HCAPTCHA_SITE_KEY"
        "CONFIG_LANGUAGE_CODE"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file" 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        return 1  # Incompleto
    fi
    
    return 0  # Completo
}

INSTALL_DIR="$(pwd)/.install_status"
mkdir -p "$INSTALL_DIR"

clear

echo "========================================================="
echo "  🚀 Bem-vindo ao Instalador do Projeto Lineage 2 PDL!   "
echo "========================================================="
echo

# Detect Ubuntu version
UBUNTU_VERSION=$(lsb_release -cs)
echo "📦 Detectada versão do Ubuntu: $UBUNTU_VERSION"

# Set Docker Compose command based on Ubuntu version
if [ "$UBUNTU_VERSION" = "focal" ]; then
  DOCKER_COMPOSE="docker-compose"
else
  DOCKER_COMPOSE="docker compose"
fi

# Map Ubuntu versions to Docker repository versions
case $UBUNTU_VERSION in
  "focal")
    DOCKER_REPO="focal"
    ;;
  "jammy")
    DOCKER_REPO="jammy"
    ;;
  "noble")
    DOCKER_REPO="jammy"  # Ubuntu 24.04 uses jammy repository for now
    ;;
  *)
    echo "❌ Versão do Ubuntu não suportada: $UBUNTU_VERSION"
    echo "Por favor, use Ubuntu 20.04 (Focal), 22.04 (Jammy) ou 24.04 (Noble)"
    exit 1
    ;;
esac

if [ -f "$INSTALL_DIR/.install_done" ]; then
  echo "⚠️  Instalação já foi concluída anteriormente."
  echo
  read -p "Deseja rodar os containers (s) ou refazer a instalação (r)? (s/r): " OPCAO

  if [[ "$OPCAO" == "s" || "$OPCAO" == "S" ]]; then
    pushd lineage > /dev/null
    $DOCKER_COMPOSE up -d
    popd > /dev/null
    echo "✅ Containers iniciados."
    exit 0
  elif [[ "$OPCAO" == "r" || "$OPCAO" == "R" ]]; then
    echo "🔄 Refazendo instalação..."
    rm -rf "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
  else
    echo "❌ Opção inválida."
    exit 1
  fi
fi

echo "Este script vai preparar todo o ambiente para você."
echo
read -p "Deseja continuar com a instalação? (s/n): " CONTINUE

if [[ "$CONTINUE" != "s" && "$CONTINUE" != "S" ]]; then
  echo "Instalação cancelada."
  exit 0
fi

if ! command -v git &> /dev/null; then
  echo "❌ Git não está instalado. Instalando..."
  sudo apt install -y git
fi

if [ ! -f "$INSTALL_DIR/system_ready" ]; then
  echo
  echo "🔄 Atualizando pacotes e instalando dependências..."
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt update
  
  # Verificar versão atual do Python
  SYSTEM_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "0.0.0")
  PYTHON_MAJOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f1)
  PYTHON_MINOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f2)
  
  echo "Python atual detectado: $SYSTEM_PYTHON_VERSION"
  
  # Verificar se Python é menor que 3.11 ou instalar Python 3.13 de qualquer forma para garantir
  INSTALL_PYTHON313=true
  if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "Python $SYSTEM_PYTHON_VERSION é menor que 3.11 (requerido para autobahn==25.11.1)"
    echo "Instalando Python 3.13..."
  else
    echo "Python $SYSTEM_PYTHON_VERSION atende aos requisitos, mas instalando Python 3.13 para garantir compatibilidade..."
  fi
  
  sudo apt install -y python3.13 python3.13-venv python3.13-dev
  sudo apt install -y apt-transport-https ca-certificates curl gettext
  
  # Configurar python3.13 como padrão usando update-alternatives
  if command -v update-alternatives &> /dev/null; then
    echo "Configurando Python 3.13 como padrão..."
    
    # Detectar qual é o Python do sistema original (antes de mudar)
    SYSTEM_PYTHON_ORIGINAL=$(readlink -f /usr/bin/python3 2>/dev/null | grep -oE "python3\.[0-9]+" || \
                             ls -la /usr/bin/python3.* 2>/dev/null | grep -E "python3\.(10|11)" | head -1 | awk '{print $NF}' | xargs basename || \
                             echo "python3.10")
    
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 2>/dev/null || true
    sudo update-alternatives --set python3 /usr/bin/python3.13 2>/dev/null || true
    echo "Python 3.13 configurado como padrão"
    
    # Resolver problema do apt_pkg: ajustar scripts do sistema para usar Python original
    echo "Ajustando ferramentas do sistema para usar Python $SYSTEM_PYTHON_ORIGINAL..."
    
    SYSTEM_PYTHON_PATH="/usr/bin/$SYSTEM_PYTHON_ORIGINAL"
    if [ ! -f "$SYSTEM_PYTHON_PATH" ]; then
      # Tentar encontrar o caminho correto
      SYSTEM_PYTHON_PATH=$(which "$SYSTEM_PYTHON_ORIGINAL" 2>/dev/null || echo "/usr/bin/$SYSTEM_PYTHON_ORIGINAL")
    fi
    
    if [ -f "$SYSTEM_PYTHON_PATH" ] && [ -f "/usr/lib/cnf-update-db" ]; then
      # Fazer backup do cnf-update-db original
      if [ ! -f "/usr/lib/cnf-update-db.backup" ]; then
        sudo cp /usr/lib/cnf-update-db /usr/lib/cnf-update-db.backup 2>/dev/null || true
      fi
      
      # Modificar o shebang para usar o Python do sistema
      sudo sed -i "1s|^#!.*|#!$SYSTEM_PYTHON_PATH|" /usr/lib/cnf-update-db 2>/dev/null && \
        echo "✅ Ajustado /usr/lib/cnf-update-db para usar $SYSTEM_PYTHON_ORIGINAL" || \
        echo "⚠️  Não foi possível ajustar cnf-update-db automaticamente"
    fi
    
    # Verificar se python3-apt funciona
    if python3 -c "import apt_pkg" 2>/dev/null; then
      echo "✅ python3-apt está funcionando com Python 3.13"
    else
      echo "ℹ️  python3-apt não está disponível para Python 3.13, mas ferramentas do sistema foram ajustadas"
    fi
  fi
  
  touch "$INSTALL_DIR/system_ready"
fi

if [ ! -f "$INSTALL_DIR/docker_ready" ]; then
  echo
  echo "🐳 Instalando Docker e Docker Compose..."
  
  # Remove old versions if they exist
  sudo apt remove -y docker docker-engine docker.io containerd runc || true
  
  # Install prerequisites
  sudo apt update
  sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

  if [ "$UBUNTU_VERSION" = "focal" ]; then
    echo "📦 Instalando Docker do repositório do Ubuntu para Ubuntu 20.04..."
    sudo apt install -y docker.io
  else
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $DOCKER_REPO stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Update package index
    sudo apt update

    # Install Docker Engine
    sudo apt install -y docker-ce docker-ce-cli containerd.io
  fi

  # Start and enable Docker
  sudo systemctl start docker
  sudo systemctl enable docker

  # Verify installation
  if ! docker info &> /dev/null; then
    echo "❌ Docker não está rodando corretamente. Verifique a instalação."
    exit 1
  fi

  # Install Docker Compose
  if ! $DOCKER_COMPOSE version &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Instalando..."
    if [ "$UBUNTU_VERSION" = "focal" ]; then
      echo "📦 Instalando Docker Compose standalone para Ubuntu 20.04..."
      sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose
      sudo rm -f /usr/bin/docker-compose
      sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
      $DOCKER_COMPOSE --version
    else
      echo "📦 Instalando Docker Compose plugin para Ubuntu 22.04/24.04..."
      sudo apt-get update
      sudo apt-get install -y docker-compose-plugin
      $DOCKER_COMPOSE version
    fi
  else
    $DOCKER_COMPOSE version
  fi

  touch "$INSTALL_DIR/docker_ready"
fi

if [ ! -f "$INSTALL_DIR/repo_cloned" ]; then
  echo
  log_info "📂 Verificando repositório do projeto..."
  
  # Se já estamos dentro do repositório (manage.py existe), não precisa clonar
  if [ -f "manage.py" ]; then
    log_success "Repositório já está presente (manage.py encontrado)."
    touch "$INSTALL_DIR/repo_cloned"
  elif [ -d "lineage" ] && [ -f "lineage/manage.py" ]; then
    log_info "Repositório encontrado em subdiretório 'lineage'."
    touch "$INSTALL_DIR/repo_cloned"
  else
    log_info "Clonando repositório do projeto..."
    git clone https://github.com/D3NKYT0/lineage.git || {
      log_error "Falha ao clonar repositório."
      log_info "Certifique-se de que o Git está instalado e você tem acesso à internet."
      exit 1
    }
    log_success "Repositório clonado com sucesso."
    touch "$INSTALL_DIR/repo_cloned"
  fi
fi

# Entrar no diretório do projeto se necessário
if [ -d "lineage" ] && [ -f "lineage/manage.py" ] && [ ! -f "manage.py" ]; then
  pushd lineage > /dev/null
elif [ -f "manage.py" ]; then
  # Já estamos no diretório correto
  :
else
  log_error "Não foi possível encontrar o diretório do projeto."
  exit 1
fi

if [ ! -f "$INSTALL_DIR/python_ready" ]; then
  echo
  echo "🐍 Configurando ambiente Python (virtualenv)..."
  
  # Verificar se python3.13 está disponível, caso contrário usar python3
  if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
  else
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
      echo "❌ Python $PYTHON_VERSION é menor que 3.11 e Python 3.13 não está disponível."
      echo "Execute o script novamente para instalar Python 3.13."
      exit 1
    fi
  fi
  
  $PYTHON_CMD -m venv .venv
  source .venv/bin/activate
  
  # Verificar versão do Python no venv
  VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
  echo "Python no venv: $VENV_PYTHON_VERSION"
  
  pip install --upgrade pip
  pip install --upgrade setuptools wheel

  # Modificar requirements.txt para incluir o repositório do GitHub
  echo "📦 Atualizando requirements.txt..."
  
  # Fazer backup do requirements.txt original
  if [ ! -f "requirements.txt.bak" ]; then
    cp requirements.txt requirements.txt.bak 2>/dev/null || true
  fi
  
  # Limpar o arquivo usando Python para garantir encoding correto
  python3 << 'PYTHON_CLEAN'
import sys
import re

def is_valid_requirement_line(line):
    """Verifica se a linha é válida para requirements.txt"""
    line = line.strip()
    if not line:  # Linha vazia é válida (mas vamos remover no final)
        return True
    # Linha válida deve começar com letra, número, #, -, git+, ou http
    if re.match(r'^[a-zA-Z0-9#\-]|^git\+|^http', line):
        # Verificar se não contém caracteres de controle ou inválidos
        try:
            # Tentar codificar como UTF-8 válido
            line.encode('utf-8')
            return True
        except:
            return False
    return False

try:
    # Ler arquivo com tratamento de encoding
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Se falhar, tentar com errors='ignore'
        with open('requirements.txt', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    
    # Filtrar linhas válidas
    valid_lines = []
    for line in lines:
        cleaned_line = line.rstrip('\n\r')
        if is_valid_requirement_line(cleaned_line):
            valid_lines.append(cleaned_line)
        # Se a linha tem caracteres inválidos, pular
    
    # Remover django-encrypted-fields-and-files se existir
    valid_lines = [l for l in valid_lines if 'django-encrypted-fields-and-files' not in l]
    
    # Remover linhas vazias no final
    while valid_lines and not valid_lines[-1].strip():
        valid_lines.pop()
    
    # Adicionar linha vazia e o repositório do GitHub se não estiver presente
    github_repo = "git+https://github.com/D3NKYT0/django-encrypted-fields.git"
    if github_repo not in valid_lines:
        valid_lines.append("")
        valid_lines.append(github_repo)
    
    # Escrever arquivo limpo
    with open('requirements.txt', 'w', encoding='utf-8', newline='\n') as f:
        for line in valid_lines:
            f.write(line + '\n')
    
    print(f"✅ requirements.txt limpo e atualizado ({len(valid_lines)} linhas válidas)")
    sys.exit(0)
except Exception as e:
    print(f"❌ Erro ao limpar requirements.txt: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_CLEAN
  
  if [ $? -ne 0 ]; then
    log_warning "Falha ao limpar requirements.txt, tentando método alternativo..."
    # Método alternativo simples: usar grep para filtrar linhas válidas
    if [ -f "requirements.txt.bak" ]; then
      # Manter apenas linhas que começam com caracteres válidos
      grep -E '^[a-zA-Z0-9#\-]|^git\+|^http' requirements.txt.bak | \
        grep -v 'django-encrypted-fields-and-files' > requirements.txt.clean 2>/dev/null || true
      
      if [ -f "requirements.txt.clean" ] && [ -s "requirements.txt.clean" ]; then
        mv requirements.txt.clean requirements.txt
        echo "" >> requirements.txt
        echo "git+https://github.com/D3NKYT0/django-encrypted-fields.git" >> requirements.txt
        log_info "requirements.txt limpo usando método alternativo"
      else
        log_error "Não foi possível limpar requirements.txt"
        exit 1
      fi
    else
      log_error "Backup do requirements.txt não encontrado"
      exit 1
    fi
  fi

  # Instalar dependências
  echo "📦 Instalando dependências Python..."
  pip install -r requirements.txt

  # Criar diretórios necessários
  echo "📁 Criando diretórios necessários..."
  mkdir -p logs
  mkdir -p themes
  touch "$INSTALL_DIR/python_ready"
else
  # Verificar se o venv existe e se o Python é >= 3.11
  if [ -d ".venv" ]; then
    source .venv/bin/activate
    
    # Verificar versão do Python no venv
    VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "0.0.0")
    VENV_MAJOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f1)
    VENV_MINOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$VENV_MAJOR" -lt 3 ] || ([ "$VENV_MAJOR" -eq 3 ] && [ "$VENV_MINOR" -lt 11 ]); then
      echo "⚠️  Python no venv ($VENV_PYTHON_VERSION) é menor que 3.11"
      echo "Removendo venv antigo e recriando com Python 3.13..."
      deactivate 2>/dev/null || true
      rm -rf .venv
      
      if command -v python3.13 &> /dev/null; then
        python3.13 -m venv .venv
        source .venv/bin/activate
        echo "✅ Virtual environment recriado com Python 3.13"
      else
        echo "❌ Python 3.13 não encontrado. Execute o script novamente para instalar."
        exit 1
      fi
    fi
  else
    # Se não existe venv, criar com Python 3.13
    if command -v python3.13 &> /dev/null; then
      python3.13 -m venv .venv
      source .venv/bin/activate
    else
      python3 -m venv .venv
      source .venv/bin/activate
    fi
  fi
fi

if [ ! -f "$INSTALL_DIR/env_created" ]; then
  echo
  log_info "⚙️ Criando arquivo .env..."
  if [ ! -f ".env" ]; then
    log_info "Executando script de geração do .env..."
    if [ -f "setup/generate-env.sh" ]; then
      bash setup/generate-env.sh || {
        log_error "Falha ao gerar arquivo .env"
        log_info "Você pode executar manualmente depois com: bash setup/generate-env.sh"
        exit 1
      }
    else
      log_error "Script setup/generate-env.sh não encontrado!"
      exit 1
    fi
  else
    log_warning "Arquivo .env já existe. Verificando se está completo..."
    
    # Verificar se o .env está completo
    if ! check_env_complete ".env"; then
      log_warning "O arquivo .env parece estar incompleto (faltam variáveis obrigatórias)."
      echo
      read -p "Deseja executar o script generate-env.sh para completar o .env? (s/n): " EXEC_GENERATE
      if [[ "$EXEC_GENERATE" =~ ^[sS]$ ]]; then
        log_info "Executando script de geração do .env..."
        if [ -f "setup/generate-env.sh" ]; then
          # Fazer backup do .env existente antes de executar generate-env.sh
          backup_env_file ".env"
          
          # Executar generate-env.sh (ele vai perguntar se quer sobrescrever)
          bash setup/generate-env.sh || {
            log_error "Falha ao gerar arquivo .env"
            log_info "Você pode executar manualmente depois com: bash setup/generate-env.sh"
            exit 1
          }
        else
          log_error "Script setup/generate-env.sh não encontrado!"
          exit 1
        fi
      else
        log_warning "Continuando com o .env existente. Certifique-se de que todas as variáveis necessárias estão configuradas."
      fi
    else
      log_success "Arquivo .env parece estar completo."
    fi
  fi
  
  # Verificar e garantir ENCRYPTION_KEY (obrigatório)
  # IMPORTANTE: NÃO sobrescreve chaves existentes para evitar quebrar dados criptografados
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_warning "ENCRYPTION_KEY não encontrada no .env. Gerando..."
    backup_env_file ".env"
    FERNET_KEY=$(python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
    if [ -n "$FERNET_KEY" ]; then
      echo "" >> .env
      echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
      log_success "ENCRYPTION_KEY adicionada ao .env."
    else
      log_error "Não foi possível gerar ENCRYPTION_KEY."
      log_error "Adicione manualmente ao .env: ENCRYPTION_KEY='sua_chave_aqui'"
      exit 1
    fi
  else
    log_info "ENCRYPTION_KEY já existe no .env (não será sobrescrita para preservar dados criptografados)."
  fi
  
  # Verificar se SECRET_KEY existe no .env
  if ! grep -q "^SECRET_KEY=" .env 2>/dev/null; then
    log_warning "SECRET_KEY não encontrada no .env. Gerando..."
    backup_env_file ".env"
    SECRET_KEY=$(python3 - <<EOF
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
)
    if [ -n "$SECRET_KEY" ]; then
      sed -i "1i SECRET_KEY=$SECRET_KEY" .env
      log_success "SECRET_KEY adicionada ao .env."
    fi
  fi
  
  # Validação final - garantir que ENCRYPTION_KEY existe
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_error "ENCRYPTION_KEY não foi criada corretamente!"
    exit 1
  fi
  
  touch "$INSTALL_DIR/env_created"
  log_success "Arquivo .env criado e validado com sucesso."
fi

# Garantir ENCRYPTION_KEY mesmo se .env já existia (para casos onde foi criado manualmente)
# IMPORTANTE: Só adiciona se não existir, NUNCA substitui chaves existentes
if [ -f ".env" ] && ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
  log_warning "ENCRYPTION_KEY não encontrada no .env existente. Gerando..."
  backup_env_file ".env"
  FERNET_KEY=$(python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
  if [ -n "$FERNET_KEY" ]; then
    echo "" >> .env
    echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
    log_success "ENCRYPTION_KEY adicionada ao .env existente."
  else
    log_error "Não foi possível gerar ENCRYPTION_KEY."
    log_error "Adicione manualmente ao .env: ENCRYPTION_KEY='sua_chave_aqui'"
    exit 1
  fi
elif [ -f ".env" ] && grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
  log_info "ENCRYPTION_KEY já existe no .env (preservada para manter dados criptografados)."
fi

if [ ! -f "$INSTALL_DIR/htpasswd_created" ]; then
  echo
  echo "🔐 Configurando autenticação básica (.htpasswd)..."
  read -p "👤 Digite o login para o admin: " ADMIN_USER
  read -s -p "🔒 Digite a senha para o admin: " ADMIN_PASS
  echo
  mkdir -p nginx
  HASHED_PASS=$(python3 - <<EOF
from passlib.hash import bcrypt
print(bcrypt.using(rounds=10).hash("$ADMIN_PASS"))
EOF
)
  echo "$ADMIN_USER:$HASHED_PASS" > nginx/.htpasswd
  echo "✅ Arquivo nginx/.htpasswd criado."
  touch "$INSTALL_DIR/htpasswd_created"
fi

if [ ! -f "$INSTALL_DIR/fernet_key_generated" ]; then
  # Verificar se ENCRYPTION_KEY já foi gerado pelo generate-env.sh
  # IMPORTANTE: NÃO substitui chaves existentes para evitar quebrar dados criptografados
  # Só substitui a chave placeholder padrão na primeira instalação (quando não há dados ainda)
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_info "ENCRYPTION_KEY não encontrada. Gerando..."
    FERNET_KEY=$(python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
    if [ -n "$FERNET_KEY" ]; then
      echo "" >> .env
      echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
      log_success "ENCRYPTION_KEY adicionada ao .env."
    else
      log_warning "Não foi possível gerar ENCRYPTION_KEY."
    fi
  elif grep -qE "^ENCRYPTION_KEY\s*=\s*['\"]?iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac=" .env 2>/dev/null; then
    # Só substitui se for a chave padrão/placeholder E se for a primeira instalação
    # Verificar se já foi feita instalação anterior (se sim, não substituir!)
    # Verificar também se há containers Docker rodando (instalação antiga)
    local has_running_containers=false
    if command -v docker &> /dev/null; then
      if docker ps --format '{{.Names}}' 2>/dev/null | grep -qE "(site_http|site_wsgi|postgres|celery)"; then
        has_running_containers=true
      fi
    fi
    
    # Verificar se há chave preservada no install.sh
    local has_preserved_key=false
    if [ -f "$INSTALL_DIR/.encryption_key_preserved" ]; then
      has_preserved_key=true
    fi
    
    # Verificar se é primeira instalação (não há instalação anterior)
    if [ ! -f "$INSTALL_DIR/.install_done" ] && [ ! -f "$INSTALL_DIR/build_executed" ] && [ "$has_running_containers" = "false" ] && [ "$has_preserved_key" = "false" ]; then
      log_warning "ENCRYPTION_KEY é a chave padrão/placeholder. Gerando nova chave (primeira instalação)..."
      backup_env_file ".env"
      FERNET_KEY=$(python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
      if [ -n "$FERNET_KEY" ]; then
        sed -i "/^ENCRYPTION_KEY\s*=/c\ENCRYPTION_KEY='$FERNET_KEY'" .env
        log_success "ENCRYPTION_KEY atualizada no .env (chave padrão substituída)."
      else
        log_warning "Não foi possível gerar ENCRYPTION_KEY. Mantendo valor padrão."
      fi
    else
      log_warning "ENCRYPTION_KEY é a chave padrão, mas foi detectada instalação anterior."
      if [ "$has_running_containers" = "true" ]; then
        log_warning "Containers Docker estão rodando - preservando chave para manter dados criptografados."
      fi
      if [ "$has_preserved_key" = "true" ]; then
        log_warning "Chave preservada detectada - não será substituída."
      fi
      log_warning "NÃO será substituída para preservar dados criptografados."
      log_info "Se você realmente precisa substituir, faça backup do banco primeiro e remova os arquivos de status!"
    fi
  else
    log_info "ENCRYPTION_KEY já foi configurada (não será sobrescrita para preservar dados criptografados)."
  fi
  touch "$INSTALL_DIR/fernet_key_generated"
fi

if [ ! -f "$INSTALL_DIR/build_executed" ]; then
  echo
  log_info "🔨 Preparando build.sh..."
  
  # Validar que .env existe e tem ENCRYPTION_KEY antes de executar build.sh
  if [ ! -f ".env" ]; then
    log_error "Arquivo .env não encontrado! Execute primeiro: bash setup/generate-env.sh"
    exit 1
  fi
  
  # Verificar se ENCRYPTION_KEY existe (não gerar aqui, já foi verificado antes)
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_error "ENCRYPTION_KEY não encontrada no .env!"
    log_error "A chave deve ter sido gerada anteriormente. Verifique o .env."
    log_info "Você pode adicionar manualmente ao .env: ENCRYPTION_KEY='sua_chave_aqui'"
    exit 1
  fi
  
  # Não copia mais o build.sh, apenas referencia
  # O build.sh deve ser executado da pasta setup/
  if [ ! -f "setup/build.sh" ]; then
    log_error "Arquivo setup/build.sh não encontrado!"
    exit 1
  fi
  
  chmod +x setup/build.sh || true

  echo
  log_info "🚀 Executando build.sh..."
  bash setup/build.sh || { 
    log_error "Falha ao executar build.sh"
    log_info "Você pode executar manualmente depois com: bash setup/build.sh"
    exit 1
  }

  touch "$INSTALL_DIR/build_executed"
fi

if [ ! -f "$INSTALL_DIR/superuser_created" ]; then
  echo
  log_info "👤 Criando usuário administrador no Django..."
  
  # Perguntar se deseja criar o superuser agora
  read -p "Deseja criar o usuário administrador agora? (s/n): " CREATE_SUPERUSER
  
  if [[ ! "$CREATE_SUPERUSER" =~ ^[sS]$ ]]; then
    log_info "Criação do superuser pulada. Você pode criar depois com:"
    echo "  $DOCKER_COMPOSE exec site_http python3 manage.py createsuperuser"
    touch "$INSTALL_DIR/superuser_created"
  # Verificar se os containers estão rodando
  elif ! $DOCKER_COMPOSE ps | grep -q "site_http.*Up"; then
    log_warning "Containers não estão rodando. Pulando criação de superuser."
    log_info "Você pode criar o superuser depois com:"
    echo "  $DOCKER_COMPOSE exec site_http python3 manage.py createsuperuser"
    touch "$INSTALL_DIR/superuser_created"
  else
    read -p "Username: " DJANGO_SUPERUSER_USERNAME
    read -p "Email: " DJANGO_SUPERUSER_EMAIL
    read -s -p "Password: " DJANGO_SUPERUSER_PASSWORD
    echo
    read -s -p "Confirme a senha: " DJANGO_SUPERUSER_PASSWORD_CONFIRM
    echo

    if [ "$DJANGO_SUPERUSER_PASSWORD" != "$DJANGO_SUPERUSER_PASSWORD_CONFIRM" ]; then
      log_error "As senhas não conferem. Abortando."
      exit 1
    fi

    # Detectar qual serviço usar
    APP_SERVICE=""
    APP_CANDIDATES=("site_http" "site_wsgi" "app" "web" "site" "django" "backend")
    for svc in "${APP_CANDIDATES[@]}"; do
      if $DOCKER_COMPOSE ps --services 2>/dev/null | grep -q "^${svc}$"; then
        if $DOCKER_COMPOSE exec -T "$svc" python3 manage.py --version > /dev/null 2>&1; then
          APP_SERVICE="$svc"
          break
        fi
      fi
    done

    if [ -z "$APP_SERVICE" ]; then
      log_warning "Não foi possível detectar o serviço Django. Pulando criação de superuser."
      log_info "Você pode criar manualmente depois com:"
      echo "  $DOCKER_COMPOSE exec site_http python3 manage.py createsuperuser"
    else
      log_info "Usando serviço: $APP_SERVICE"
      if $DOCKER_COMPOSE exec -T "$APP_SERVICE" python3 manage.py shell <<PYTHON_SCRIPT
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
    print('✅ Superuser \"$DJANGO_SUPERUSER_USERNAME\" criado com sucesso.')
else:
    print('ℹ️ O usuário \"$DJANGO_SUPERUSER_USERNAME\" já existe.')
PYTHON_SCRIPT
      then
        log_success "Superuser criado ou já existente."
      else
        log_warning "Falha ao criar superuser via script. Tente manualmente."
        log_info "Você pode criar manualmente depois com:"
        echo "  $DOCKER_COMPOSE exec $APP_SERVICE python3 manage.py createsuperuser"
      fi
    fi
  fi
  
  touch "$INSTALL_DIR/superuser_created"
fi

# Voltar ao diretório anterior se necessário
if [ "$(pwd)" != "$(dirname "$INSTALL_DIR")" ] && [ -d "lineage" ]; then
  popd > /dev/null 2>&1 || true
fi

touch "$INSTALL_DIR/.install_done"

echo
log_success "🎉 Instalação concluída com sucesso!"
echo
log_info "Informações importantes:"
echo "  - Acesse: http://localhost:6085"
echo "  - Para atualizar: bash setup/build.sh"
echo "  - Para parar: $DOCKER_COMPOSE down"
echo "  - Para iniciar: $DOCKER_COMPOSE up -d"
echo
log_info "Para configurar domínio personalizado:"
echo "  - Execute: sudo bash setup/nginx-proxy.sh"
echo