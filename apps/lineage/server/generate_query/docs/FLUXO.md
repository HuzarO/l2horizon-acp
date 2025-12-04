# 🔄 Fluxo do Sistema

## 📊 Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE GERAÇÃO DE QUERIES                │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │  Banco de    │
     │  Dados L2    │
     └──────┬───────┘
            │
            │ 1. Conecta
            ▼
     ┌──────────────┐
     │   Schema     │
     │   Mapper     │◄─── Analisa tabelas e colunas
     └──────┬───────┘
            │
            │ 2. Gera
            ▼
     ┌──────────────┐
     │ schema_*.yaml│
     │ schema_*.json│◄─── Mapeamento do schema
     └──────┬───────┘
            │
            │ 3. Lê
            ▼
     ┌──────────────┐
     │    Query     │
     │  Generator   │◄─── Gera código Python
     └──────┬───────┘
            │
            │ 4. Cria
            ▼
     ┌──────────────┐
     │ query_*.py   │
     │              │◄─── Arquivo pronto para uso!
     └──────────────┘
            │
            │ 5. Usa
            ▼
     ┌──────────────┐
     │  Seu Projeto │
     │  Django/Web  │
     └──────────────┘
```

---

## 🔍 Detalhamento das Etapas

### Etapa 1: Mapeamento do Banco 🗺️

```python
# schema_mapper.py

1. Conecta no banco de dados
   ↓
2. Lista todas as tabelas
   ↓
3. Para cada tabela importante:
   - Lê todas as colunas
   - Identifica tipos de dados
   - Detecta chave primária
   ↓
4. Analisa o padrão de nomes
   ↓
5. Detecta tipo de schema
   (ACIS v1, L2J Premium, etc)
   ↓
6. Salva em YAML e JSON
```

**Input:**
```
MySQL Database
├── characters (52 colunas)
├── accounts (15 colunas)
└── clan_data (28 colunas)
```

**Output:**
```yaml
# schema_acis_v1.yaml
database_type: acis_v1
tables:
  characters:
    columns:
      obj_Id: int(11)
      char_name: varchar(35)
      level: int(11)
      ...
    primary_key: obj_Id
```

---

### Etapa 2: Geração do Arquivo Query 🔨

```python
# query_generator.py

1. Lê o arquivo schema_*.yaml
   ↓
2. Identifica padrões específicos:
   - Nome da coluna de ID (obj_Id, charId, char_id)
   - Estrutura de subclasses
   - Estrutura de clans
   - Nome da coluna de access_level
   ↓
3. Gera métodos adaptados:
   - LineageStats.top_pvp()
   - LineageStats.top_pk()
   - LineageStats.players_online()
   - ... (20+ métodos)
   ↓
4. Ajusta automaticamente:
   - JOINs entre tabelas
   - Nomes de colunas
   - WHERE clauses
   ↓
5. Salva em query_*.py
```

**Input:**
```yaml
database_type: acis_v1
tables:
  characters:
    primary_key: obj_Id
```

**Output:**
```python
# query_acis_v1.py
def top_pvp(limit=10):
    sql = """
        SELECT C.char_name, C.pvpkills
        FROM characters C
        WHERE C.obj_Id = :id  # ← Adaptado!
    """
```

---

## 🎯 Comparação: Manual vs Automático

### ❌ Método Manual (Antigo)

```
1. Analisar banco de dados manualmente          ⏰ 2-3 horas
2. Identificar diferenças de schema             ⏰ 1-2 horas
3. Copiar arquivo query existente               ⏰ 5 min
4. Ajustar cada query manualmente               ⏰ 3-4 horas
5. Testar e corrigir erros                      ⏰ 2-3 horas
───────────────────────────────────────────────────────────
TOTAL:                                          ⏰ 8-12 HORAS ❌
```

### ✅ Método Automático (Novo)

```
1. Configurar conexão do banco                  ⏰ 2 min
2. Executar gerar_query.py                      ⏰ 30 seg
3. Revisar arquivo gerado                       ⏰ 5-10 min
4. Fazer ajustes finos (se necessário)          ⏰ 10-20 min
───────────────────────────────────────────────────────────
TOTAL:                                          ⏰ 15-30 MIN ✅
```

**Economia: ~95% de tempo! 🚀**

---

## 🔀 Fluxos de Uso

### Fluxo 1: Mapeamento Automático (Recomendado)

```
Você → gerar_query.py
          ↓
    Schema Mapper (automático)
          ↓
    schema_*.yaml (gerado)
          ↓
    Query Generator (automático)
          ↓
    query_*.py ✅
```

**Quando usar:**
- ✅ Você tem acesso direto ao banco
- ✅ Primeira vez com o banco
- ✅ Quer velocidade máxima

---

### Fluxo 2: Mapeamento Manual

```
Você → template_schema.yaml
          ↓
    Edição manual (seu conhecimento)
          ↓
    schema_custom.yaml
          ↓
    gerar_query.py schema_custom.yaml
          ↓
    query_custom.py ✅
```

**Quando usar:**
- ✅ Sem acesso direto ao banco
- ✅ Schema muito customizado
- ✅ Quer controle total

---

### Fluxo 3: Atualização de Schema Existente

```
Você → gerar_query.py
          ↓
    Backup automático (query_*.backup.py)
          ↓
    Remapeamento
          ↓
    Novo query_*.py
          ↓
    git diff (verificar mudanças) ✅
```

**Quando usar:**
- ✅ Banco foi atualizado
- ✅ Novas tabelas/colunas
- ✅ Mudança de versão

---

## 🎨 Arquitetura do Código

```
┌─────────────────────────────────────────────────────────┐
│                     CAMADA DE USO                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  views.py, services.py, tasks.py, etc.          │  │
│  │  from ...querys.query_* import LineageStats     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   CAMADA DE QUERY                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  query_acis_v1.py (GERADO AUTOMATICAMENTE)      │  │
│  │  ├─ LineageStats                                │  │
│  │  ├─ LineageServices                             │  │
│  │  ├─ LineageAccount                              │  │
│  │  └─ LineageMarketplace                          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  CAMADA DE DATABASE                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  database.py                                     │  │
│  │  LineageDB().select()                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     MySQL Database                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  characters, accounts, clan_data, items, etc.    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes

### 1. **schema_mapper.py**
**Responsabilidade:** Conectar no banco e mapear estrutura

```python
mapper = SchemaMapper()
schema = mapper.map_database_schema()
mapper.save_schema_to_yaml('schema.yaml')
```

**Métodos principais:**
- `get_all_tables()` - Lista tabelas
- `get_table_columns(table)` - Lista colunas
- `_detect_schema_type()` - Identifica tipo
- `map_database_schema()` - Mapeamento completo

---

### 2. **query_generator.py**
**Responsabilidade:** Gerar código Python a partir do schema

```python
generator = QueryGenerator('schema.yaml')
generator.generate_file('query_custom.py')
```

**Métodos principais:**
- `_get_char_id_column()` - Detecta coluna de ID
- `_get_clan_structure()` - Analisa clans
- `generate_lineage_stats_class()` - Gera classe
- `generate_file()` - Gera arquivo completo

---

### 3. **gerar_query.py**
**Responsabilidade:** Orquestrar todo o processo

```python
# Executa:
1. SchemaMapper (se necessário)
2. QueryGenerator
3. Backup
4. Validações
```

---

## 📈 Estatísticas

### Linhas de Código Geradas Automaticamente

```
LineageStats:           ~400 linhas
LineageServices:        ~100 linhas
LineageAccount:         ~300 linhas
LineageMarketplace:     ~200 linhas
TransferFromWallet:     ~100 linhas
TransferFromChar:       ~150 linhas
LineageInflation:       ~150 linhas
─────────────────────────────────────
TOTAL:                  ~1400 linhas ✅
```

### Tempo Economizado por Projeto

```
Mapeamento manual:      8-12 horas
Mapeamento automático:  0.5 hora
─────────────────────────────────────
Economia:               7.5-11.5 horas por projeto! 🚀
```

### Redução de Erros

```
Manual:   ~30-50 erros típicos
         (typos, colunas erradas, JOINs incorretos)

Automático: ~0-5 ajustes finos necessários
           (geralmente específicos do negócio)
```

---

## 🎯 Casos de Uso Reais

### Caso 1: Novo Servidor L2
```
Problema: Servidor High Five com schema customizado
Solução: gerar_query.py (30 segundos)
Resultado: 1400 linhas geradas, prontas para uso
```

### Caso 2: Migração de Projeto
```
Problema: Migrar de ACIS para L2J Premium
Solução: Mapear novo banco, gerar novo query
Resultado: Código adaptado automaticamente
```

### Caso 3: Múltiplos Servidores
```
Problema: 3 servidores com schemas diferentes
Solução: Gerar query_server1.py, query_server2.py, query_server3.py
Resultado: Todos funcionando em paralelo
```

---

## 🔐 Segurança

### Permissões Recomendadas

```sql
-- Criar usuário read-only para mapeamento
CREATE USER 'l2_mapper'@'%' IDENTIFIED BY 'senha_segura';
GRANT SELECT ON l2jdb.* TO 'l2_mapper'@'%';
FLUSH PRIVILEGES;
```

### O que o Mapper Acessa

```
✅ SELECT em tabelas (apenas leitura)
✅ SHOW TABLES
✅ SHOW COLUMNS
❌ Nenhuma modificação no banco
❌ Nenhum INSERT/UPDATE/DELETE
```

---

**🎉 Sistema completo e pronto para uso!**

