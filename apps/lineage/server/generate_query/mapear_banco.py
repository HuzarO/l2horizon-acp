#!/usr/bin/env python
"""
Script para mapear banco de dados com configuração customizada
Permite conectar em diferentes bancos sem alterar database.py
"""

import sys
import os
from pathlib import Path
import yaml

# Adicionar ao path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent.parent.parent))


def mapear_tabela_custom(connection, table_name):
    """Mapeia uma tabela usando conexão customizada"""
    try:
        cursor = connection.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        result = cursor.fetchall()
        
        columns = {}
        primary_key = None
        
        for row in result:
            col_name = row[0]  # Field
            col_type = row[1]  # Type
            col_key = row[3] if len(row) > 3 else ''  # Key
            
            columns[col_name] = str(col_type)
            
            if col_key == 'PRI' and primary_key is None:
                primary_key = col_name
        
        cursor.close()
        return columns, primary_key
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return {}, None


def detectar_tipo_schema(tabelas_mapeadas):
    """Detecta o tipo de schema"""
    if 'characters' not in tabelas_mapeadas:
        return 'unknown'
    
    char_columns = tabelas_mapeadas['characters']['columns']
    
    if 'obj_Id' in char_columns:
        return 'acis'
    elif 'charId' in char_columns:
        if 'base_class' in char_columns:
            return 'mobius'
        else:
            return 'l2jpremium'
    elif 'char_id' in char_columns:
        return 'classic'
    
    return 'custom'


def main():
    print("\n" + "="*70)
    print("🔍 MAPEADOR CUSTOMIZADO - Conectar em Qualquer Banco")
    print("="*70)
    print()
    
    # Solicitar configurações
    print("📋 Digite as configurações do banco:")
    print()
    
    host = input("  Host [localhost]: ").strip() or "localhost"
    port = input("  Porta [3306]: ").strip() or "3306"
    database = input("  Database: ").strip()
    user = input("  Usuário [root]: ").strip() or "root"
    password = input("  Senha: ").strip()
    
    if not database:
        print("\n❌ Database é obrigatório!")
        sys.exit(1)
    
    nome_schema = input("\n  Nome para salvar schema [auto]: ").strip()
    if not nome_schema:
        nome_schema = database.lower()
    
    # Conectar
    print("\n" + "="*70)
    print("📡 Conectando ao banco...")
    print("="*70)
    print()
    
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        print(f"✅ Conectado em: {user}@{host}:{port}/{database}\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}\n")
        sys.exit(1)
    
    # Mapear tabelas
    tabelas_importantes = [
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
    
    print("="*70)
    print(f"📊 Mapeando {len(tabelas_importantes)} tabelas...")
    print("="*70)
    print()
    
    schema_data = {}
    
    for table_name in tabelas_importantes:
        print(f"📋 {table_name:25} ", end='', flush=True)
        columns, pk = mapear_tabela_custom(connection, table_name)
        
        if columns:
            schema_data[table_name] = {
                'columns': columns,
                'primary_key': pk or 'id'
            }
            print(f"✅ {len(columns):2} colunas")
        else:
            print(f"⚠️  Não encontrada")
    
    connection.close()
    
    if not schema_data:
        print("\n❌ Nenhuma tabela foi mapeada!")
        sys.exit(1)
    
    # Detectar tipo
    tipo_detectado = detectar_tipo_schema(schema_data)
    
    print("\n" + "="*70)
    print("🔍 ANÁLISE DO SCHEMA")
    print("="*70)
    print()
    
    print(f"🎯 Tipo detectado: {tipo_detectado.upper()}\n")
    
    # Mostrar detalhes
    if 'characters' in schema_data:
        char_cols = schema_data['characters']['columns']
        print("📌 Tabela characters:")
        print(f"   └─ PK: {schema_data['characters']['primary_key']}")
        print(f"   └─ Total: {len(char_cols)} colunas")
        
        if 'obj_Id' in char_cols:
            print(f"   └─ ID: obj_Id (ACIS)")
        elif 'charId' in char_cols:
            print(f"   └─ ID: charId (L2J/Mobius)")
        elif 'char_id' in char_cols:
            print(f"   └─ ID: char_id (Classic)")
        
        if 'classid' in char_cols:
            print(f"   └─ Classe: classid")
        elif 'base_class' in char_cols:
            print(f"   └─ Classe: base_class (Mobius)")
        
        for col in ['accesslevel', 'accessLevel', 'access_level']:
            if col in char_cols:
                print(f"   └─ Access: {col}")
                break
    
    if 'accounts' in schema_data:
        acc_cols = schema_data['accounts']['columns']
        print("\n📌 Tabela accounts:")
        print(f"   └─ Total: {len(acc_cols)} colunas")
        
        for col in ['accessLevel', 'access_level', 'accesslevel']:
            if col in acc_cols:
                print(f"   └─ Access: {col}")
                break
    
    # Salvar schema
    print("\n" + "="*70)
    print("💾 SALVANDO SCHEMA")
    print("="*70)
    print()
    
    # Detectar configurações
    has_subclass = 'character_subclasses' in schema_data
    clan_name_in_subpledges = 'clan_data' in schema_data and 'clan_name' not in schema_data['clan_data']['columns']
    
    char_id_col = schema_data['characters']['primary_key'] if 'characters' in schema_data else 'obj_Id'
    
    access_level_col = 'accesslevel'
    if 'characters' in schema_data:
        for candidate in ['accesslevel', 'accessLevel', 'access_level']:
            if candidate in schema_data['characters']['columns']:
                access_level_col = candidate
                break
    
    base_class_col = 'classid'
    if 'characters' in schema_data:
        for candidate in ['classid', 'base_class', 'class_id']:
            if candidate in schema_data['characters']['columns']:
                base_class_col = candidate
                break
    
    schema_final = {
        'database_type': nome_schema,
        'tables': {}
    }
    
    for table_name, table_data in schema_data.items():
        schema_final['tables'][table_name] = {
            'columns': table_data['columns'],
            'primary_key': table_data['primary_key']
        }
    
    schema_final['config'] = {
        'has_subclass_table': has_subclass,
        'clan_name_in_subpledges': clan_name_in_subpledges,
        'custom_columns': {
            'char_id_column': char_id_col,
            'access_level_column': access_level_col,
            'base_class_column': base_class_col
        }
    }
    
    # Salvar
    output_file = current_dir / 'schemas' / f'schema_{nome_schema}.yaml'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(schema_final, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✅ Schema salvo: {output_file.name}")
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO")
    print("="*70)
    print(f"""
✅ Tipo detectado: {tipo_detectado}
✅ Nome do schema: {nome_schema}
✅ Tabelas mapeadas: {len(schema_data)}
✅ Arquivo: schemas/schema_{nome_schema}.yaml

📋 Configurações:
   • ID: {char_id_col}
   • Classe: {base_class_col}
   • Access level: {access_level_col}
   • Subclasses: {'SIM' if has_subclass else 'NÃO'}
   • Clan name em subpledges: {'SIM' if clan_name_in_subpledges else 'NÃO'}

🎯 Próximo passo:
   python query_generator.py schemas/schema_{nome_schema}.yaml
""")
    
    print("="*70)
    print("✅ Mapeamento concluído!")
    print("="*70)
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

