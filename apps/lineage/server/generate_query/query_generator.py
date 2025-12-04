"""
Query Generator - Gera arquivos query_*.py automaticamente baseado em schema mapeado
"""

import os
import sys
import yaml
import json
from typing import Dict, Any
from datetime import datetime
from class_templates import (
    get_lineage_services_template,
    get_transfer_wallet_to_char_template,
    get_transfer_char_to_wallet_template,
    get_lineage_marketplace_template,
    get_lineage_inflation_template
)


class QueryGenerator:
    """
    Gera arquivos de query Python baseado em um schema YAML/JSON mapeado
    """
    
    def __init__(self, schema_file: str):
        self.schema_file = schema_file
        self.schema = self._load_schema()
        self.database_type = self.schema.get('database_type', 'custom')
        self.tables = self.schema.get('tables', {})
    
    def _load_schema(self) -> Dict[str, Any]:
        """Carrega o arquivo de schema (YAML ou JSON)"""
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                if self.schema_file.endswith('.yaml') or self.schema_file.endswith('.yml'):
                    return yaml.safe_load(f)
                elif self.schema_file.endswith('.json'):
                    return json.load(f)
                else:
                    raise ValueError("Formato de arquivo não suportado. Use .yaml ou .json")
        except Exception as e:
            print(f"❌ Erro ao carregar schema: {e}")
            sys.exit(1)
    
    def _get_char_id_column(self) -> str:
        """Detecta o nome da coluna de ID do personagem"""
        if 'characters' in self.tables:
            columns = self.tables['characters']['columns']
            for candidate in ['obj_Id', 'charId', 'char_id', 'id']:
                if candidate in columns:
                    return candidate
        return 'obj_Id'  # fallback
    
    def _get_access_level_column(self) -> str:
        """Detecta o nome da coluna de nível de acesso"""
        if 'characters' in self.tables:
            columns = self.tables['characters']['columns']
            for candidate in ['accesslevel', 'accessLevel', 'access_level']:
                if candidate in columns:
                    return candidate
        return 'accesslevel'  # fallback
    
    def _has_subclass_table(self) -> bool:
        """Verifica se existe tabela de subclasses"""
        return 'character_subclasses' in self.tables
    
    def _get_subclass_char_id(self) -> str:
        """Detecta o nome da coluna de ID do personagem na tabela de subclasses"""
        if 'character_subclasses' in self.tables:
            columns = self.tables['character_subclasses']['columns']
            for candidate in ['char_obj_id', 'charId', 'char_id']:
                if candidate in columns:
                    return candidate
        return 'char_obj_id'  # fallback
    
    def _get_clan_structure(self) -> Dict[str, str]:
        """Detecta a estrutura das tabelas de clan"""
        structure = {
            'has_subpledges': 'clan_subpledges' in self.tables,
            'clan_name_source': 'clan_data',  # ou clan_subpledges
            'ally_name_column': 'ally_name'
        }
        
        # Verifica se clan_data tem o campo name diretamente
        if 'clan_data' in self.tables:
            columns = self.tables['clan_data']['columns']
            if 'clan_name' in columns or 'name' in columns:
                structure['clan_name_source'] = 'clan_data'
            else:
                structure['clan_name_source'] = 'clan_subpledges'
        
        return structure
    
    def generate_header(self) -> str:
        """Gera o cabeçalho do arquivo"""
        return f'''"""
Query File: query_{self.database_type}.py
Generated automatically by Query Generator
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database Type: {self.database_type}
"""

from apps.lineage.server.database import LineageDB
from apps.lineage.server.utils.cache import cache_lineage_result

import time
import base64
import hashlib


'''
    
    def generate_lineage_stats_class(self) -> str:
        """Gera a classe LineageStats com todos os métodos de estatísticas"""
        char_id = self._get_char_id_column()
        access_level = self._get_access_level_column()
        has_subclass = self._has_subclass_table()
        subclass_char_id = self._get_subclass_char_id()
        clan_structure = self._get_clan_structure()
        
        # Determinar como fazer JOIN com clan
        if clan_structure['clan_name_source'] == 'clan_data':
            clan_join = """
            LEFT JOIN clan_data D ON D.clan_id = C.clanid"""
            clan_name_field = "D.clan_name"
            ally_field = "D.ally_id"
        else:
            clan_join = """
            LEFT JOIN clan_subpledges D ON D.clan_id = C.clanid AND D.sub_pledge_id = 0
            LEFT JOIN clan_data CD ON CD.clan_id = C.clanid"""
            clan_name_field = "D.name AS clan_name"
            ally_field = "CD.ally_id"
        
        # Subclass JOIN
        subclass_join = ""
        level_source = "C.level"
        if has_subclass:
            subclass_join = f"""
            LEFT JOIN character_subclasses CS ON CS.{subclass_char_id} = C.{char_id} AND CS.class_index = 0"""
            level_source = "CS.level"
        
        code = f'''class LineageStats:

    @staticmethod
    def _run_query(sql, params=None, use_cache=True):
        return LineageDB().select(sql, params=params, use_cache=use_cache)
    
    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_crests(ids, type='clan'):
        if not ids:
            return []

        table = 'clan_data'
        id_column = 'clan_id'
        crest_column = 'crest_id'

        sql = f"""
            SELECT {{id_column}}, {{crest_column}}
            FROM {{table}}
            WHERE {{id_column}} IN :ids
        """
        return LineageStats._run_query(sql, {{"ids": tuple(ids)}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def players_online():
        sql = "SELECT COUNT(*) AS quant FROM characters WHERE online > 0 AND {access_level} = '0'"
        return LineageStats._run_query(sql)
    
    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_pvp(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime,
                {level_source},
                C.classid AS base,
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY pvpkills DESC, pkkills DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_pk(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime,
                {level_source},
                C.classid AS base,
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY pkkills DESC, pvpkills DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_online(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime,
                {level_source},
                C.classid AS base,
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY onlinetime DESC, pvpkills DESC, pkkills DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_level(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime, 
                {level_source},
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY {level_source} DESC, C.onlinetime DESC, C.char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_adena(limit=10, adn_billion_item=0, value_item=1000000):
        item_bonus_sql = ""
        if adn_billion_item != 0:
            item_bonus_sql = f"""
                IFNULL((SELECT SUM(I2.count) * :value_item
                        FROM items I2
                        WHERE I2.owner_id = C.{char_id} AND I2.item_id = :adn_billion_item
                        GROUP BY I2.owner_id), 0) +
            """
        sql = f"""
            SELECT 
                C.char_name, 
                C.online, 
                C.onlinetime, 
                {level_source}, 
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                (
                    {{item_bonus_sql}}
                    IFNULL((SELECT SUM(I1.count)
                            FROM items I1
                            WHERE I1.owner_id = C.{char_id} AND I1.item_id = '57'
                            GROUP BY I1.owner_id), 0)
                ) AS adenas
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY adenas DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{
            "limit": limit,
            "adn_billion_item": adn_billion_item,
            "value_item": value_item
        }})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_clans(limit=10):
        sql = """
            SELECT 
                C.clan_id, 
                C.clan_name, 
                C.clan_level, 
                C.reputation_score, 
                C.ally_name,
                C.ally_id,
                P.char_name, 
                (SELECT COUNT(*) FROM characters WHERE clanid = C.clan_id) AS membros
            FROM clan_data C
            LEFT JOIN characters P ON P.{char_id} = C.leader_id
            ORDER BY C.clan_level DESC, C.reputation_score DESC, membros DESC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_ranking():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                C.classid AS base, 
                O.olympiad_points
            FROM olympiad_nobles O
            LEFT JOIN characters C ON C.{char_id} = O.char_id{clan_join}
            ORDER BY olympiad_points DESC, base ASC, char_name ASC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_all_heroes():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                {clan_name_field}, 
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                C.classid AS base, 
                H.count
            FROM heroes H
            LEFT JOIN characters C ON C.{char_id} = H.char_id{clan_join}
            WHERE H.played > 0 AND H.count > 0
            ORDER BY H.count DESC, base ASC, char_name ASC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_current_heroes():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                C.classid AS base
            FROM heroes H
            LEFT JOIN characters C ON C.{char_id} = H.char_id{clan_join}
            WHERE H.played > 0 AND H.count > 0
            ORDER BY base ASC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def grandboss_status():
        sql = """
            SELECT boss_id, respawn_time AS respawn
            FROM grandboss_data
            ORDER BY respawn_time DESC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def siege():
        sql = """
            SELECT 
                W.id, 
                W.name, 
                W.siegeDate AS sdate, 
                W.treasury AS stax,
                P.char_name, 
                C.clan_name,
                C.clan_id,
                C.ally_id,
                C.ally_name
            FROM castle W
            LEFT JOIN clan_data C ON C.hasCastle = W.id
            LEFT JOIN characters P ON P.{char_id} = C.leader_id
        """
        return LineageStats._run_query(sql)


'''
        return code
    
    def generate_lineage_services_class(self) -> str:
        """Gera a classe LineageServices"""
        char_id = self._get_char_id_column()
        return get_lineage_services_template(char_id)
    
    def generate_transfer_wallet_to_char_class(self) -> str:
        """Gera a classe TransferFromWalletToChar"""
        char_id = self._get_char_id_column()
        return get_transfer_wallet_to_char_template(char_id)
    
    def generate_transfer_char_to_wallet_class(self) -> str:
        """Gera a classe TransferFromCharToWallet"""
        char_id = self._get_char_id_column()
        return get_transfer_char_to_wallet_template(char_id)
    
    def generate_lineage_marketplace_class(self) -> str:
        """Gera a classe LineageMarketplace"""
        char_id = self._get_char_id_column()
        return get_lineage_marketplace_template(char_id)
    
    def generate_lineage_inflation_class(self) -> str:
        """Gera a classe LineageInflation"""
        char_id = self._get_char_id_column()
        access_level = self._get_access_level_column()
        return get_lineage_inflation_template(char_id, access_level)
    
    def generate_lineage_account_class(self) -> str:
        """Gera a classe LineageAccount"""
        return '''
class LineageAccount:
    _checked_columns = False

    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_acess_level():
        return 'accessLevel'

    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_account_by_login(login):
        sql = """
            SELECT *
            FROM accounts
            WHERE login = :login
            LIMIT 1
        """
        try:
            result = LineageDB().select(sql, {"login": login})
            return result[0] if result else None
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def register(login, password, access_level, email):
        try:
            hashed = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
            sql = """
                INSERT INTO accounts (login, password, accessLevel, email, created_time)
                VALUES (:login, :password, :access_level, :email, :created_time)
            """
            params = {
                "login": login,
                "password": hashed,
                "access_level": access_level,
                "email": email,
                "created_time": int(time.time())
            }
            LineageDB().insert(sql, params)
            return True
        except Exception as e:
            print(f"Erro ao registrar conta: {e}")
            return None


'''
    
    def generate_file(self, output_file: str = None, output_dir: str = None):
        """Gera o arquivo query_*.py completo com TODAS as 7 classes"""
        if output_file is None:
            output_file = f"query_{self.database_type}.py"
        
        print(f"🔨 Gerando arquivo: {output_file}")
        print(f"📋 Gerando 7 classes completas...")
        
        content = self.generate_header()
        content += self.generate_lineage_stats_class()
        content += self.generate_lineage_services_class()
        content += self.generate_lineage_account_class()
        content += self.generate_transfer_wallet_to_char_class()
        content += self.generate_transfer_char_to_wallet_class()
        content += self.generate_lineage_marketplace_class()
        content += self.generate_lineage_inflation_class()
        
        # Determinar diretório de saída
        if output_dir is None:
            # Por padrão, gera em ../querys/ (um nível acima de generate_query)
            # Se estamos em generate_query/schemas/, subir 2 níveis
            current_dir = os.path.dirname(os.path.abspath(self.schema_file))
            if current_dir.endswith('schemas'):
                output_dir = os.path.join(current_dir, '..', '..', 'querys')
            else:
                output_dir = os.path.join(current_dir, '..', 'querys')
        
        # Criar diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Caminho completo do arquivo
        output_path = os.path.join(output_dir, output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Arquivo gerado com sucesso!")
            print(f"📁 Local: {os.path.abspath(output_path)}")
            print(f"📊 Database Type: {self.database_type}")
            print(f"📋 Classes geradas (7 no total):")
            print("   1. LineageStats - Rankings e estatísticas")
            print("   2. LineageServices - Serviços de personagens")
            print("   3. LineageAccount - Gerenciamento de contas")
            print("   4. TransferFromWalletToChar - Wallet → Char")
            print("   5. TransferFromCharToWallet - Char → Wallet")
            print("   6. LineageMarketplace - Sistema de marketplace")
            print("   7. LineageInflation - Análise de inflação")
            print("\n💡 Próximo passo: Revise o arquivo gerado e ajuste conforme necessário")
            
            return output_path
        except Exception as e:
            print(f"❌ Erro ao gerar arquivo: {e}")
            return None


def main():
    """Função principal"""
    print("="*70)
    print("🏗️  QUERY GENERATOR - Lineage 2")
    print("="*70)
    print()
    
    if len(sys.argv) < 2:
        print("❌ Uso: python query_generator.py <schema_file.yaml>")
        print("\n💡 Exemplo:")
        print("   python query_generator.py schemas/schema_acis_v1.yaml")
        sys.exit(1)
    
    schema_file = sys.argv[1]
    
    if not os.path.exists(schema_file):
        print(f"❌ Arquivo não encontrado: {schema_file}")
        sys.exit(1)
    
    generator = QueryGenerator(schema_file)
    generator.generate_file()
    
    print("\n" + "="*70)
    print("✅ Geração concluída!")
    print("="*70)


if __name__ == '__main__':
    main()

