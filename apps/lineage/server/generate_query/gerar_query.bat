@echo off
REM Script Windows para gerar queries L2 automaticamente
REM 
REM Estrutura:
REM - generate_query/ - Ferramentas (este arquivo)
REM - generate_query/schemas/ - Schemas mapeados
REM - querys/ - Arquivos query_*.py gerados

echo.
echo ====================================================================
echo    GERADOR DE QUERIES L2 - Windows
echo ====================================================================
echo.

REM Mudar para o diretório correto (generate_query/)
cd /d "%~dp0"

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.7+ e tente novamente.
    pause
    exit /b 1
)

REM Verificar se PyYAML está instalado
python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] PyYAML nao encontrado. Instalando...
    pip install pyyaml
)

REM Executar o script
if "%~1"=="" (
    echo Iniciando mapeamento automatico...
    python gerar_query.py
) else (
    echo Usando schema: %1
    python gerar_query.py %1
)

echo.
echo ====================================================================
echo Processo finalizado!
echo ====================================================================
echo.
pause

