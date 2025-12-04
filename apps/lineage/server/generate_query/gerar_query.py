#!/usr/bin/env python3
"""
Script Interativo para Gerar Arquivos Query Automaticamente

Conecta no banco de dados real e gera o arquivo query_*.py
baseado no schema real do banco.
"""

import os
import sys
from pathlib import Path

# Adicionar path do projeto
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from apps.lineage.server.database import LineageDB
from dotenv import load_dotenv
import pymysql

load_dotenv()


def print_header():
    """Imprime cabeçalho do script"""
    print("\n" + "=" * 70)
    print("🔧 GERADOR AUTOMÁTICO DE QUERIES LINEAGE 2")
    print("=" * 70)
    print()


def verificar_banco_configurado():
    """Verifica se o banco está configurado no .env"""
    print("📋 ETAPA 1: Verificando configuração do banco")
    print("-" * 70)
    
    required_vars = {
        'LINEAGE_DB_ENABLED': os.getenv('LINEAGE_DB_ENABLED'),
        'LINEAGE_DB_HOST': os.getenv('LINEAGE_DB_HOST'),
        'LINEAGE_DB_USER': os.getenv('LINEAGE_DB_USER'),
        'LINEAGE_DB_PASSWORD': os.getenv('LINEAGE_DB_PASSWORD'),
        'LINEAGE_DB_NAME': os.getenv('LINEAGE_DB_NAME'),
        'LINEAGE_DB_PORT': os.getenv('LINEAGE_DB_PORT', '3306'),
    }
    
    missing = []
    for var, value in required_vars.items():
        if not value:
            missing.append(var)
            print(f"   ❌ {var}: NÃO CONFIGURADO")
        else:
            # Ocultar senha
            display_value = '***' if 'PASSWORD' in var else value
            print(f"   ✅ {var}: {display_value}")
    
    print()
    
    if missing:
        print("❌ ERRO: Variáveis faltando no .env:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Configure estas variáveis no arquivo .env antes de continuar.")
        return False
    
    # Verificar se está habilitado
    if os.getenv('LINEAGE_DB_ENABLED', 'false').lower() != 'true':
        print("⚠️  AVISO: LINEAGE_DB_ENABLED está desabilitado")
        resposta = input("\n   Deseja habilitar temporariamente para gerar o schema? (s/n): ").lower()
        if resposta != 's':
            return False
    
    print("✅ Banco configurado corretamente!\n")
    return True


def testar_conexao():
    """Testa conexão com o banco"""
    print("📋 ETAPA 2: Testando conexão com o banco")
    print("-" * 70)
    
    try:
        host = os.getenv('LINEAGE_DB_HOST')
        port = int(os.getenv('LINEAGE_DB_PORT', '3306'))
        user = os.getenv('LINEAGE_DB_USER')
        password = os.getenv('LINEAGE_DB_PASSWORD')
        database = os.getenv('LINEAGE_DB_NAME')
        
        print(f"   Conectando em: {user}@{host}:{port}/{database}")
        
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        print(f"   ✅ Conectado com sucesso!")
        print(f"   📊 Versão MySQL: {version}\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}\n")
        return False


def mapear_schema_banco():
    """Mapeia o schema real do banco de dados"""
    print("📋 ETAPA 3: Mapeando schema do banco")
    print("-" * 70)
    
    try:
        host = os.getenv('LINEAGE_DB_HOST')
        port = int(os.getenv('LINEAGE_DB_PORT', '3306'))
        user = os.getenv('LINEAGE_DB_USER')
        password = os.getenv('LINEAGE_DB_PASSWORD')
        database = os.getenv('LINEAGE_DB_NAME')
        
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Listar tabelas importantes
        tabelas_importantes = [
            'characters',
            'character_subclasses',
            'accounts',
            'clan_data',
            'clan_subpledges',
            'ally_data',
            'items',
            'olympiad_nobles',
            'heroes',
            'castle',
            'grandboss_data',
            'raidboss_spawnlist',
            'siege_clans'
        ]
        
        schema = {}
        
        print()
        for tabela in tabelas_importantes:
            try:
                cursor.execute(f"SHOW COLUMNS FROM {tabela}")
                colunas = cursor.fetchall()
                
                schema[tabela] = {
                    'columns': {},
                    'primary_key': None
                }
                
                print(f"   ✅ {tabela}: {len(colunas)} colunas")
                
                for col in colunas:
                    col_name = col[0]
                    col_type = col[1]
                    col_key = col[3]
                    
                    schema[tabela]['columns'][col_name] = col_type
                    
                    if col_key == 'PRI':
                        schema[tabela]['primary_key'] = col_name
                
            except pymysql.err.ProgrammingError:
                print(f"   ⚠️  {tabela}: não encontrada (opcional)")
        
        cursor.close()
        connection.close()
        
        print()
        return schema
        
    except Exception as e:
        print(f"   ❌ Erro ao mapear schema: {e}\n")
        return None


def detectar_configuracoes(schema):
    """Detecta as configurações do schema"""
    print("📋 ETAPA 4: Detectando configurações do schema")
    print("-" * 70)
    
    config = {
        'char_id': 'charId',
        'access_level': 'accesslevel',
        'has_subclass': False,
        'subclass_char_id': 'charId',
        'base_class_col': 'classid',
        'clan_name_source': 'clan_subpledges',
        'has_ally_data': False
    }
    
    # Detectar char_id
    if 'characters' in schema:
        char_cols = schema['characters']['columns']
        
        for candidate in ['obj_Id', 'charId', 'char_id']:
            if candidate in char_cols:
                config['char_id'] = candidate
                print(f"   ✅ ID do personagem: {candidate}")
                break
        
        # Detectar access_level
        for candidate in ['accesslevel', 'accessLevel', 'access_level']:
            if candidate in char_cols:
                config['access_level'] = candidate
                print(f"   ✅ Access level: {candidate}")
                break
        
        # Detectar base_class
        for candidate in ['base_class', 'classid', 'class_id']:
            if candidate in char_cols:
                config['base_class_col'] = candidate
                print(f"   ✅ Coluna de classe: {candidate}")
                break
    
    # Detectar subclass
    if 'character_subclasses' in schema:
        config['has_subclass'] = True
        print(f"   ✅ Tem tabela character_subclasses")
        
        subclass_cols = schema['character_subclasses']['columns']
        # Tentar detectar a coluna de ID na tabela de subclass
        for candidate in ['char_obj_id', 'charId', 'char_id', 'objId']:
            if candidate in subclass_cols:
                config['subclass_char_id'] = candidate
                print(f"   ✅ ID em subclass: {candidate}")
                break
        
        # Detectar coluna de classe na subclass (pode ser diferente de characters)
        for candidate in ['class_id', 'classid', 'base_class']:
            if candidate in subclass_cols:
                # Não sobrescrever base_class_col aqui, manter o de characters
                print(f"   ℹ️  Coluna de classe em subclass: {candidate}")
                break
    else:
        print(f"   ⚠️  Não tem tabela character_subclasses")
    
    # Detectar estrutura de clan
    if 'clan_data' in schema:
        clan_cols = schema['clan_data']['columns']
        
        # Verificar se tem clan_name diretamente em clan_data
        if 'clan_name' in clan_cols:
            config['clan_name_source'] = 'clan_data'
            print(f"   ✅ Nome do clan: clan_data.clan_name")
        elif 'clan_subpledges' in schema:
            config['clan_name_source'] = 'clan_subpledges'
            print(f"   ✅ Nome do clan: clan_subpledges.name (sub_pledge_id = 0)")
        else:
            print(f"   ⚠️  Estrutura de clan não identificada")
    
    # Detectar ally_data
    if 'ally_data' in schema:
        config['has_ally_data'] = True
        print(f"   ✅ Tem tabela ally_data separada")
    else:
        print(f"   ⚠️  Não tem tabela ally_data (usa clan_data.ally_id)")
    
    print()
    return config


def gerar_arquivo_query(nome_projeto, schema, config):
    """Gera o arquivo query_*.py"""
    print("📋 ETAPA 5: Gerando arquivo de query")
    print("-" * 70)
    
    from classes.lineage_stats import get_lineage_stats_template
    from classes.lineage_services import get_lineage_services_template
    from classes.lineage_account import get_lineage_account_template
    from classes.transfer_wallet_to_char import get_transfer_wallet_to_char_template
    from classes.transfer_char_to_wallet import get_transfer_char_to_wallet_template
    from classes.lineage_marketplace import get_lineage_marketplace_template
    from classes.lineage_inflation import get_lineage_inflation_template
    
    # Preparar estrutura de clan
    clan_structure = {
        'clan_name_source': config['clan_name_source'],
        'has_ally_data': config['has_ally_data']
    }
    
    # Gerar classes
    print("   📝 Gerando classe LineageStats...")
    stats_code = get_lineage_stats_template(
        char_id=config['char_id'],
        access_level=config['access_level'],
        has_subclass=config['has_subclass'],
        subclass_char_id=config['subclass_char_id'],
        clan_structure=clan_structure,
        base_class_col=config['base_class_col']
    )
    
    print("   📝 Gerando classe LineageServices...")
    services_code = get_lineage_services_template(
        char_id=config['char_id'],
        has_subclass=config['has_subclass'],
        subclass_char_id=config['subclass_char_id'],
        base_class_col=config['base_class_col']
    )
    
    print("   📝 Gerando classe LineageAccount...")
    account_code = get_lineage_account_template(
        access_level_column=config['access_level']
    )
    
    print("   📝 Gerando classe TransferFromWalletToChar...")
    wallet_to_char_code = get_transfer_wallet_to_char_template(
        char_id=config['char_id']
    )
    
    print("   📝 Gerando classe TransferFromCharToWallet...")
    char_to_wallet_code = get_transfer_char_to_wallet_template(
        char_id=config['char_id']
    )
    
    print("   📝 Gerando classe LineageMarketplace...")
    marketplace_code = get_lineage_marketplace_template(
        char_id=config['char_id'],
        access_level_column=config['access_level']
    )
    
    print("   📝 Gerando classe LineageInflation...")
    inflation_code = get_lineage_inflation_template(
        char_id=config['char_id'],
        access_level=config['access_level']
    )
    
    # Montar arquivo completo
    from datetime import datetime
    
    arquivo_completo = f'''"""
Query File: query_{nome_projeto}.py
Generated automatically by Query Generator
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database Schema: {nome_projeto}

⚠️  Este arquivo foi gerado automaticamente.
    Para regenerar, execute: python gerar_query.py
"""

from apps.lineage.server.database import LineageDB
from apps.lineage.server.utils.cache import cache_lineage_result

import time
import base64
import hashlib
from datetime import datetime


# ============================================================================
# CONFIGURAÇÃO DO SCHEMA - Nomes reais das colunas do banco
# ============================================================================
# ⚠️  NÃO use nomes hardcoded nas views!
#     SEMPRE use estas constantes:
#     
#     Exemplo:
#       ❌ ERRADO: account['accesslevel']
#       ✅ CERTO:  account[ACCESS_LEVEL]

# Tabela: characters
CHAR_ID = '{config['char_id']}'                    # obj_Id, charId ou char_id
ACCESS_LEVEL = '{config['access_level']}'          # accesslevel, accessLevel ou access_level
BASE_CLASS_COL = '{config['base_class_col']}'      # classid, base_class ou class_id

# Tabela: character_subclasses
HAS_SUBCLASS = {config['has_subclass']}            # Se tem tabela de subclass
SUBCLASS_CHAR_ID = '{config['subclass_char_id']}'  # Coluna de ID na subclass

# Estrutura de Clans
CLAN_NAME_SOURCE = '{config['clan_name_source']}'  # clan_data ou clan_subpledges
HAS_ALLY_DATA = {config['has_ally_data']}          # Se tem tabela ally_data

# ============================================================================


{stats_code}

{services_code}

{account_code}

{wallet_to_char_code}

{char_to_wallet_code}

{marketplace_code}

{inflation_code}
'''
    
    # Salvar arquivo
    output_dir = Path(__file__).parent.parent / 'querys'
    output_file = output_dir / f'query_{nome_projeto}.py'
    
    # Fazer backup se já existir
    if output_file.exists():
        backup_file = output_dir / f'query_{nome_projeto}.py.backup'
        print(f"   💾 Backup: {backup_file.name}")
        import shutil
        shutil.copy(output_file, backup_file)
    
    # Salvar
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(arquivo_completo)
    
    print(f"   ✅ Arquivo gerado: {output_file.name}")
    print(f"   📁 Caminho: {output_file}")
    print()
    
    return output_file


def main():
    """Função principal"""
    print_header()
    
    # Etapa 1: Pedir nome do projeto
    print("📋 ETAPA 0: Nome do projeto")
    print("-" * 70)
    nome_projeto = input("   Digite o nome do projeto (ex: mobius, l2jpremium, acis): ").strip().lower()
    
    if not nome_projeto:
        print("   ❌ Nome do projeto é obrigatório!")
        return
    
    print(f"   ✅ Projeto: {nome_projeto}\n")
    
    # Etapa 2: Verificar .env
    if not verificar_banco_configurado():
        print("\n❌ Configure o banco no .env e tente novamente.")
        return
    
    # Etapa 3: Testar conexão
    if not testar_conexao():
        print("\n❌ Não foi possível conectar ao banco.")
        return
    
    # Etapa 4: Mapear schema
    schema = mapear_schema_banco()
    if not schema:
        print("\n❌ Não foi possível mapear o schema.")
        return
    
    # Etapa 5: Detectar configurações
    config = detectar_configuracoes(schema)
    
    # Etapa 6: Confirmação
    print("📋 RESUMO DA CONFIGURAÇÃO")
    print("-" * 70)
    print(f"   Projeto: {nome_projeto}")
    print(f"   Tabelas encontradas: {len(schema)}")
    print(f"   ID do personagem: {config['char_id']}")
    print(f"   Access level: {config['access_level']}")
    print(f"   Tem subclass: {'Sim' if config['has_subclass'] else 'Não'}")
    print(f"   Nome do clan: {config['clan_name_source']}")
    print()
    
    resposta = input("   Gerar arquivo query_" + nome_projeto + ".py? (s/n): ").lower()
    if resposta != 's':
        print("\n❌ Geração cancelada.")
        return
    
    print()
    
    # Etapa 7: Gerar arquivo
    output_file = gerar_arquivo_query(nome_projeto, schema, config)
    
    # Sucesso!
    print("=" * 70)
    print("✅ ARQUIVO GERADO COM SUCESSO!")
    print("=" * 70)
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário.")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
