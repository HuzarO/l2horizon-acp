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
            'epic_boss_spawn',  # Mobius usa epic_boss_spawn para grandboss
            'raidboss_spawnlist',
            'raidboss_status',  # Mobius usa raidboss_status ao invés de raidboss_spawnlist
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
        'base_class_col': None,  # será detectado ou permanece None
        'clan_name_source': 'clan_subpledges',
        'subpledge_filter': 'sub_pledge_id',  # ou 'type' ou None
        'has_ally_data': False,
        'clan_id_col': 'clan_id',  # padrão
        'crest_col': 'crest_id',  # padrão, pode ser None
        'clan_leader_col': 'leader_id',  # padrão, pode ser None
        'subclass_filter_base': "isBase = '1'",  # padrão para Mobius
        'subclass_filter_sub': "isBase = '0'"  # padrão para Mobius
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
        base_class_found = False
        for candidate in ['base_class', 'classid', 'class_id']:
            if candidate in char_cols:
                config['base_class_col'] = candidate
                print(f"   ✅ Coluna de classe em characters: {candidate}")
                base_class_found = True
                break
        
        if not base_class_found:
            config['base_class_col'] = None
            print(f"   ⚠️  Coluna de classe não encontrada em characters (será buscada em character_subclasses)")
    
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
        
        # Detectar filtro de subclass (isBase ou class_index)
        if 'isBase' in subclass_cols:
            config['subclass_filter_base'] = "isBase = '1'"
            config['subclass_filter_sub'] = "isBase = '0'"
            print(f"   ✅ Filtro de subclass: isBase")
        elif 'class_index' in subclass_cols:
            config['subclass_filter_base'] = "class_index = 0"
            config['subclass_filter_sub'] = "class_index > 0"
            print(f"   ✅ Filtro de subclass: class_index")
        else:
            # Fallback para isBase
            config['subclass_filter_base'] = "isBase = '1'"
            config['subclass_filter_sub'] = "isBase = '0'"
            print(f"   ⚠️  Filtro de subclass não detectado, usando padrão: isBase")
    else:
        print(f"   ⚠️  Não tem tabela character_subclasses")
    
    # Detectar estrutura de clan
    if 'clan_data' in schema:
        clan_cols = schema['clan_data']['columns']
        
        # Detectar coluna de ID do clan
        clan_id_detected = False
        for candidate in ['clan_id', 'clanId', 'id']:
            if candidate in clan_cols:
                config['clan_id_col'] = candidate
                print(f"   ✅ ID do clan: {candidate}")
                clan_id_detected = True
                break
        
        if not clan_id_detected:
            # Usar primary key se não encontrou
            if schema['clan_data'].get('primary_key'):
                config['clan_id_col'] = schema['clan_data']['primary_key']
                print(f"   ✅ ID do clan (PK): {config['clan_id_col']}")
            else:
                print(f"   ⚠️  ID do clan não detectado, usando padrão: {config['clan_id_col']}")
        
        # Detectar coluna de crest
        for candidate in ['crest_id', 'crestId', 'crest', 'crestid']:
            if candidate in clan_cols:
                config['crest_col'] = candidate
                print(f"   ✅ Coluna de crest: {candidate}")
                break
        else:
            # Se não encontrou, usar None (não tem crest)
            config['crest_col'] = None
            print(f"   ⚠️  Coluna de crest não encontrada")
        
        # Detectar coluna de leader
        for candidate in ['leader_id', 'leaderId', 'leader', 'leaderid']:
            if candidate in clan_cols:
                config['clan_leader_col'] = candidate
                print(f"   ✅ Coluna de líder do clan: {candidate}")
                break
        else:
            # Se não encontrou, usar None (não tem leader ou está em outra tabela)
            config['clan_leader_col'] = None
            print(f"   ⚠️  Coluna de líder do clan não encontrada")
        
        # Verificar se tem clan_name diretamente em clan_data
        if 'clan_name' in clan_cols:
            config['clan_name_source'] = 'clan_data'
            print(f"   ✅ Nome do clan: clan_data.clan_name")
        elif 'clan_subpledges' in schema:
            # Verificar se clan_subpledges tem sub_pledge_id
            subpledge_cols = schema['clan_subpledges']['columns']
            if 'sub_pledge_id' in subpledge_cols or 'type' in subpledge_cols:
                config['clan_name_source'] = 'clan_subpledges'
                config['subpledge_filter'] = 'sub_pledge_id' if 'sub_pledge_id' in subpledge_cols else 'type'
                print(f"   ✅ Nome do clan: clan_subpledges.name ({config['subpledge_filter']} = 0)")
            else:
                # clan_subpledges sem filtro (só tem o nome do clan principal)
                config['clan_name_source'] = 'clan_subpledges_simple'
                print(f"   ✅ Nome do clan: clan_subpledges.name (sem filtro)")
        else:
            print(f"   ⚠️  Estrutura de clan não identificada")
    
    # Detectar ally_data
    if 'ally_data' in schema:
        config['has_ally_data'] = True
        print(f"   ✅ Tem tabela ally_data separada")
    else:
        print(f"   ⚠️  Não tem tabela ally_data (usa clan_data.ally_id)")
    
    # Detectar colunas de castle
    if 'castle' in schema:
        castle_cols = schema['castle']['columns']
        
        # Detectar coluna de siege date
        for candidate in ['siegeDate', 'siege_date', 'siegedate', 'next_siege_date']:
            if candidate in castle_cols:
                config['castle_siege_date_col'] = candidate
                print(f"   ✅ Coluna de siege date: {candidate}")
                break
        else:
            config['castle_siege_date_col'] = None
            print(f"   ⚠️  Coluna de siege date não encontrada")
        
        # Detectar coluna de treasury
        for candidate in ['treasury', 'tax_income', 'tax_money']:
            if candidate in castle_cols:
                config['castle_treasury_col'] = candidate
                break
        else:
            config['castle_treasury_col'] = 'treasury'
    else:
        config['castle_siege_date_col'] = 'siegeDate'
        config['castle_treasury_col'] = 'treasury'
    
    # Detectar tabelas opcionais de boss
    if 'raidboss_spawnlist' in schema:
        config['has_raidboss_table'] = True
        config['raidboss_table_name'] = 'raidboss_spawnlist'
        raidboss_cols = schema['raidboss_spawnlist']['columns']
        
        # Detectar coluna de ID do boss
        for candidate in ['boss_id', 'id', 'npc_id']:
            if candidate in raidboss_cols:
                config['raidboss_id_col'] = candidate
                break
        else:
            config['raidboss_id_col'] = 'boss_id'  # fallback
        
        # Detectar coluna de respawn
        for candidate in ['respawn_time', 'respawnTime', 'respawn', 'next_respawn_time', 'respawn_delay', 'date_of_death']:
            if candidate in raidboss_cols:
                config['raidboss_respawn_col'] = candidate
                break
        else:
            config['raidboss_respawn_col'] = 'respawn_time'  # fallback
        
        print(f"   ✅ Tabela de raidboss: raidboss_spawnlist (ID: {config['raidboss_id_col']}, Respawn: {config['raidboss_respawn_col']})")
    elif 'raidboss_status' in schema:
        config['has_raidboss_table'] = True
        config['raidboss_table_name'] = 'raidboss_status'
        raidboss_cols = schema['raidboss_status']['columns']
        
        # Detectar coluna de ID do boss
        for candidate in ['boss_id', 'id', 'npc_id']:
            if candidate in raidboss_cols:
                config['raidboss_id_col'] = candidate
                break
        else:
            config['raidboss_id_col'] = 'id'  # fallback para Mobius
        
        # Detectar coluna de respawn (Mobius usa respawn_delay ou date_of_death)
        for candidate in ['respawn_time', 'respawnTime', 'respawn', 'next_respawn_time', 'respawn_delay', 'date_of_death']:
            if candidate in raidboss_cols:
                config['raidboss_respawn_col'] = candidate
                break
        else:
            config['raidboss_respawn_col'] = 'respawn_delay'  # fallback para Mobius
        
        print(f"   ✅ Tabela de raidboss: raidboss_status (ID: {config['raidboss_id_col']}, Respawn: {config['raidboss_respawn_col']})")
    else:
        config['has_raidboss_table'] = False
        config['raidboss_table_name'] = None
        config['raidboss_id_col'] = 'boss_id'
        config['raidboss_respawn_col'] = 'respawn_delay'
        print(f"   ⚠️  Tabela de raidboss não encontrada")
    
    # Detectar tabela de grandboss
    if 'grandboss_data' in schema:
        config['has_grandboss_table'] = True
        config['grandboss_table_name'] = 'grandboss_data'
        grandboss_cols = schema['grandboss_data']['columns']
        
        # Detectar coluna de ID
        for candidate in ['boss_id', 'bossId', 'id', 'npc_id']:
            if candidate in grandboss_cols:
                config['grandboss_id_col'] = candidate
                break
        else:
            config['grandboss_id_col'] = 'boss_id'
        
        # Detectar coluna de respawn
        for candidate in ['respawn_time', 'respawnTime', 'respawnDate', 'respawn_date']:
            if candidate in grandboss_cols:
                config['grandboss_respawn_col'] = candidate
                break
        else:
            config['grandboss_respawn_col'] = 'respawn_time'
        
        print(f"   ✅ Tabela de grandboss: grandboss_data (ID: {config['grandboss_id_col']}, Respawn: {config['grandboss_respawn_col']})")
    elif 'epic_boss_spawn' in schema:
        config['has_grandboss_table'] = True
        config['grandboss_table_name'] = 'epic_boss_spawn'
        grandboss_cols = schema['epic_boss_spawn']['columns']
        
        # Detectar coluna de ID
        for candidate in ['boss_id', 'bossId', 'id', 'npc_id']:
            if candidate in grandboss_cols:
                config['grandboss_id_col'] = candidate
                break
        else:
            config['grandboss_id_col'] = 'bossId'
        
        # Detectar coluna de respawn
        for candidate in ['respawn_time', 'respawnTime', 'respawnDate', 'respawn_date']:
            if candidate in grandboss_cols:
                config['grandboss_respawn_col'] = candidate
                break
        else:
            config['grandboss_respawn_col'] = 'respawnDate'
        
        print(f"   ✅ Tabela de grandboss: epic_boss_spawn (ID: {config['grandboss_id_col']}, Respawn: {config['grandboss_respawn_col']})")
    else:
        config['has_grandboss_table'] = False
        config['grandboss_table_name'] = None
        config['grandboss_id_col'] = 'boss_id'
        config['grandboss_respawn_col'] = 'respawn_time'
        print(f"   ⚠️  Tabela de grandboss não encontrada")
    
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
        'subpledge_filter': config.get('subpledge_filter', 'sub_pledge_id'),
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
        base_class_col=config['base_class_col'],
        clan_id_col=config.get('clan_id_col', 'clan_id'),
        crest_col=config.get('crest_col', 'crest_id'),
        clan_leader_col=config.get('clan_leader_col', 'leader_id'),
        has_raidboss_table=config.get('has_raidboss_table', False),
        raidboss_table_name=config.get('raidboss_table_name', 'raidboss_spawnlist'),
        raidboss_id_col=config.get('raidboss_id_col', 'boss_id'),
        raidboss_respawn_col=config.get('raidboss_respawn_col', 'respawn_time'),
        has_grandboss_table=config.get('has_grandboss_table', False),
        grandboss_table_name=config.get('grandboss_table_name', 'grandboss_data'),
        grandboss_id_col=config.get('grandboss_id_col', 'boss_id'),
        grandboss_respawn_col=config.get('grandboss_respawn_col', 'respawn_time'),
        castle_siege_date_col=config.get('castle_siege_date_col', 'siegeDate'),
        castle_treasury_col=config.get('castle_treasury_col', 'treasury')
    )
    
    print("   📝 Gerando classe LineageServices...")
    services_code = get_lineage_services_template(
        char_id=config['char_id'],
        has_subclass=config['has_subclass'],
        subclass_char_id=config['subclass_char_id'],
        base_class_col=config['base_class_col'],
        clan_structure=clan_structure,
        subclass_filter_base=config.get('subclass_filter_base', "isBase = '1'"),
        subclass_filter_sub=config.get('subclass_filter_sub', "isBase = '0'")
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
        access_level_column=config['access_level'],
        clan_structure=clan_structure
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
BASE_CLASS_COL = {config['base_class_col'] if config['base_class_col'] is None else f"'{config['base_class_col']}'"}      # classid, base_class ou class_id (None se não existe em characters)

# Tabela: character_subclasses
HAS_SUBCLASS = {config['has_subclass']}            # Se tem tabela de subclass
SUBCLASS_CHAR_ID = '{config['subclass_char_id']}'  # Coluna de ID na subclass

# Estrutura de Clans
CLAN_NAME_SOURCE = '{config['clan_name_source']}'  # clan_data, clan_subpledges ou clan_subpledges_simple
SUBPLEDGE_FILTER = '{config.get('subpledge_filter', 'sub_pledge_id')}'  # sub_pledge_id, type ou None
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
    print(f"   Coluna de classe: {config['base_class_col']}")
    print(f"   Access level: {config['access_level']}")
    print(f"   Tem subclass: {'Sim' if config['has_subclass'] else 'Não'}")
    print(f"   Nome do clan: {config['clan_name_source']}")
    if config.get('subpledge_filter'):
        print(f"   Filtro subpledge: {config['subpledge_filter']}")
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
