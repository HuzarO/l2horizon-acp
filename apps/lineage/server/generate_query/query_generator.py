"""
Query Generator - Gera arquivos query_*.py automaticamente baseado em schema mapeado
"""

import os
import sys
import yaml
import json
from typing import Dict, Any
from datetime import datetime
from classes import (
    get_lineage_stats_template,
    get_lineage_services_template,
    get_lineage_account_template,
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
        """Gera a classe LineageStats usando template"""
        char_id = self._get_char_id_column()
        access_level = self._get_access_level_column()
        has_subclass = self._has_subclass_table()
        subclass_char_id = self._get_subclass_char_id()
        clan_structure = self._get_clan_structure()
        
        return get_lineage_stats_template(char_id, access_level, has_subclass, 
                                          subclass_char_id, clan_structure)
    
    def generate_lineage_services_class(self) -> str:
        """Gera a classe LineageServices usando template"""
        char_id = self._get_char_id_column()
        has_subclass = self._has_subclass_table()
        subclass_char_id = self._get_subclass_char_id()
        return get_lineage_services_template(char_id, has_subclass, subclass_char_id)
    
    def _get_account_access_level_column(self) -> str:
        """Detecta o nome da coluna de nível de acesso na tabela accounts"""
        if 'accounts' in self.tables:
            columns = self.tables['accounts']['columns']
            for candidate in ['accessLevel', 'access_level', 'accesslevel']:
                if candidate in columns:
                    return candidate
        return 'accessLevel'  # fallback
    
    def generate_lineage_account_class(self) -> str:
        """Gera a classe LineageAccount usando template"""
        access_level_col = self._get_account_access_level_column()
        return get_lineage_account_template(access_level_col)
    
    def generate_transfer_wallet_to_char_class(self) -> str:
        """Gera a classe TransferFromWalletToChar usando template"""
        char_id = self._get_char_id_column()
        return get_transfer_wallet_to_char_template(char_id)
    
    def generate_transfer_char_to_wallet_class(self) -> str:
        """Gera a classe TransferFromCharToWallet usando template"""
        char_id = self._get_char_id_column()
        return get_transfer_char_to_wallet_template(char_id)
    
    def generate_lineage_marketplace_class(self) -> str:
        """Gera a classe LineageMarketplace usando template"""
        char_id = self._get_char_id_column()
        access_level_col = self._get_account_access_level_column()
        return get_lineage_marketplace_template(char_id, access_level_col)
    
    def generate_lineage_inflation_class(self) -> str:
        """Gera a classe LineageInflation usando template"""
        char_id = self._get_char_id_column()
        access_level = self._get_access_level_column()
        return get_lineage_inflation_template(char_id, access_level)
    
    def XXXgenerate_lineage_account_class_OLD_REMOVE_ME(self) -> str:
        """CÓDIGO ANTIGO - IGNORAR - SERÁ REMOVIDO"""
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
    @cache_lineage_result(timeout=300)
    def find_accounts_by_email(email):
        sql = """
            SELECT *
            FROM accounts
            WHERE email = :email
        """
        try:
            return LineageDB().select(sql, {"email": email})
        except:
            return []

    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_account_by_login_and_email(login, email):
        sql = """
            SELECT *
            FROM accounts
            WHERE login = :login AND email = :email
            LIMIT 1
        """
        try:
            result = LineageDB().select(sql, {"login": login, "email": email})
            return result[0] if result else None
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def link_account_to_user(login, user_uuid):
        try:
            sql = """
                UPDATE accounts
                SET linked_uuid = :uuid
                WHERE login = :login AND (linked_uuid IS NULL OR linked_uuid = '')
                LIMIT 1
            """
            params = {
                "uuid": str(user_uuid),
                "login": login
            }
            return LineageDB().update(sql, params)
        except Exception as e:
            print(f"Erro ao vincular conta Lineage a UUID: {e}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def unlink_account_from_user(login, user_uuid):
        """Desvincula uma conta do Lineage de um UUID de usuário."""
        try:
            sql = """
                UPDATE accounts
                SET linked_uuid = NULL
                WHERE login = :login
            """
            params = {"login": str(login).strip()}
            result = LineageDB().update(sql, params)
            return result is not None and result > 0
        except Exception as e:
            print(f"Erro ao desvincular conta Lineage do UUID: {e}")
            return False

    @staticmethod
    @cache_lineage_result(timeout=300)
    def ensure_columns():
        if LineageAccount._checked_columns:
            return

        lineage_db = LineageDB()
        
        if not lineage_db.enabled:
            LineageAccount._checked_columns = True
            return
            
        columns = lineage_db.get_table_columns("accounts")

        try:
            if "email" not in columns:
                sql = """
                    ALTER TABLE accounts
                    ADD COLUMN email VARCHAR(100) NOT NULL DEFAULT '';
                """
                if lineage_db.execute_raw(sql):
                    print("✅ Coluna 'email' adicionada com sucesso.")

            if "created_time" not in columns:
                sql = """
                    ALTER TABLE accounts
                    ADD COLUMN created_time INT(11) NULL DEFAULT NULL;
                """
                if lineage_db.execute_raw(sql):
                    print("✅ Coluna 'created_time' adicionada com sucesso.")

            if "linked_uuid" not in columns:
                sql = """
                    ALTER TABLE accounts
                    ADD COLUMN linked_uuid VARCHAR(36) NULL DEFAULT NULL;
                """
                if lineage_db.execute_raw(sql):
                    print("✅ Coluna 'linked_uuid' adicionada com sucesso.")

            LineageAccount._checked_columns = True

        except Exception as e:
            print(f"❌ Erro ao alterar tabela 'accounts': {e}")

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def check_login_exists(login):
        sql = "SELECT * FROM accounts WHERE login = :login LIMIT 1"
        return LineageDB().select(sql, {"login": login})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def check_email_exists(email):
        sql = "SELECT login, email FROM accounts WHERE email = :email"
        return LineageDB().select(sql, {"email": email})

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def register(login, password, access_level, email):
        try:
            LineageAccount.ensure_columns()
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

    @staticmethod
    @cache_lineage_result(timeout=300)
    def update_password(password, login):
        try:
            hashed = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
            sql = """
                UPDATE accounts SET password = :password
                WHERE login = :login LIMIT 1
            """
            params = {
                "password": hashed,
                "login": login
            }
            LineageDB().update(sql, params)
            return True
        except Exception as e:
            print(f"Erro ao atualizar senha: {e}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def update_password_group(password, logins_list):
        if not logins_list:
            return None
        try:
            hashed = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
            sql = "UPDATE accounts SET password = :password WHERE login IN :logins"
            params = {
                "password": hashed,
                "logins": logins_list
            }
            LineageDB().update(sql, params)
            return True
        except Exception as e:
            print(f"Erro ao atualizar senhas em grupo: {e}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def update_access_level(access, login):
        try:
            sql = """
                UPDATE accounts SET accessLevel = :access
                WHERE login = :login LIMIT 1
            """
            params = {
                "access": access,
                "login": login
            }
            return LineageDB().update(sql, params)
        except Exception as e:
            print(f"Erro ao atualizar accessLevel: {e}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def validate_credentials(login, password):
        try:
            sql = "SELECT password FROM accounts WHERE login = :login LIMIT 1"
            result = LineageDB().select(sql, {"login": login})

            if not result:
                return False

            hashed_input = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
            stored_hash = result[0]['password']
            return hashed_input == stored_hash

        except Exception as e:
            print(f"Erro ao verificar senha: {e}")
            return False


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

