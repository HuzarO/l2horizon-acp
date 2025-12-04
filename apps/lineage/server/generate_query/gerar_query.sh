#!/bin/bash
# Script Linux/Mac para gerar queries L2 automaticamente
#
# Estrutura:
# - generate_query/ - Ferramentas (este arquivo)
# - generate_query/schemas/ - Schemas mapeados
# - querys/ - Arquivos query_*.py gerados

echo ""
echo "===================================================================="
echo "   GERADOR DE QUERIES L2 - Linux/Mac"
echo "===================================================================="
echo ""

# Mudar para o diretório correto (generate_query/)
cd "$(dirname "$0")"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não encontrado!"
    echo "Por favor, instale Python 3.7+ e tente novamente."
    exit 1
fi

# Verificar se PyYAML está instalado
python3 -c "import yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[AVISO] PyYAML não encontrado. Instalando..."
    pip3 install pyyaml
fi

# Executar o script
if [ -z "$1" ]; then
    echo "Iniciando mapeamento automático..."
    python3 gerar_query.py
else
    echo "Usando schema: $1"
    python3 gerar_query.py "$1"
fi

echo ""
echo "===================================================================="
echo "Processo finalizado!"
echo "===================================================================="
echo ""

