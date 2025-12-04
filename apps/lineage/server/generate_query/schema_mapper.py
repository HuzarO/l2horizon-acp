"""
Schema Mapper para Bancos de Dados do Lineage 2
Ferramenta para mapear automaticamente a estrutura de tabelas e colunas do banco de dados L2
"""

import sys
import os
from typing import Dict, List, Any
import yaml
import json

# Adicionar o path do projeto para importar LineageDB
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from apps.lineage.server.database import LineageDB


class SchemaMapper:
    """
    Mapeia o schema de um banco de dados L2 para gerar arquivos de query automaticamente
    """
    
    def __init__(self):
        self.db = LineageDB()
        self.schema = {}
    
    def get_table_columns(self, table_name: str) -> Dict[str, str]:
        """Obtém todas as colunas de uma tabela com seus tipos"""
        try:
            sql = f"SHOW COLUMNS FROM {table_name}"
            result = self.db.select(sql, use_cache=False)
            
            columns = {}
            for row in result:
                col_name = row.get('Field') or row.get('field')
                col_type = row.get('Type') or row.get('type')
                columns[col_name] = col_type
            
            return columns
        except Exception as e:
            print(f"⚠️  Erro ao buscar colunas da tabela {table_name}: {e}")
            return {}
    
    def get_all_tables(self) -> List[str]:
        """Lista todas as tabelas do banco de dados"""
        try:
            sql = "SHOW TABLES"
            result = self.db.select(sql, use_cache=False)
            
            tables = []
            for row in result:
                # O nome da coluna pode variar dependendo do banco
                table_name = list(row.values())[0] if isinstance(row, dict) else row[0]
                tables.append(table_name)
            
            return tables
        except Exception as e:
            print(f"❌ Erro ao listar tabelas: {e}")
            return []
    
    def map_database_schema(self, important_tables: List[str] = None) -> Dict[str, Any]:
        """
        Mapeia o schema completo do banco de dados
        
        Args:
            important_tables: Lista de tabelas importantes a mapear. Se None, mapeia todas.
        
        Returns:
            Dicionário com o schema mapeado
        """
        if important_tables is None:
            important_tables = [
                'characters',
                'character_subclasses',
                'accounts',
                'clan_data',
                'clan_subpledges',
                'items',
                'olympiad_nobles',
                'heroes',
                'grandboss_data',
                'raidboss_spawnlist',
                'castle',
                'siege_clans'
            ]
        
        print("🔍 Iniciando mapeamento do banco de dados...")
        print(f"📋 Tabelas a mapear: {len(important_tables)}\n")
        
        schema = {
            'database_type': 'unknown',
            'tables': {}
        }
        
        all_tables = self.get_all_tables()
        
        for table_name in important_tables:
            if table_name not in all_tables:
                print(f"⚠️  Tabela '{table_name}' não encontrada no banco")
                continue
            
            print(f"📊 Mapeando tabela: {table_name}")
            columns = self.get_table_columns(table_name)
            
            if columns:
                schema['tables'][table_name] = {
                    'columns': columns,
                    'primary_key': self._detect_primary_key(table_name, columns)
                }
                print(f"   ✅ {len(columns)} colunas mapeadas")
            else:
                print(f"   ❌ Falha ao mapear")
        
        # Detectar tipo de schema baseado nas colunas
        schema['database_type'] = self._detect_schema_type(schema['tables'])
        
        self.schema = schema
        return schema
    
    def _detect_primary_key(self, table_name: str, columns: Dict[str, str]) -> str:
        """Detecta a chave primária mais provável da tabela"""
        # Heurística para detectar PK comum em L2
        pk_candidates = {
            'characters': ['obj_Id', 'charId', 'char_id'],
            'accounts': ['login', 'account_name'],
            'clan_data': ['clan_id'],
            'items': ['object_id'],
        }
        
        if table_name in pk_candidates:
            for candidate in pk_candidates[table_name]:
                if candidate in columns:
                    return candidate
        
        # Fallback: procura por colunas comuns de PK
        for common_pk in ['id', 'obj_Id', 'charId', 'object_id']:
            if common_pk in columns:
                return common_pk
        
        return list(columns.keys())[0] if columns else 'id'
    
    def _detect_schema_type(self, tables: Dict[str, Any]) -> str:
        """
        Detecta o tipo de schema baseado nas colunas das tabelas
        
        Returns:
            String identificando o tipo: 'acis_v1', 'l2jpremium', 'classic', etc.
        """
        if 'characters' not in tables:
            return 'unknown'
        
        char_columns = tables['characters']['columns']
        
        # ACIS usa obj_Id
        if 'obj_Id' in char_columns:
            return 'acis_v1'
        
        # L2J Premium usa charId
        elif 'charId' in char_columns:
            return 'l2jpremium'
        
        # Interlude clássico geralmente usa char_id
        elif 'char_id' in char_columns:
            return 'classic'
        
        return 'unknown'
    
    def save_schema_to_yaml(self, output_file: str):
        """Salva o schema mapeado em arquivo YAML"""
        if not self.schema:
            print("❌ Nenhum schema foi mapeado ainda. Execute map_database_schema() primeiro.")
            return
        
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.schema, f, default_flow_style=False, allow_unicode=True)
            
            print(f"\n✅ Schema salvo em: {output_file}")
            print(f"📦 Tipo detectado: {self.schema['database_type']}")
            print(f"📊 Tabelas mapeadas: {len(self.schema['tables'])}")
        except Exception as e:
            print(f"❌ Erro ao salvar schema: {e}")
    
    def save_schema_to_json(self, output_file: str):
        """Salva o schema mapeado em arquivo JSON"""
        if not self.schema:
            print("❌ Nenhum schema foi mapeado ainda. Execute map_database_schema() primeiro.")
            return
        
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.schema, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Schema salvo em: {output_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar schema: {e}")
    
    def print_schema_summary(self):
        """Imprime um resumo do schema mapeado"""
        if not self.schema:
            print("❌ Nenhum schema foi mapeado ainda.")
            return
        
        print("\n" + "="*70)
        print("📊 RESUMO DO SCHEMA MAPEADO")
        print("="*70)
        print(f"\n🔧 Tipo de Schema: {self.schema['database_type']}")
        print(f"📦 Total de Tabelas: {len(self.schema['tables'])}\n")
        
        for table_name, table_info in self.schema['tables'].items():
            columns = table_info['columns']
            pk = table_info.get('primary_key', '?')
            print(f"📋 {table_name}")
            print(f"   └─ PK: {pk}")
            print(f"   └─ Colunas: {len(columns)}")
            
            # Mostrar algumas colunas importantes
            important_cols = [col for col in columns.keys() if any(
                key in col.lower() for key in ['id', 'name', 'level', 'online']
            )]
            if important_cols:
                print(f"   └─ Principais: {', '.join(important_cols[:5])}")
            print()


def main():
    """Função principal para executar o mapeamento"""
    print("="*70)
    print("🗺️  SCHEMA MAPPER - Lineage 2 Database")
    print("="*70)
    print()
    
    mapper = SchemaMapper()
    
    # Mapear o schema
    schema = mapper.map_database_schema()
    
    # Mostrar resumo
    mapper.print_schema_summary()
    
    # Criar diretório schemas se não existir
    schemas_dir = os.path.join(os.path.dirname(__file__), 'schemas')
    os.makedirs(schemas_dir, exist_ok=True)
    
    # Salvar em YAML e JSON
    schema_type = schema.get('database_type', 'unknown')
    yaml_file = os.path.join(schemas_dir, f'schema_{schema_type}.yaml')
    json_file = os.path.join(schemas_dir, f'schema_{schema_type}.json')
    
    mapper.save_schema_to_yaml(yaml_file)
    mapper.save_schema_to_json(json_file)
    
    print("\n" + "="*70)
    print("✅ Mapeamento concluído!")
    print("="*70)
    print("\n💡 Próximos passos:")
    print("   1. Revise os arquivos gerados em: querys/schemas/")
    print("   2. Execute: python query_generator.py schema_{tipo}.yaml")
    print("   3. Um novo arquivo query_*.py será gerado automaticamente\n")


if __name__ == '__main__':
    main()

