# Schemas de Banco de Dados L2

Este diretório contém os mapeamentos de schemas de bancos de dados Lineage 2.

## Estrutura de Arquivos

- `schema_*.yaml` ou `schema_*.json` - Schemas mapeados automaticamente
- `template_schema.yaml` - Template para criar mapeamentos manuais

## Schemas Suportados

### Detectados Automaticamente

O schema_mapper pode detectar automaticamente:

- **ACIS v1** - Usa `obj_Id` para characters
- **L2J Premium** - Usa `charId` para characters  
- **Classic** - Usa `char_id` para characters

### Como Usar

Coloque aqui os schemas mapeados de diferentes projetos L2 para facilitar a geração de arquivos de query.

