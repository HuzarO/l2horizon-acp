#!/usr/bin/env python
"""
Script de Automação - Gerar Query Automaticamente
Executa o mapeamento e geração em um único comando

Estrutura:
- generate_query/ - Ferramentas (este arquivo)
- generate_query/schemas/ - Schemas mapeados
- querys/ - Arquivos query_*.py gerados
"""

import sys
import os
from pathlib import Path

# Adicionar ao path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent.parent.parent))
sys.path.insert(0, str(current_dir))

from schema_mapper import SchemaMapper
from query_generator import QueryGenerator


def print_banner():
    print("\n" + "="*70)
    print("🚀 GERADOR AUTOMÁTICO DE QUERIES L2")
    print("="*70)
    print("📁 Ferramentas: generate_query/")
    print("📁 Saída: querys/")
    print("="*70 + "\n")


def print_step(step_num, description):
    print(f"\n{'='*70}")
    print(f"📍 PASSO {step_num}: {description}")
    print("="*70 + "\n")


def main():
    print_banner()
    
    # Verificar se deve usar schema existente ou mapear novo
    use_existing = False
    schema_file = None
    
    if len(sys.argv) > 1:
        schema_file = sys.argv[1]
        if os.path.exists(schema_file):
            use_existing = True
            print(f"✅ Usando schema existente: {schema_file}\n")
        else:
            print(f"❌ Arquivo não encontrado: {schema_file}")
            print("💡 Continuando com mapeamento automático...\n")
    
    # PASSO 1: Mapear o banco de dados
    if not use_existing:
        print_step(1, "Mapeando o Banco de Dados")
        
        try:
            mapper = SchemaMapper()
            schema = mapper.map_database_schema()
            mapper.print_schema_summary()
            
            # Criar diretório schemas
            schemas_dir = current_dir / 'schemas'
            schemas_dir.mkdir(exist_ok=True)
            
            # Salvar schema
            schema_type = schema.get('database_type', 'unknown')
            schema_file = schemas_dir / f'schema_{schema_type}.yaml'
            
            mapper.save_schema_to_yaml(str(schema_file))
            mapper.save_schema_to_json(str(schema_file).replace('.yaml', '.json'))
            
            print(f"\n✅ Schema mapeado e salvo!")
            
        except Exception as e:
            print(f"\n❌ Erro ao mapear banco de dados: {e}")
            print("\n💡 Você pode criar um mapeamento manual:")
            print(f"   1. Copie: schemas/template_schema.yaml")
            print(f"   2. Edite conforme seu banco")
            print(f"   3. Execute: python gerar_query.py schemas/seu_schema.yaml")
            sys.exit(1)
    
    # PASSO 2: Gerar arquivo de query
    print_step(2, "Gerando Arquivo de Query")
    
    try:
        generator = QueryGenerator(str(schema_file))
        
        # Nome do arquivo de saída
        output_file = f"query_{generator.database_type}.py"
        
        # Diretório de saída (../querys/)
        querys_dir = current_dir.parent / 'querys'
        output_path = querys_dir / output_file
        
        # Verificar se arquivo já existe
        if output_path.exists():
            print(f"⚠️  Arquivo {output_file} já existe em querys/!")
            response = input("   Deseja sobrescrever? (s/N): ").strip().lower()
            if response not in ['s', 'sim', 'y', 'yes']:
                print("\n❌ Operação cancelada pelo usuário")
                sys.exit(0)
            
            # Fazer backup
            backup_file = output_path.with_suffix('.backup.py')
            if output_path.exists():
                import shutil
                shutil.copy2(output_path, backup_file)
                print(f"   📦 Backup criado: {backup_file.name}")
        
        # Gerar arquivo em querys/
        generated_path = generator.generate_file(output_file, output_dir=str(querys_dir))
        
        if generated_path is None:
            raise Exception("Falha ao gerar arquivo")
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar arquivo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # PASSO 3: Resumo final
    print_step(3, "Resumo e Próximos Passos")
    
    print("✅ Processo concluído com sucesso!\n")
    print("📂 Arquivos gerados:")
    print(f"   - Schema:  generate_query/schemas/schema_{generator.database_type}.yaml")
    print(f"   - Query:   querys/{output_file}\n")
    
    print("🎯 Próximos passos:")
    print("   1. Revise o arquivo gerado:")
    print(f"      code querys/{output_file}\n")
    print("   2. Teste as queries:")
    print(f"      from apps.lineage.server.querys.{output_file[:-3]} import LineageStats")
    print("      result = LineageStats.players_online()")
    print("      print(result)\n")
    print("   3. Integre em suas views:")
    print(f"      from apps.lineage.server.querys.{output_file[:-3]} import LineageStats, LineageAccount\n")
    
    print("="*70)
    print("🎉 Tudo pronto! Boa sorte com seu servidor L2!")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

