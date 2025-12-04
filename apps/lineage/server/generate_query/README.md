# 🗺️ Sistema de Mapeamento e Geração de Queries L2

Sistema automatizado para mapear schemas de bancos de dados Lineage 2 e gerar arquivos `query_*.py` automaticamente.

## 📚 Documentação

- 🎯 **[COMECE AQUI](docs/COMECE_AQUI.md)** - Guia rápido para começar em 30 segundos
- 🇧🇷 **[LEIA-ME](docs/LEIA-ME.md)** - Documentação completa em português (RECOMENDADO)
- ⚡ **[Quick Start](docs/QUICK_START.md)** - Guia rápido de 5 minutos
- 💡 **[Exemplos de Uso](docs/EXEMPLO_USO.md)** - Tutoriais práticos passo a passo
- 🔄 **[Fluxo do Sistema](docs/FLUXO.md)** - Como funciona internamente
- 📖 **[Índice Completo](docs/INDEX.md)** - Navegação por toda documentação

---

## 📋 Visão Geral

Este sistema resolve o problema de ter que escrever manualmente 1000+ linhas de código de queries toda vez que você precisa integrar um novo projeto L2 com schema diferente.

### O que ele faz:

1. **Mapeia** automaticamente a estrutura do banco de dados L2
2. **Detecta** o tipo de schema (ACIS, L2J Premium, Classic, etc)
3. **Gera** automaticamente o arquivo `query_*.py` adaptado ao schema

## 🚀 Como Usar

### Uso Rápido (Recomendado)

```bash
# Entre nesta pasta
cd apps/lineage/server/generate_query

# Execute o gerador (tudo em um comando)
python gerar_query.py
```

Pronto! O arquivo será gerado em `../querys/query_*.py`

---

### Método 1: Mapeamento Automático (Detalhado)

#### Passo 1: Mapear o Banco de Dados

```bash
cd apps/lineage/server/generate_query
python schema_mapper.py
```

Isso vai:
- Conectar no banco de dados configurado em `LineageDB`
- Analisar as tabelas principais
- Detectar o tipo de schema automaticamente
- Gerar arquivos `schema_*.yaml` e `schema_*.json` em `schemas/`

#### Passo 2: Gerar o Arquivo de Query

```bash
python query_generator.py schemas/schema_acis_v1.yaml
```

Pronto! Um novo arquivo será gerado em `../querys/query_acis_v1.py`

### Método 2: Mapeamento Manual

Se você não tem acesso direto ao banco ou quer customizar:

#### Passo 1: Copiar o Template

```bash
cp schemas/template_schema.yaml schemas/schema_meu_l2.yaml
```

#### Passo 2: Editar o Schema

Abra `schema_meu_l2.yaml` e ajuste conforme seu banco de dados:

```yaml
database_type: meu_l2_custom

tables:
  characters:
    columns:
      charId: int(11)  # Seu banco usa charId? Ajuste aqui
      char_name: varchar(35)
      # ... outras colunas
    primary_key: charId
```

#### Passo 3: Gerar o Query

```bash
python query_generator.py schemas/schema_meu_l2.yaml
```

## 📂 Estrutura de Arquivos

```
generate_query/               # Ferramentas (esta pasta)
├── README.md                 # Este arquivo
├── gerar_query.py            # Script principal (USE ESTE!)
├── gerar_query.bat           # Atalho Windows
├── gerar_query.sh            # Atalho Linux/Mac
├── schema_mapper.py          # Mapeia bancos de dados
├── query_generator.py        # Gera arquivos query_*.py
├── docs/                     # Documentação completa
│   ├── COMECE_AQUI.md        # Início rápido (30 seg)
│   ├── LEIA-ME.md            # 🇧🇷 Português completo
│   ├── QUICK_START.md        # Guia 5 min
│   ├── EXEMPLO_USO.md        # Tutoriais
│   ├── FLUXO.md              # Arquitetura
│   └── INDEX.md              # Índice navegável
└── schemas/                  # Schemas mapeados
    ├── README.md
    ├── template_schema.yaml  # Template manual
    └── schema_*.yaml         # Gerados

../querys/                    # Arquivos gerados (SAÍDA)
├── query_acis_v1.py          # Gerados aqui!
├── query_l2jpremium.py
└── query_*.py
```

## 🔍 Schemas Suportados

### Detecção Automática

O `schema_mapper` detecta automaticamente:

| Tipo | Identificação | Coluna de ID |
|------|---------------|--------------|
| **ACIS v1** | Usa `obj_Id` na tabela characters | `obj_Id` |
| **L2J Premium** | Usa `charId` na tabela characters | `charId` |
| **Classic** | Usa `char_id` na tabela characters | `char_id` |

### Diferenças Comuns Entre Schemas

#### ACIS v1
```sql
-- Tabela characters usa obj_Id
SELECT * FROM characters WHERE obj_Id = 123;

-- Subclasses em tabela separada
SELECT * FROM character_subclasses WHERE char_obj_id = 123;

-- Nome do clan em clan_subpledges
SELECT name FROM clan_subpledges WHERE sub_pledge_id = 0;
```

#### L2J Premium
```sql
-- Tabela characters usa charId
SELECT * FROM characters WHERE charId = 123;

-- Level direto na tabela characters
SELECT level FROM characters WHERE charId = 123;

-- Nome do clan em clan_data
SELECT clan_name FROM clan_data WHERE clan_id = 456;
```

## 🛠️ Configuração

### Pré-requisitos

1. Python 3.7+
2. PyYAML:
   ```bash
   pip install pyyaml
   ```
3. Banco de dados L2 acessível

### Configurar Conexão do Banco

Edite `../database.py`:

```python
class LineageDB:
    def __init__(self):
        self.host = "localhost"       # IP do servidor
        self.port = 3306              # Porta MySQL
        self.database = "l2jdb"       # Nome do banco
        self.user = "root"            # Usuário
        self.password = "senha"       # Senha
        self.enabled = True           # Ativar?
```

## 📝 Exemplo Completo

### Cenário: Você tem um servidor High Five novo

```bash
# 1. Entrar na pasta generate_query
cd apps/lineage/server/generate_query

# 2. Executar o gerador (faz tudo automaticamente)
python gerar_query.py

# Saída:
# 🔍 Iniciando mapeamento do banco de dados...
# 📊 Mapeando tabela: characters
#    ✅ 45 colunas mapeadas
# 📊 Mapeando tabela: accounts
#    ✅ 12 colunas mapeadas
# ...
# ✅ Schema salvo em: schemas/schema_acis_v1.yaml
# 📦 Tipo detectado: acis_v1
# 🔨 Gerando arquivo: query_acis_v1.py
# ✅ Arquivo gerado em: ../querys/query_acis_v1.py
# 🎉 Tudo pronto!

# 3. Usar no seu projeto
from apps.lineage.server.querys.query_acis_v1 import LineageStats
players = LineageStats.players_online()
```

## 🎯 Classes Geradas

O arquivo `query_*.py` gerado contém:

### 1. **LineageStats**
Métodos para rankings e estatísticas:
- `players_online()` - Jogadores online
- `top_pvp(limit)` - Top PvP
- `top_pk(limit)` - Top PK
- `top_online(limit)` - Top tempo online
- `top_level(limit)` - Top level
- `top_adena(limit)` - Top adena
- `top_clans(limit)` - Top clans
- `olympiad_ranking()` - Ranking da olympiada
- `olympiad_all_heroes()` - Todos os heróis
- `olympiad_current_heroes()` - Heróis atuais
- `grandboss_status()` - Status dos grandbosses
- `siege()` - Informações de siege

### 2. **LineageAccount**
Métodos para gerenciar contas:
- `get_account_by_login(login)` - Buscar conta
- `register(login, password, access_level, email)` - Registrar conta
- E mais...

## 🔧 Customização

### Adicionar Novos Métodos

Edite o `query_generator.py` e adicione seus métodos customizados na classe `QueryGenerator`.

### Ajustar Detecção de Schema

Edite o método `_detect_schema_type()` em `schema_mapper.py` para adicionar novos tipos.

## ⚠️ Notas Importantes

1. **Sempre revise o arquivo gerado** - O gerador faz o trabalho pesado, mas sempre confira se está correto
2. **Backup** - Faça backup dos arquivos query_*.py existentes antes de gerar novos
3. **Permissões** - Certifique-se que tem permissão de leitura no banco de dados

## 🐛 Resolução de Problemas

### Erro: "Tabela não encontrada"
- Verifique se o banco de dados está acessível
- Confira as credenciais em `database.py`

### Schema detectado como "unknown"
- Crie um mapeamento manual usando `template_schema.yaml`
- Ou edite `_detect_schema_type()` para adicionar seu tipo

### Arquivo gerado com erros
- Revise o schema YAML
- Ajuste manualmente as queries geradas
- Abra uma issue no repositório

## 📚 Recursos Adicionais

- `schemas/template_schema.yaml` - Template completo com documentação
- `schemas/README.md` - Informações sobre schemas
- Arquivos `query_*.py` existentes - Exemplos de diferentes schemas

## 🤝 Contribuindo

Encontrou um bug ou tem uma melhoria? Contribuições são bem-vindas!

1. Adicione novos tipos de schema em `schema_mapper.py`
2. Melhore a geração de queries em `query_generator.py`
3. Compartilhe seus schemas em `schemas/`

---

**Desenvolvido para facilitar a integração de projetos Lineage 2** 🎮

Economize horas de trabalho manual e evite erros de digitação! 🚀

