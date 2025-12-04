# 📖 Exemplo Prático de Uso

## Cenário Real: Mapear um Servidor L2 High Five

Você tem um novo servidor High Five e precisa gerar as queries para ele.

### Passo a Passo

#### 1️⃣ Configure a Conexão do Banco

Edite `apps/lineage/server/database.py`:

```python
class LineageDB:
    def __init__(self):
        self.host = "192.168.1.100"      # IP do servidor
        self.port = 3306                  # Porta MySQL
        self.database = "l2jgs"           # Nome do banco
        self.user = "l2j_user"            # Usuário
        self.password = "senha_forte"     # Senha
```

#### 2️⃣ Execute o Mapeamento

Abra o terminal no diretório do projeto:

```bash
# Windows PowerShell
cd D:\PROJETOS\PDL\SITE
python apps\lineage\server\querys\schema_mapper.py
```

**Saída esperada:**

```
======================================================================
🗺️  SCHEMA MAPPER - Lineage 2 Database
======================================================================

🔍 Iniciando mapeamento do banco de dados...
📋 Tabelas a mapear: 12

📊 Mapeando tabela: characters
   ✅ 52 colunas mapeadas
📊 Mapeando tabela: character_subclasses
   ✅ 8 colunas mapeadas
📊 Mapeando tabela: accounts
   ✅ 15 colunas mapeadas
📊 Mapeando tabela: clan_data
   ✅ 28 colunas mapeadas
📊 Mapeando tabela: clan_subpledges
   ✅ 10 colunas mapeadas
📊 Mapeando tabela: items
   ✅ 12 colunas mapeadas
📊 Mapeando tabela: olympiad_nobles
   ✅ 12 colunas mapeadas
📊 Mapeando tabela: heroes
   ✅ 8 colunas mapeadas
📊 Mapeando tabela: grandboss_data
   ✅ 5 colunas mapeadas
📊 Mapeando tabela: raidboss_spawnlist
   ✅ 6 colunas mapeadas
📊 Mapeando tabela: castle
   ✅ 8 colunas mapeadas
📊 Mapeando tabela: siege_clans
   ✅ 4 colunas mapeadas

======================================================================
📊 RESUMO DO SCHEMA MAPEADO
======================================================================

🔧 Tipo de Schema: acis_v1
📦 Total de Tabelas: 12

📋 characters
   └─ PK: obj_Id
   └─ Colunas: 52
   └─ Principais: obj_Id, char_name, level, online

📋 accounts
   └─ PK: login
   └─ Colunas: 15
   └─ Principais: login, email

...

✅ Schema salvo em: querys/schemas/schema_acis_v1.yaml
✅ Schema salvo em: querys/schemas/schema_acis_v1.json
📦 Tipo detectado: acis_v1

======================================================================
✅ Mapeamento concluído!
======================================================================

💡 Próximos passos:
   1. Revise os arquivos gerados em: querys/schemas/
   2. Execute: python query_generator.py schemas/schema_acis_v1.yaml
   3. Um novo arquivo query_*.py será gerado automaticamente
```

#### 3️⃣ Revise o Schema Mapeado

Abra o arquivo gerado:

```bash
# Abrir no VSCode/Cursor
code apps\lineage\server\querys\schemas\schema_acis_v1.yaml
```

**Exemplo de conteúdo:**

```yaml
database_type: acis_v1
tables:
  characters:
    columns:
      obj_Id: int(11)
      char_name: varchar(35)
      level: int(11)
      classid: int(11)
      pvpkills: int(11)
      pkkills: int(11)
      online: int(1)
      onlinetime: int(11)
      clanid: int(11)
      account_name: varchar(45)
      accesslevel: int(11)
      # ... mais colunas
    primary_key: obj_Id
  
  accounts:
    columns:
      login: varchar(45)
      password: varchar(45)
      email: varchar(100)
      # ... mais colunas
    primary_key: login
  
  # ... mais tabelas
```

✅ Se estiver correto, prossiga para o próximo passo!

#### 4️⃣ Gere o Arquivo de Query

```bash
python apps\lineage\server\querys\query_generator.py apps\lineage\server\querys\schemas\schema_acis_v1.yaml
```

**Saída esperada:**

```
======================================================================
🏗️  QUERY GENERATOR - Lineage 2
======================================================================

🔨 Gerando arquivo: query_acis_v1.py
✅ Arquivo gerado com sucesso: apps/lineage/server/querys/query_acis_v1.py
📊 Database Type: acis_v1
📋 Classes geradas:
   - LineageStats (com métodos de ranking e estatísticas)
   - LineageAccount (gerenciamento de contas)

💡 Próximo passo: Revise o arquivo gerado e ajuste conforme necessário

======================================================================
✅ Geração concluída!
======================================================================
```

#### 5️⃣ Teste o Arquivo Gerado

Crie um teste rápido:

```python
# test_query.py
from apps.lineage.server.querys.query_acis_v1 import LineageStats

# Testar método
try:
    online = LineageStats.players_online()
    print(f"✅ Jogadores online: {online}")
    
    top_pvp = LineageStats.top_pvp(limit=5)
    print(f"✅ Top 5 PvP:")
    for player in top_pvp:
        print(f"   - {player['char_name']}: {player['pvpkills']} PvPs")
    
    print("\n✅ Todas as queries estão funcionando!")
except Exception as e:
    print(f"❌ Erro: {e}")
```

```bash
python test_query.py
```

#### 6️⃣ Integre no Projeto

O arquivo está pronto! Agora você pode usar em suas views:

```python
# views.py
from apps.lineage.server.querys.query_acis_v1 import LineageStats

def ranking_pvp(request):
    top_players = LineageStats.top_pvp(limit=100)
    return render(request, 'ranking.html', {'players': top_players})
```

---

## 🎯 Caso de Uso 2: Mapeamento Manual

Se você não tem acesso direto ao banco ou quer customizar:

### 1️⃣ Copie o Template

```bash
cp apps\lineage\server\querys\schemas\template_schema.yaml apps\lineage\server\querys\schemas\schema_meu_servidor.yaml
```

### 2️⃣ Edite o Schema

Abra `schema_meu_servidor.yaml` e ajuste conforme seu banco:

```yaml
database_type: meu_servidor_custom

tables:
  characters:
    columns:
      charId: int(11)           # ⚠️ Ajuste: Meu banco usa charId, não obj_Id
      char_name: varchar(35)
      level: int(11)
      classid: int(11)
      # ... ajuste todas as colunas conforme seu banco
    primary_key: charId         # ⚠️ Ajuste a PK também

  # ... ajuste todas as tabelas
```

### 3️⃣ Gere o Query

```bash
python apps\lineage\server\querys\query_generator.py apps\lineage\server\querys\schemas\schema_meu_servidor.yaml
```

### 4️⃣ Ajustes Finais

Abra o arquivo gerado e faça ajustes finos se necessário:

```python
# query_meu_servidor.py

# O gerador já adaptou todas as queries para usar charId:
def top_pvp(limit=10):
    sql = """
        SELECT 
            C.char_name, 
            C.pvpkills, 
            # ...
        FROM characters C
        WHERE C.accessLevel = '0'  # ✅ Gerado automaticamente
        ORDER BY pvpkills DESC
        LIMIT :limit
    """
```

---

## 🔄 Caso de Uso 3: Atualizar Schema Existente

Se o banco mudou e você precisa atualizar:

### 1️⃣ Backup do Arquivo Atual

```bash
cp apps\lineage\server\querys\query_acis_v1.py apps\lineage\server\querys\query_acis_v1.backup.py
```

### 2️⃣ Remapear o Banco

```bash
python apps\lineage\server\querys\schema_mapper.py
```

### 3️⃣ Gerar Novo Arquivo

```bash
python apps\lineage\server\querys\query_generator.py apps\lineage\server\querys\schemas\schema_acis_v1.yaml
```

### 4️⃣ Compare as Diferenças

Use o diff do Git:

```bash
git diff apps\lineage\server\querys\query_acis_v1.py
```

---

## 💡 Dicas e Truques

### Dica 1: Mapear Apenas Algumas Tabelas

Edite `schema_mapper.py` linha ~60:

```python
important_tables = [
    'characters',
    'accounts',
    'clan_data',
    # Adicione apenas as que você precisa
]
```

### Dica 2: Adicionar Métodos Customizados

Após gerar, adicione seus métodos no arquivo:

```python
# query_acis_v1.py

class LineageStats:
    # ... métodos gerados automaticamente
    
    @staticmethod
    @cache_lineage_result(timeout=300)
    def meu_metodo_custom():
        sql = """
            SELECT * FROM minha_tabela
        """
        return LineageStats._run_query(sql)
```

### Dica 3: Versionar os Schemas

Mantenha um histórico dos schemas:

```bash
schemas/
├── schema_acis_v1_2024_12.yaml
├── schema_acis_v1_2025_01.yaml
└── schema_acis_v1_latest.yaml
```

---

## ⚠️ Checklist de Verificação

Antes de usar em produção, verifique:

- [ ] Conexão com o banco está funcionando
- [ ] Schema mapeado está correto (revise o YAML)
- [ ] Arquivo query_*.py foi gerado sem erros
- [ ] Testes básicos passaram
- [ ] Backup do arquivo anterior foi feito
- [ ] Permissões do banco estão corretas (read-only recomendado)

---

## 🆘 Problemas Comuns

### "Connection refused"
**Solução:** Verifique host, porta e firewall do banco de dados.

### "Table 'characters' doesn't exist"
**Solução:** O banco pode usar nome diferente. Edite o schema manualmente.

### "Column 'obj_Id' not found"
**Solução:** Seu banco usa nome diferente para ID. Use mapeamento manual.

### Queries retornando dados vazios
**Solução:** Verifique se a coluna `accesslevel` existe e tem valor '0' para jogadores.

---

**🎉 Pronto! Você economizou horas de trabalho manual!**

