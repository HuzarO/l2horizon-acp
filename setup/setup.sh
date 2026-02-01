#!/bin/bash

################################################################################
# Setup Script for Painel Definitivo Lineage (PDL)
# 
# This script prepares the complete environment for PDL, including:
# - System dependencies installation
# - Docker and Docker Compose installation
# - Python environment configuration
# - Configuration files creation
################################################################################

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
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

# Function to create backup of .env before modifications
backup_env_file() {
    local env_file="${1:-.env}"
    
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

# Function to check if .env is complete
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
        return 1  # Incomplete
    fi
    
    return 0  # Complete
}

INSTALL_DIR="$(pwd)/.install_status"
mkdir -p "$INSTALL_DIR"

clear

echo "========================================================="
echo "  🚀 Welcome to Lineage 2 PDL Project Installer!   "
echo "========================================================="
echo

# Detect Ubuntu version
UBUNTU_VERSION=$(lsb_release -cs)
echo "📦 Detected Ubuntu version: $UBUNTU_VERSION"

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
    echo "❌ Ubuntu version not supported: $UBUNTU_VERSION"
    echo "Please use Ubuntu 20.04 (Focal), 22.04 (Jammy) or 24.04 (Noble)"
    exit 1
    ;;
esac

if [ -f "$INSTALL_DIR/.install_done" ]; then
  echo "⚠️  Installation was already completed previously."
  echo
  read -p "Do you want to run containers (y) or redo installation (r)? (y/r): " OPCAO

  if [[ "$OPCAO" == "y" || "$OPCAO" == "Y" ]]; then
    pushd lineage > /dev/null
    $DOCKER_COMPOSE up -d
    popd > /dev/null
    echo "✅ Containers started."
    exit 0
  elif [[ "$OPCAO" == "r" || "$OPCAO" == "R" ]]; then
    echo "🔄 Redoing installation..."
    rm -rf "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
  else
    echo "❌ Invalid option."
    exit 1
  fi
fi

echo "This script will prepare the entire environment for you."
echo
read -p "Do you want to continue with the installation? (y/n): " CONTINUE

if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
  echo "Installation cancelled."
  exit 0
fi

if ! command -v git &> /dev/null; then
  echo "❌ Git is not installed. Installing..."
  sudo apt install -y git
fi

if [ ! -f "$INSTALL_DIR/system_ready" ]; then
  echo
  echo "🔄 Updating packages and installing dependencies..."
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt update
  
  # Check current Python version
  SYSTEM_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "0.0.0")
  PYTHON_MAJOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f1)
  PYTHON_MINOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f2)
  
  echo "Current Python detected: $SYSTEM_PYTHON_VERSION"
  
  # Check if Python is less than 3.11 or install Python 3.13 anyway to ensure
  INSTALL_PYTHON313=true
  if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "Python $SYSTEM_PYTHON_VERSION is less than 3.11 (required for autobahn==25.11.1)"
    echo "Installing Python 3.13..."
  else
    echo "Python $SYSTEM_PYTHON_VERSION meets requirements, but installing Python 3.13 to ensure compatibility..."
  fi
  
  sudo apt install -y python3.13 python3.13-venv python3.13-dev
  sudo apt install -y apt-transport-https ca-certificates curl gettext
  
  # Install bcrypt and passlib in system Python for script usage
  echo "📦 Installing bcrypt and passlib in system Python..."
  # Install bcrypt (latest version) and passlib as fallback
  python3 -m pip install --user --break-system-packages bcrypt "passlib==1.7.4" 2>/dev/null || \
  python3 -m pip install --user bcrypt "passlib==1.7.4" 2>/dev/null || \
  sudo python3 -m pip install bcrypt "passlib==1.7.4" 2>/dev/null || true
  
  # Install system htpasswd as alternative
  sudo apt install -y apache2-utils 2>/dev/null || true
  
  if python3 -c "import bcrypt" 2>/dev/null || python3 -c "import passlib" 2>/dev/null; then
    echo "✅ bcrypt/passlib installed in system Python"
  else
    echo "⚠️  Could not install bcrypt/passlib in system Python (will be installed in venv or use htpasswd)"
  fi
  
  # DO NOT configure Python 3.13 as system default
  # The operating system should continue using Python 3.10 (or 3.11) for system tools
  # Python 3.13 will only be used explicitly in the project's virtual environment
  
  # Ensure Python 3.10 (or system version) remains as default
  SYSTEM_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "")
  SYSTEM_PYTHON_MAJOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f1)
  SYSTEM_PYTHON_MINOR=$(echo "$SYSTEM_PYTHON_VERSION" | cut -d. -f2)
  
  # If Python 3.13 was previously configured as default, revert
  if [ "$SYSTEM_PYTHON_MAJOR" = "3" ] && [ "$SYSTEM_PYTHON_MINOR" = "13" ]; then
    echo "⚠️  Python 3.13 is configured as system default"
    echo "Reverting to system Python (3.10/3.11) to maintain compatibility with system tools..."
    
    # Find system Python (3.10 or 3.11)
    SYSTEM_PYTHON_ORIGINAL=$(ls -1 /usr/bin/python3.* 2>/dev/null | grep -E "python3\.(10|11)" | head -1 | xargs basename 2>/dev/null || echo "python3.10")
    
    if [ -f "/usr/bin/$SYSTEM_PYTHON_ORIGINAL" ]; then
      if command -v update-alternatives &> /dev/null; then
        # Add system Python as alternative if it doesn't exist
        sudo update-alternatives --install /usr/bin/python3 python3 "/usr/bin/$SYSTEM_PYTHON_ORIGINAL" 10 2>/dev/null || true
        # Configure system Python as default
        sudo update-alternatives --set python3 "/usr/bin/$SYSTEM_PYTHON_ORIGINAL" 2>/dev/null || true
        echo "✅ System Python ($SYSTEM_PYTHON_ORIGINAL) configured as default"
      else
        # If update-alternatives is not available, create direct symlink
        sudo ln -sf "/usr/bin/$SYSTEM_PYTHON_ORIGINAL" /usr/bin/python3 2>/dev/null || true
        echo "✅ System Python ($SYSTEM_PYTHON_ORIGINAL) configured as default via symlink"
      fi
    fi
  fi
  
  # Check final version of default Python
  FINAL_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "unknown")
  echo "ℹ️  System default Python: $FINAL_PYTHON_VERSION (for system tools)"
  echo "ℹ️  Python 3.13 installed and available via 'python3.13' (will be used in project's virtual environment)"
  
  touch "$INSTALL_DIR/system_ready"
fi

if [ ! -f "$INSTALL_DIR/docker_ready" ]; then
  echo
  echo "🐳 Installing Docker and Docker Compose..."
  
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
    echo "📦 Installing Docker from Ubuntu repository for Ubuntu 20.04..."
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
    echo "❌ Docker is not running correctly. Check the installation."
    exit 1
  fi

  # Install Docker Compose
  if ! $DOCKER_COMPOSE version &> /dev/null; then
    echo "❌ Docker Compose not found. Installing..."
    if [ "$UBUNTU_VERSION" = "focal" ]; then
      echo "📦 Installing Docker Compose standalone for Ubuntu 20.04..."
      sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose
      sudo rm -f /usr/bin/docker-compose
      sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
      $DOCKER_COMPOSE --version
    else
      echo "📦 Installing Docker Compose plugin for Ubuntu 22.04/24.04..."
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
  log_info "📂 Checking project repository..."
  
  # If already inside the repository (manage.py exists), no need to clone
  if [ -f "manage.py" ]; then
    log_success "Repository already present (manage.py found)."
    touch "$INSTALL_DIR/repo_cloned"
  elif [ -d "lineage" ] && [ -f "lineage/manage.py" ]; then
    log_info "Repository found in subdirectory 'lineage'."
    touch "$INSTALL_DIR/repo_cloned"
  else
    log_info "Cloning project repository..."
    git clone https://github.com/D3NKYT0/lineage.git || {
      log_error "Failed to clone repository."
      log_info "Make sure Git is installed and you have internet access."
      exit 1
    }
    log_success "Repository cloned successfully."
    touch "$INSTALL_DIR/repo_cloned"
  fi
fi

# Enter project directory if needed
if [ -d "lineage" ] && [ -f "lineage/manage.py" ] && [ ! -f "manage.py" ]; then
  pushd lineage > /dev/null
elif [ -f "manage.py" ]; then
  # Already in the correct directory
  :
else
  log_error "Could not find project directory."
  exit 1
fi

if [ ! -f "$INSTALL_DIR/python_ready" ]; then
  echo
  echo "🐍 Configuring Python environment (virtualenv)..."
  
  # Check if python3.13 is available, otherwise use python3
  if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
  else
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
      echo "❌ Python $PYTHON_VERSION is less than 3.11 and Python 3.13 is not available."
      echo "Run the script again to install Python 3.13."
      exit 1
    fi
  fi
  
  $PYTHON_CMD -m venv .venv
  source .venv/bin/activate
  
  # Check Python version in venv
  VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
  echo "Python in venv: $VENV_PYTHON_VERSION"
  
  pip install --upgrade pip
  pip install --upgrade setuptools wheel

  # Modify requirements.txt to include GitHub repository
  echo "📦 Updating requirements.txt..."
  
  # Check if the file is already correct (UTF-8, no null characters, has GitHub repository)
  NEEDS_CLEANUP=false
  HAS_GITHUB_REPO=false
  
  if [ -f "requirements.txt" ]; then
    # Check for null characters (UTF-16) - read first bytes
    if python3 -c "with open('requirements.txt', 'rb') as f: data=f.read(1000); exit(0 if b'\x00' in data else 1)" 2>/dev/null; then
      NEEDS_CLEANUP=true
      echo "⚠️  Detected UTF-16 encoding or invalid characters, file needs cleaning"
    fi
    
    # Check if GitHub repository is already present
    if grep -q "git+https://github.com/D3NKYT0/django-encrypted-fields.git" requirements.txt 2>/dev/null; then
      HAS_GITHUB_REPO=true
    fi
    
    # Check if has django-encrypted-fields-and-files (needs removal)
    if grep -q "django-encrypted-fields-and-files" requirements.txt 2>/dev/null; then
      NEEDS_CLEANUP=true
      echo "ℹ️  Need to remove django-encrypted-fields-and-files and add GitHub repository"
    fi
  fi
  
  # If no cleanup needed and already has repository, just skip
  if [ "$NEEDS_CLEANUP" = "false" ] && [ "$HAS_GITHUB_REPO" = "true" ]; then
    echo "✅ requirements.txt is already up to date, no modification needed"
  else
    # Need to clean or add repository
    # Backup original requirements.txt
    if [ ! -f "requirements.txt.bak" ]; then
      cp requirements.txt requirements.txt.bak 2>/dev/null || true
    fi
    
    if [ "$NEEDS_CLEANUP" = "true" ]; then
  
  # Clean the file using Python to ensure correct encoding
  python3 << 'PYTHON_CLEAN'
import sys
import re

def detect_encoding(file_path):
    """Detects the file encoding"""
    encodings = ['utf-8', 'utf-16', 'utf-16le', 'utf-16be', 'latin-1', 'cp1252']
    
    # Check BOM (Byte Order Mark)
    try:
        with open(file_path, 'rb') as f:
            bom = f.read(4)
            if bom.startswith(b'\xff\xfe'):
                return 'utf-16le'
            elif bom.startswith(b'\xfe\xff'):
                return 'utf-16be'
            elif bom.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
    except:
        pass
    
    # Try each encoding
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return 'utf-8'  # fallback

def clean_line(line):
    """Removes null characters and normalizes the line"""
    # Remove null characters (\x00)
    line = line.replace('\x00', '')
    # Remove BOM if present
    if line.startswith('\ufeff'):
        line = line[1:]
    return line.strip()

def is_valid_requirement_line(line):
    """Checks if the line is valid for requirements.txt"""
    line = clean_line(line)
    if not line:  # Empty line is valid (but we'll remove it at the end)
        return True
    # Valid line should start with letter, number, #, -, git+, or http
    if re.match(r'^[a-zA-Z0-9#\-]|^git\+|^http', line):
        # Check if it doesn't contain invalid control characters (except \n, \r, \t)
        if all(ord(c) >= 32 or c in '\n\r\t' for c in line):
            return True
    return False

try:
    # Detect file encoding
    detected_encoding = detect_encoding('requirements.txt')
    
    # Read file with detected encoding
    try:
        with open('requirements.txt', 'r', encoding=detected_encoding) as f:
            raw_content = f.read()
    except Exception as e:
        # If it fails, try with errors='replace' to replace invalid characters
        with open('requirements.txt', 'r', encoding=detected_encoding, errors='replace') as f:
            raw_content = f.read()
    
    # Split into lines and clean
    lines = raw_content.splitlines()
    
    # Filter and clean valid lines
    valid_lines = []
    for line in lines:
        cleaned_line = clean_line(line)
        if is_valid_requirement_line(cleaned_line):
            valid_lines.append(cleaned_line)
    
    # Remove django-encrypted-fields-and-files if exists
    valid_lines = [l for l in valid_lines if 'django-encrypted-fields-and-files' not in l]
    
    # Remove empty lines at the end
    while valid_lines and not valid_lines[-1].strip():
        valid_lines.pop()
    
    # Add empty line and GitHub repository if not present
    github_repo = "git+https://github.com/D3NKYT0/django-encrypted-fields.git"
    if github_repo not in valid_lines:
        valid_lines.append("")
        valid_lines.append(github_repo)
    
    # Write clean file in UTF-8
    with open('requirements.txt', 'w', encoding='utf-8', newline='\n') as f:
        for line in valid_lines:
            f.write(line + '\n')
    
    print(f"✅ requirements.txt cleaned and updated ({len(valid_lines)} valid lines, encoding converted from {detected_encoding} to UTF-8)")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error cleaning requirements.txt: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_CLEAN
  
    if [ $? -ne 0 ]; then
    log_warning "Failed to clean requirements.txt with Python, trying alternative method..."
    
    # Alternative method: convert encoding and clean
    if [ -f "requirements.txt.bak" ]; then
      # Try to convert from UTF-16 to UTF-8 using iconv (if available)
      if command -v iconv &> /dev/null; then
        # Try UTF-16LE first (more common on Windows)
        iconv -f UTF-16LE -t UTF-8 requirements.txt.bak 2>/dev/null | \
          tr -d '\x00' > requirements.txt.clean 2>/dev/null || \
        iconv -f UTF-16 -t UTF-8 requirements.txt.bak 2>/dev/null | \
          tr -d '\x00' > requirements.txt.clean 2>/dev/null || true
      fi
      
      # If iconv didn't work or is not available, use tr to remove \x00
      if [ ! -f "requirements.txt.clean" ] || [ ! -s "requirements.txt.clean" ]; then
        tr -d '\x00' < requirements.txt.bak > requirements.txt.clean 2>/dev/null || true
      fi
      
      # Filter valid lines
      if [ -f "requirements.txt.clean" ] && [ -s "requirements.txt.clean" ]; then
        # Keep only lines that start with valid characters
        grep -E '^[a-zA-Z0-9#\-]|^git\+|^http' requirements.txt.clean | \
          grep -v 'django-encrypted-fields-and-files' > requirements.txt.tmp 2>/dev/null || true
        
        if [ -f "requirements.txt.tmp" ] && [ -s "requirements.txt.tmp" ]; then
          mv requirements.txt.tmp requirements.txt
          echo "" >> requirements.txt
          echo "git+https://github.com/D3NKYT0/django-encrypted-fields.git" >> requirements.txt
          log_info "requirements.txt cleaned using alternative method (encoding converted)"
        else
          log_error "Could not extract valid lines from requirements.txt"
          exit 1
        fi
      else
        log_error "Could not convert encoding of requirements.txt"
        exit 1
      fi
    else
      log_error "Backup of requirements.txt not found"
      exit 1
    fi
    fi
    else
      # No cleanup needed, just add GitHub repository if not present
      if [ "$HAS_GITHUB_REPO" = "false" ]; then
        echo "ℹ️  Adding GitHub repository to requirements.txt..."
        # Remove django-encrypted-fields-and-files if exists
        sed -i '/django-encrypted-fields-and-files/d' requirements.txt 2>/dev/null || true
        # Add GitHub repository at the end
        echo "" >> requirements.txt
        echo "git+https://github.com/D3NKYT0/django-encrypted-fields.git" >> requirements.txt
        echo "✅ GitHub repository added to requirements.txt"
      fi
    fi
  fi

  # Install dependencies
  echo "📦 Installing Python dependencies..."
  pip install -r requirements.txt

  # Create necessary directories
  echo "📁 Creating necessary directories..."
  mkdir -p logs
  mkdir -p themes
  touch "$INSTALL_DIR/python_ready"
else
  # Check if venv exists and Python is >= 3.11
  if [ -d ".venv" ]; then
    source .venv/bin/activate
    
    # Check Python version in venv
    VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}' 2>/dev/null || echo "0.0.0")
    VENV_MAJOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f1)
    VENV_MINOR=$(echo "$VENV_PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$VENV_MAJOR" -lt 3 ] || ([ "$VENV_MAJOR" -eq 3 ] && [ "$VENV_MINOR" -lt 11 ]); then
      echo "⚠️  Python in venv ($VENV_PYTHON_VERSION) is less than 3.11"
      echo "Removing old venv and recreating with Python 3.13..."
      deactivate 2>/dev/null || true
      rm -rf .venv
      
      if command -v python3.13 &> /dev/null; then
        python3.13 -m venv .venv
        source .venv/bin/activate
        echo "✅ Virtual environment recreated with Python 3.13"
      else
        echo "❌ Python 3.13 not found. Run the script again to install."
        exit 1
      fi
    fi
  else
    # If venv doesn't exist, create with Python 3.13
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
  log_info "⚙️ Creating .env file..."
  if [ ! -f ".env" ]; then
    log_info "Running .env generation script..."
    if [ -f "setup/generate-env.sh" ]; then
      bash setup/generate-env.sh || {
        log_error "Failed to generate .env file"
        log_info "You can run manually later with: bash setup/generate-env.sh"
        exit 1
      }
    else
      log_error "Script setup/generate-env.sh not found!"
      exit 1
    fi
  else
    log_warning ".env file already exists. Checking if it's complete..."
    
    # Check if .env is complete
    if ! check_env_complete ".env"; then
      log_warning "The .env file seems incomplete (missing required variables)."
      echo
      read -p "Do you want to run the generate-env.sh script to complete .env? (y/n): " EXEC_GENERATE
      if [[ "$EXEC_GENERATE" =~ ^[yY]$ ]]; then
        log_info "Running .env generation script..."
        if [ -f "setup/generate-env.sh" ]; then
          # Backup existing .env before running generate-env.sh
          backup_env_file ".env"
          
          # Run generate-env.sh (it will ask if you want to overwrite)
          bash setup/generate-env.sh || {
            log_error "Failed to generate .env file"
            log_info "You can run manually later with: bash setup/generate-env.sh"
            exit 1
          }
        else
          log_error "Script setup/generate-env.sh not found!"
          exit 1
        fi
      else
        log_warning "Continuing with existing .env. Make sure all necessary variables are configured."
      fi
    else
      log_success ".env file appears to be complete."
    fi
  fi
  
  # Check and ensure ENCRYPTION_KEY (required)
  # IMPORTANT: DOES NOT overwrite existing keys to avoid breaking encrypted data
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_warning "ENCRYPTION_KEY not found in .env. Generating..."
    backup_env_file ".env"
    
    # Use venv Python if available
    if [ -f ".venv/bin/python" ]; then
      PYTHON_ENV_CMD=".venv/bin/python"
    elif command -v python &> /dev/null; then
      PYTHON_ENV_CMD="python"
    else
      PYTHON_ENV_CMD="python3"
    fi
    
    FERNET_KEY=$($PYTHON_ENV_CMD - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
    if [ -n "$FERNET_KEY" ]; then
      echo "" >> .env
      echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
      log_success "ENCRYPTION_KEY added to .env."
    else
      log_error "Could not generate ENCRYPTION_KEY."
      log_error "Add manually to .env: ENCRYPTION_KEY='your_key_here'"
      exit 1
    fi
  else
    log_info "ENCRYPTION_KEY already exists in .env (will not be overwritten to preserve encrypted data)."
  fi
  
  # Check if SECRET_KEY exists in .env
  if ! grep -q "^SECRET_KEY=" .env 2>/dev/null; then
    log_warning "SECRET_KEY not found in .env. Generating..."
    backup_env_file ".env"
    
    # Use venv Python if available
    if [ -f ".venv/bin/python" ]; then
      PYTHON_ENV_CMD=".venv/bin/python"
    elif command -v python &> /dev/null; then
      PYTHON_ENV_CMD="python"
    else
      PYTHON_ENV_CMD="python3"
    fi
    
    SECRET_KEY=$($PYTHON_ENV_CMD - <<EOF
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
)
    if [ -n "$SECRET_KEY" ]; then
      sed -i "1i SECRET_KEY=$SECRET_KEY" .env
      log_success "SECRET_KEY added to .env."
    fi
  fi
  
  # Final validation - ensure ENCRYPTION_KEY exists
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_error "ENCRYPTION_KEY was not created correctly!"
    exit 1
  fi
  
  touch "$INSTALL_DIR/env_created"
  log_success ".env file created and validated successfully."
fi

# Ensure ENCRYPTION_KEY even if .env already existed (for cases where it was created manually)
# IMPORTANT: Only adds if it doesn't exist, NEVER replaces existing keys
if [ -f ".env" ] && ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
  log_warning "ENCRYPTION_KEY not found in existing .env. Generating..."
  backup_env_file ".env"
  
  # Use venv Python if available
  if [ -f ".venv/bin/python" ]; then
    PYTHON_ENV_CMD=".venv/bin/python"
  elif command -v python &> /dev/null; then
    PYTHON_ENV_CMD="python"
  else
    PYTHON_ENV_CMD="python3"
  fi
  
  FERNET_KEY=$($PYTHON_ENV_CMD - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
  if [ -n "$FERNET_KEY" ]; then
    echo "" >> .env
    echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
    log_success "ENCRYPTION_KEY added to existing .env."
  else
    log_error "Could not generate ENCRYPTION_KEY."
    log_error "Add manually to .env: ENCRYPTION_KEY='your_key_here'"
    exit 1
  fi
elif [ -f ".env" ] && grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
  log_info "ENCRYPTION_KEY already exists in .env (preserved to maintain encrypted data)."
fi

if [ ! -f "$INSTALL_DIR/htpasswd_created" ]; then
  echo
  echo "🔐 Configuring basic authentication (.htpasswd)..."
  
  # Ensure venv is activated
  if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || true
  fi
  
  # Determine which Python to use and ensure bcrypt/passlib is available
  PYTHON_CMD=""
  
  # Try venv Python first (check bcrypt first, more reliable)
  if [ -f ".venv/bin/python" ] && .venv/bin/python -c "import bcrypt" 2>/dev/null; then
    PYTHON_CMD=".venv/bin/python"
    echo "ℹ️  Using Python from virtual environment (bcrypt available)"
  elif [ -f ".venv/bin/python" ] && .venv/bin/python -c "import passlib" 2>/dev/null; then
    PYTHON_CMD=".venv/bin/python"
    echo "ℹ️  Using Python from virtual environment (passlib available)"
  elif command -v python &> /dev/null && python -c "import bcrypt" 2>/dev/null; then
    PYTHON_CMD="python"
    echo "ℹ️  Using venv Python (activated, bcrypt available)"
  elif command -v python &> /dev/null && python -c "import passlib" 2>/dev/null; then
    PYTHON_CMD="python"
    echo "ℹ️  Using venv Python (activated, passlib available)"
  elif python3 -c "import bcrypt" 2>/dev/null; then
    PYTHON_CMD="python3"
    echo "ℹ️  Using system Python (bcrypt available)"
  elif python3 -c "import passlib" 2>/dev/null; then
    PYTHON_CMD="python3"
    echo "ℹ️  Using system Python (passlib available)"
  else
    # bcrypt/passlib is not available, try to install
    echo "📦 bcrypt/passlib not found, installing..."
    
    # Try to install in venv first
    if [ -f ".venv/bin/python" ]; then
      .venv/bin/python -m pip install bcrypt "passlib==1.7.4" 2>/dev/null && \
      (.venv/bin/python -c "import bcrypt" 2>/dev/null || .venv/bin/python -c "import passlib" 2>/dev/null) && \
      PYTHON_CMD=".venv/bin/python" && \
      echo "✅ bcrypt/passlib installed in virtual environment"
    fi
    
    # If it didn't work, try to install in system
    if [ -z "$PYTHON_CMD" ]; then
      python3 -m pip install --user --break-system-packages bcrypt "passlib==1.7.4" 2>/dev/null || \
      python3 -m pip install --user bcrypt "passlib==1.7.4" 2>/dev/null || \
      sudo python3 -m pip install bcrypt "passlib==1.7.4" 2>/dev/null || true
      
      if python3 -c "import bcrypt" 2>/dev/null || python3 -c "import passlib" 2>/dev/null; then
        PYTHON_CMD="python3"
        echo "✅ bcrypt/passlib installed in system Python"
      else
        # Fallback: use system htpasswd
        if command -v htpasswd &> /dev/null; then
          PYTHON_CMD="htpasswd"
          echo "ℹ️  Using system htpasswd as alternative"
        else
          log_error "Could not install bcrypt/passlib. Install manually: pip install bcrypt passlib"
          exit 1
        fi
      fi
    fi
  fi
  
  read -p "👤 Enter the admin login: " ADMIN_USER
  read -s -p "🔒 Enter the admin password: " ADMIN_PASS
  echo
  mkdir -p nginx
  
  # Generate password hash
  if [ "$PYTHON_CMD" = "htpasswd" ]; then
    # Use system htpasswd
    echo "$ADMIN_PASS" | htpasswd -ciB nginx/.htpasswd "$ADMIN_USER" 2>/dev/null || \
    htpasswd -cbB nginx/.htpasswd "$ADMIN_USER" "$ADMIN_PASS" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo "✅ Hash generated using system htpasswd"
    else
      log_error "Failed to generate hash with htpasswd"
      exit 1
    fi
  else
    # Use Python - try bcrypt directly first (more reliable)
    HASHED_PASS=$($PYTHON_CMD - <<EOF
import sys
try:
    # Try to use bcrypt directly (more reliable and compatible)
    import bcrypt
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw("$ADMIN_PASS".encode('utf-8'), salt)
    print(hashed.decode('utf-8'))
except ImportError:
    # If bcrypt is not available, try passlib
    try:
        from passlib.hash import bcrypt as passlib_bcrypt
        print(passlib_bcrypt.using(rounds=10).hash("$ADMIN_PASS"))
    except Exception as e2:
        print(f"ERROR: Could not import bcrypt or passlib: {e2}", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)
    
    if [ -z "$HASHED_PASS" ] || echo "$HASHED_PASS" | grep -q "ERROR"; then
      log_error "Failed to generate password hash. Trying with system htpasswd..."
      if command -v htpasswd &> /dev/null; then
        echo "$ADMIN_PASS" | htpasswd -ciB nginx/.htpasswd "$ADMIN_USER" 2>/dev/null || \
        htpasswd -cbB nginx/.htpasswd "$ADMIN_USER" "$ADMIN_PASS" 2>/dev/null
        if [ $? -ne 0 ]; then
          log_error "Failed to generate password hash with both methods."
          exit 1
        fi
      else
        log_error "Failed to generate password hash and htpasswd is not available."
        exit 1
      fi
    else
      echo "$ADMIN_USER:$HASHED_PASS" > nginx/.htpasswd
    fi
  fi
  echo "✅ nginx/.htpasswd file created."
  touch "$INSTALL_DIR/htpasswd_created"
fi

if [ ! -f "$INSTALL_DIR/fernet_key_generated" ]; then
  # Check if ENCRYPTION_KEY was already generated by generate-env.sh
  # IMPORTANT: DOES NOT replace existing keys to avoid breaking encrypted data
  # Only replaces the default placeholder key on first installation (when there's no data yet)
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_info "ENCRYPTION_KEY not found. Generating..."
    
    # Use venv Python if available
    if [ -f ".venv/bin/python" ]; then
      PYTHON_ENV_CMD=".venv/bin/python"
    elif command -v python &> /dev/null; then
      PYTHON_ENV_CMD="python"
    else
      PYTHON_ENV_CMD="python3"
    fi
    
    FERNET_KEY=$($PYTHON_ENV_CMD - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
    if [ -n "$FERNET_KEY" ]; then
      echo "" >> .env
      echo "ENCRYPTION_KEY = '$FERNET_KEY'" >> .env
      log_success "ENCRYPTION_KEY added to .env."
    else
      log_warning "Could not generate ENCRYPTION_KEY."
    fi
  elif grep -qE "^ENCRYPTION_KEY\s*=\s*['\"]?iOg0mMfE54rqvAOZKxhmb-Rq0sgmRC4p1TBGu_JqHac=" .env 2>/dev/null; then
    # Only replace if it's the default/placeholder key AND if it's first installation
    # Check if previous installation was done (if yes, don't replace!)
    # Also check if there are running Docker containers (old installation)
    local has_running_containers=false
    if command -v docker &> /dev/null; then
      if docker ps --format '{{.Names}}' 2>/dev/null | grep -qE "(site_http|site_wsgi|postgres|celery)"; then
        has_running_containers=true
      fi
    fi
    
    # Check if there's a preserved key in install.sh
    local has_preserved_key=false
    if [ -f "$INSTALL_DIR/.encryption_key_preserved" ]; then
      has_preserved_key=true
    fi
    
    # Check if it's first installation (no previous installation)
    if [ ! -f "$INSTALL_DIR/.install_done" ] && [ ! -f "$INSTALL_DIR/build_executed" ] && [ "$has_running_containers" = "false" ] && [ "$has_preserved_key" = "false" ]; then
      log_warning "ENCRYPTION_KEY is the default/placeholder key. Generating new key (first installation)..."
      backup_env_file ".env"
      
      # Use venv Python if available
      if [ -f ".venv/bin/python" ]; then
        PYTHON_ENV_CMD=".venv/bin/python"
      elif command -v python &> /dev/null; then
        PYTHON_ENV_CMD="python"
      else
        PYTHON_ENV_CMD="python3"
      fi
      
      FERNET_KEY=$($PYTHON_ENV_CMD - <<EOF
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
EOF
)
      if [ -n "$FERNET_KEY" ]; then
        sed -i "/^ENCRYPTION_KEY\s*=/c\ENCRYPTION_KEY='$FERNET_KEY'" .env
        log_success "ENCRYPTION_KEY updated in .env (default key replaced)."
      else
        log_warning "Could not generate ENCRYPTION_KEY. Keeping default value."
      fi
    else
      log_warning "ENCRYPTION_KEY is the default key, but previous installation detected."
      if [ "$has_running_containers" = "true" ]; then
        log_warning "Docker containers are running - preserving key to maintain encrypted data."
      fi
      if [ "$has_preserved_key" = "true" ]; then
        log_warning "Preserved key detected - will not be replaced."
      fi
      log_warning "Will NOT be replaced to preserve encrypted data."
      log_info "If you really need to replace it, backup the database first and remove status files!"
    fi
  else
    log_info "ENCRYPTION_KEY already configured (will not be overwritten to preserve encrypted data)."
  fi
  touch "$INSTALL_DIR/fernet_key_generated"
fi

if [ ! -f "$INSTALL_DIR/build_executed" ]; then
  echo
  log_info "🔨 Preparing build.sh..."
  
  # Validate that .env exists and has ENCRYPTION_KEY before running build.sh
  if [ ! -f ".env" ]; then
    log_error ".env file not found! Run first: bash setup/generate-env.sh"
    exit 1
  fi
  
  # Check if ENCRYPTION_KEY exists (don't generate here, already checked before)
  if ! grep -qE "^ENCRYPTION_KEY\s*=" .env 2>/dev/null; then
    log_error "ENCRYPTION_KEY not found in .env!"
    log_error "The key should have been generated previously. Check .env."
    log_info "You can add manually to .env: ENCRYPTION_KEY='your_key_here'"
    exit 1
  fi
  
  # No longer copies build.sh, just references it
  # build.sh should be executed from setup/ folder
  if [ ! -f "setup/build.sh" ]; then
    log_error "File setup/build.sh not found!"
    exit 1
  fi
  
  chmod +x setup/build.sh || true

  echo
  log_info "🚀 Running build.sh..."
  bash setup/build.sh || { 
    log_error "Failed to execute build.sh"
    log_info "You can run manually later with: bash setup/build.sh"
    exit 1
  }

  touch "$INSTALL_DIR/build_executed"
fi

if [ ! -f "$INSTALL_DIR/superuser_created" ]; then
  echo
  log_info "👤 Creating Django administrator user..."
  
  # Ask if you want to create the superuser now
  read -p "Do you want to create the administrator user now? (y/n): " CREATE_SUPERUSER
  
  if [[ ! "$CREATE_SUPERUSER" =~ ^[yY]$ ]]; then
    log_info "Superuser creation skipped. You can create later with:"
    echo "  $DOCKER_COMPOSE exec site_http python3 manage.py createsuperuser"
    touch "$INSTALL_DIR/superuser_created"
  # Check if containers are running
  elif ! $DOCKER_COMPOSE ps | grep -q "site_http.*Up"; then
    log_warning "Containers are not running. Skipping superuser creation."
    log_info "You can create the superuser later with:"
    echo "  $DOCKER_COMPOSE exec site_http python3 manage.py createsuperuser"
    touch "$INSTALL_DIR/superuser_created"
  else
    read -p "Username: " DJANGO_SUPERUSER_USERNAME
    read -p "Email: " DJANGO_SUPERUSER_EMAIL
    read -s -p "Password: " DJANGO_SUPERUSER_PASSWORD
    echo
    read -s -p "Confirm password: " DJANGO_SUPERUSER_PASSWORD_CONFIRM
    echo

    if [ "$DJANGO_SUPERUSER_PASSWORD" != "$DJANGO_SUPERUSER_PASSWORD_CONFIRM" ]; then
      log_error "Passwords don't match. Aborting."
      exit 1
    fi

    # Detect which service to use
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
      log_warning "Could not detect Django service. Skipping superuser creation."
      log_info "You can create manually later with:"
      echo "  $DOCKER_COMPOSE exec site_http python3 manage.py createsuperuser"
    else
      log_info "Using service: $APP_SERVICE"
      if $DOCKER_COMPOSE exec -T "$APP_SERVICE" python3 manage.py shell <<PYTHON_SCRIPT
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
    print('✅ Superuser \"$DJANGO_SUPERUSER_USERNAME\" created successfully.')
else:
    print('ℹ️ User \"$DJANGO_SUPERUSER_USERNAME\" already exists.')
PYTHON_SCRIPT
      then
        log_success "Superuser created or already exists."
      else
        log_warning "Failed to create superuser via script. Try manually."
        log_info "You can create manually later with:"
        echo "  $DOCKER_COMPOSE exec $APP_SERVICE python3 manage.py createsuperuser"
      fi
    fi
  fi
  
  touch "$INSTALL_DIR/superuser_created"
fi

# Return to previous directory if necessary
if [ "$(pwd)" != "$(dirname "$INSTALL_DIR")" ] && [ -d "lineage" ]; then
  popd > /dev/null 2>&1 || true
fi

touch "$INSTALL_DIR/.install_done"

echo
log_success "🎉 Installation completed successfully!"
echo
log_info "Important information:"
echo "  - Access: http://localhost:6085"
echo "  - To update: bash setup/build.sh"
echo "  - To stop: $DOCKER_COMPOSE down"
echo "  - To start: $DOCKER_COMPOSE up -d"
echo
log_info "To configure custom domain:"
echo "  - Run: sudo bash setup/nginx-proxy.sh"
echo