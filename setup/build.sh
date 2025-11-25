#!/bin/bash

# Exit on any error
set -e

# Detect Ubuntu version
UBUNTU_VERSION=$(lsb_release -cs)
if [ "$UBUNTU_VERSION" = "focal" ]; then
  DOCKER_COMPOSE="docker-compose"
else
  DOCKER_COMPOSE="docker compose"
fi

echo "=============================="
echo "Starting deployment process"
echo "=============================="

# Pull latest changes from Git
echo "Pulling latest changes from Git..."
git pull origin main || { echo "Failed to pull from Git repository"; exit 1; }

# Função para verificar e instalar Python 3.13 se necessário
check_and_install_python() {
  echo "Checking Python version..."
  
  # Verificar versão atual do Python
  if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    PYTHON_VERSION=$(python3.13 --version 2>&1 | awk '{print $2}')
    echo "Python 3.13 encontrado: $PYTHON_VERSION"
    return 0
  fi
  
  # Verificar versão do python3 padrão
  SYSTEM_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "0.0.0")
  PYTHON_MAJOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f1)
  PYTHON_MINOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f2)
  
  echo "Python atual detectado: $SYSTEM_PYTHON_VERSION"
  
  # Verificar se Python é menor que 3.11 (requerido para autobahn==25.11.1)
  if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "Python $SYSTEM_PYTHON_VERSION é menor que 3.11 (requerido para autobahn==25.11.1)"
    echo "Instalando Python 3.13 (versão mais recente disponível)..."
    
    # Detectar versão do Ubuntu
    UBUNTU_VERSION=$(lsb_release -cs 2>/dev/null || echo "unknown")
    
    # Adicionar repositório deadsnakes se necessário
    if ! dpkg -l | grep -q python3.13; then
      echo "Adicionando repositório deadsnakes/ppa..."
      sudo apt update
      sudo apt install -y software-properties-common
      sudo add-apt-repository -y ppa:deadsnakes/ppa
      sudo apt update
      
      echo "Instalando Python 3.13 e dependências..."
      sudo apt install -y python3.13 python3.13-venv python3.13-dev
    fi
    
    # Configurar python3.13 como padrão usando update-alternatives
    if command -v update-alternatives &> /dev/null; then
      echo "Configurando Python 3.13 como padrão..."
      sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 2>/dev/null || true
      sudo update-alternatives --set python3 /usr/bin/python3.13 2>/dev/null || true
    fi
    
    PYTHON_CMD="python3.13"
    PYTHON_VERSION=$(python3.13 --version 2>&1 | awk '{print $2}')
    echo "Python 3.13 instalado e configurado: $PYTHON_VERSION"
  else
    PYTHON_CMD="python3"
    PYTHON_VERSION="$SYSTEM_PYTHON_VERSION"
    echo "Python $PYTHON_VERSION atende aos requisitos (>=3.11)"
  fi
}

# Verificar e instalar Python se necessário
check_and_install_python

# Verificar e validar versão do Python no .venv
echo "Checking Python version in virtual environment..."
SYSTEM_PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')

if [ -d ".venv" ]; then
  # Verifica se o .venv existe e obtém a versão do Python dele
  VENV_PYTHON_VERSION=$(.venv/bin/python --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "")
  
  # Comparar versões (considerando apenas major.minor)
  VENV_MAJOR_MINOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f1,2)
  SYSTEM_MAJOR_MINOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f1,2)
  
  if [ -z "$VENV_PYTHON_VERSION" ] || [ "$VENV_MAJOR_MINOR" != "$SYSTEM_MAJOR_MINOR" ]; then
    echo "Virtual environment Python version mismatch or invalid."
    echo "System Python: $SYSTEM_PYTHON_VERSION"
    echo "VENV Python: ${VENV_PYTHON_VERSION:-not found}"
    echo "Removing old virtual environment..."
    rm -rf .venv
    echo "Creating new virtual environment with Python $SYSTEM_PYTHON_VERSION..."
    $PYTHON_CMD -m venv .venv --upgrade-deps || {
      # Se --upgrade-deps não funcionar, criar sem e instalar pip depois
      $PYTHON_CMD -m venv .venv || { echo "Failed to create virtual environment"; exit 1; }
    }
  else
    echo "Virtual environment Python version matches: $VENV_PYTHON_VERSION"
  fi
else
  echo "Virtual environment not found. Creating new one with Python $SYSTEM_PYTHON_VERSION..."
  $PYTHON_CMD -m venv .venv --upgrade-deps || {
    # Se --upgrade-deps não funcionar, criar sem e instalar pip depois
    $PYTHON_CMD -m venv .venv || { echo "Failed to create virtual environment"; exit 1; }
  }
fi

# Activate virtualenv
echo "Activating virtual environment..."
source .venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Verificar se o Python do venv é >= 3.11
VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
VENV_MAJOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f1)
VENV_MINOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f2)

if [ "$VENV_MAJOR" -lt 3 ] || ([ "$VENV_MAJOR" -eq 3 ] && [ "$VENV_MINOR" -lt 11 ]); then
  echo "ERROR: Python no venv ($VENV_PYTHON_VERSION) é menor que 3.11"
  echo "Removendo venv e recriando com Python 3.13..."
  deactivate 2>/dev/null || true
  rm -rf .venv
  if command -v python3.13 &> /dev/null; then
    python3.13 -m venv .venv --upgrade-deps || {
      python3.13 -m venv .venv || { echo "Failed to create virtual environment with Python 3.13"; exit 1; }
    }
    source .venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
    echo "Virtual environment recriado com Python 3.13"
  else
    echo "ERROR: Python 3.13 não encontrado. Execute o script novamente para instalar."
    exit 1
  fi
fi

# Garantir que pip está instalado no venv
echo "Verificando pip no virtual environment..."
if ! python -m pip --version &>/dev/null; then
  echo "pip não encontrado. Instalando pip usando ensurepip..."
  python -m ensurepip --upgrade --default-pip || {
    echo "ensurepip falhou. Tentando instalar pip via get-pip.py..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python || {
      echo "Failed to install pip"
      exit 1
    }
  }
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip || { echo "Failed to upgrade pip"; exit 1; }

# Verificar se .env existe e tem ENCRYPTION_KEY antes de executar comandos Django
if [ ! -f ".env" ]; then
  echo "[ERROR] Arquivo .env não encontrado!"
  echo "[INFO] Execute primeiro: bash setup/generate-env.sh"
  exit 1
fi

if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
  echo "[ERROR] ENCRYPTION_KEY não encontrada no .env!"
  echo "[INFO] Gerando ENCRYPTION_KEY..."
  FERNET_KEY=$(python3 - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
  if [ -n "$FERNET_KEY" ]; then
    echo "" >> .env
    echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
    echo "[SUCCESS] ENCRYPTION_KEY adicionada ao .env."
  else
    echo "[ERROR] Não foi possível gerar ENCRYPTION_KEY."
    echo "[INFO] Adicione manualmente ao .env: ENCRYPTION_KEY='sua_chave_aqui'"
    exit 1
  fi
fi

# Upgrade installed packages from requirements.txt
echo "Upgrading packages from requirements.txt..."
pip install -U -r requirements.txt || { echo "Failed to upgrade packages"; exit 1; }

# Check Django project for issues
echo "Running Django system check (host)..."
python3 manage.py check || { echo "Django check failed"; exit 1; }

# Create new migrations locally
echo "Making migrations (host)..."
python3 manage.py makemigrations || { echo "Failed to make migrations"; exit 1; }

# Stop running containers gracefully
echo "Stopping containers (compose down)..."
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || {
  echo "Warning: Some containers may not have stopped cleanly. Continuing..."
}

# Remove legacy/old containers explicitly (compose service names may have changed)
echo "Removing legacy containers..."
legacy_filters=(
  "name=site"           # old app container name (requested)
  "name=site_wsgi"       # new wsgi app container (cleanup previous runs)
  "name=site_http"      # new http app container (cleanup previous runs)
  "name=web"            # common app alias
  "name=django"         # common app alias
  "name=backend"        # common app alias
  "name=celery"
  "name=celery_beat"
  "name=flower"
  "name=nginx"
  "name=redis"
)

filters_args=()
for f in "${legacy_filters[@]}"; do
  filters_args+=(--filter "$f")
done

containers=$(docker ps -a -q "${filters_args[@]}" 2>/dev/null || true)
if [ -n "$containers" ]; then
  echo "$containers" | xargs -r docker rm -f 2>/dev/null || echo "Some legacy containers could not be removed (maybe already removed)"
else
  echo "No legacy containers found to remove."
fi

# Função para limpar e preparar volumes Docker (SEM apagar volume do banco, media e logs!)
cleanup_volumes() {
  echo "Cleaning up Docker volumes (preserving database, media and logs volumes)..."
  
  # Parar containers SEM remover volumes (para preservar dados do banco, media e logs)
  $DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true
  
  # Lista de volumes para limpar (NÃO inclui postgres_data, media_data e logs_data para preservar dados!)
  local volumes=("lineage_static_data" "static_data")
  
  for vol_name in "${volumes[@]}"; do
    # Verifica se o volume existe
    if docker volume inspect "$vol_name" >/dev/null 2>&1; then
      echo "Removing volume: $vol_name (safe - only static files)"
      # Tenta remover o volume
      docker volume rm "$vol_name" 2>/dev/null || {
        echo "Warning: Could not remove volume $vol_name (may be in use). Trying force cleanup..."
        # Se o volume estiver em uso, tenta usar um container temporário para limpar
        docker run --rm -v "$vol_name":/data alpine sh -c "rm -rf /data/* /data/.[!.]*" 2>/dev/null || true
      }
    fi
  done
  
  echo "Volumes cleaned up (database, media and logs volumes preserved)."
}

# Remove optional static_data volume (if exists and not in use)
echo "Checking for unused volumes..."
# Chama a função de limpeza
cleanup_volumes

# Ensure network exists before building
echo "Ensuring Docker network exists..."
NETWORK_NAME="lineage_network"

# Check if network exists
if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "Network $NETWORK_NAME already exists."
else
  echo "Creating Docker network: $NETWORK_NAME"
  # Try to create network, handling case where it might be in use
  if ! docker network create "$NETWORK_NAME" 2>/dev/null; then
    # If creation failed, try to remove and recreate (only if not in use)
    echo "Network creation failed. Attempting to clean up and recreate..."
    docker network rm "$NETWORK_NAME" 2>/dev/null || true
    sleep 1
    if ! docker network create "$NETWORK_NAME" 2>/dev/null; then
      echo "Warning: Could not create network. Docker Compose will handle it."
    else
      echo "Network $NETWORK_NAME created successfully."
    fi
  else
    echo "Network $NETWORK_NAME created successfully."
  fi
fi

# Build Docker images
echo "Building Docker images (pulling latest bases)..."
$DOCKER_COMPOSE build --pull || { echo "Failed to build Docker images"; exit 1; }

# Preparar volumes antes de iniciar containers
echo "Preparing volumes..."
# Garante que os volumes existam e estejam limpos
$DOCKER_COMPOSE up -d --no-deps --remove-orphans postgres redis 2>/dev/null || true
sleep 2

# Criar diretórios necessários nos volumes usando container temporário
echo "Creating necessary directories in volumes..."
for vol_name in static_data media_data; do
  if docker volume inspect "$vol_name" >/dev/null 2>&1 || docker volume inspect "lineage_${vol_name}" >/dev/null 2>&1; then
    # Usa o nome correto do volume (com ou sem prefixo lineage_)
    actual_vol=$(docker volume ls -q --filter name="${vol_name}$" | head -1)
    if [ -n "$actual_vol" ]; then
      echo "Preparing volume: $actual_vol"
      # Cria diretórios necessários no volume e remove arquivos conflitantes
      docker run --rm -v "$actual_vol":/data alpine sh -c "
        set -e
        # Remove arquivos que podem estar bloqueando a criação de diretórios
        if [ -f /data/pwa/icons ]; then
          echo 'Removing conflicting file: /data/pwa/icons'
          rm -f /data/pwa/icons
        fi
        if [ -f /data/pwa ]; then
          echo 'Removing conflicting file: /data/pwa'
          rm -f /data/pwa
        fi
        # Cria diretórios necessários (pwa/icons primeiro, depois os outros)
        echo 'Creating directory: /data/pwa/icons'
        mkdir -p /data/pwa/icons
        mkdir -p /data/admin 2>/dev/null || true
        mkdir -p /data/rest_framework 2>/dev/null || true
        mkdir -p /data/pwa 2>/dev/null || true
        # Define permissões
        chmod -R 755 /data 2>/dev/null || true
        # Verifica se o diretório foi criado corretamente
        if [ ! -d /data/pwa/icons ]; then
          echo 'ERROR: Failed to create /data/pwa/icons directory' >&2
          exit 1
        fi
        echo 'Successfully prepared volume directories'
      " || {
        echo "Warning: Could not prepare volume $actual_vol using container method."
        echo "Volume will be recreated on next docker-compose up..."
        # Não remove o volume aqui para evitar perda de dados - apenas tenta criar os diretórios
      }
    fi
  fi
done

# Start containers
echo "Starting containers..."
$DOCKER_COMPOSE up -d || { echo "Failed to start containers"; exit 1; }

# Wait for DB (detect common service names)
echo "Waiting for database..."
DB_SERVICE=""
DB_CANDIDATES=("${DB_SERVICE_OVERRIDE}" postgres db postgresql)

for svc in "${DB_CANDIDATES[@]}"; do
  if [ -n "$svc" ]; then
    if $DOCKER_COMPOSE ps --services | grep -q "^${svc}$"; then
      echo "Trying DB service: $svc"
      # Try up to 30s
      for i in {1..15}; do
        if $DOCKER_COMPOSE exec -T "$svc" pg_isready -U "${POSTGRES_USER:-db_user}" > /dev/null 2>&1; then
          DB_SERVICE="$svc"
          break 2
        fi
        echo "$(date '+%H:%M:%S') - $svc not ready yet. Waiting..."
        sleep 2
      done
    fi
  fi
done

if [ -z "$DB_SERVICE" ]; then
  echo "WARNING: Could not detect a PostgreSQL service or it is not responding. Skipping DB wait."
else
  echo "Database service '$DB_SERVICE' is ready."
fi

# Run migration inside container (auto-detect app service)
echo "Applying migrations inside container..."
APP_SERVICE=""
APP_CANDIDATES=("${APP_SERVICE_OVERRIDE}" site_wsgi site_http app web site django backend)
for svc in "${APP_CANDIDATES[@]}"; do
  if [ -n "$svc" ]; then
    if $DOCKER_COMPOSE ps --services | grep -q "^${svc}$"; then
      if $DOCKER_COMPOSE exec -T "$svc" python3 manage.py --version > /dev/null 2>&1; then
        APP_SERVICE="$svc"
        break
      fi
    fi
  fi
done

if [ -z "$APP_SERVICE" ]; then
  echo "ERROR: Could not detect the Django app service to run migrations. Set APP_SERVICE_OVERRIDE or check compose services."
  exit 1
fi

$DOCKER_COMPOSE exec "$APP_SERVICE" python3 manage.py migrate || { echo "Failed to apply migrations"; exit 1; }

# Clean up (non-interactive, only unused resources)
# Preservar volumes de dados importantes: postgres_data, media_data, logs_data
echo "Cleaning up unused Docker resources..."
docker image prune -f 2>/dev/null || true
# Não fazer volume prune - volumes importantes (media, logs, database) devem ser preservados
# docker volume prune -f 2>/dev/null || true  # Desabilitado para preservar volumes de dados
docker container prune -f 2>/dev/null || true
docker builder prune -f 2>/dev/null || true

echo "=============================="
echo "Deployment completed successfully."
echo "=============================="
