# 📁 Diretório de Queries L2

## 📍 Você está em: `querys/`

Esta pasta contém os **arquivos query_*.py gerados** pelo sistema de mapeamento.

---

## 🎯 Arquivos Neste Diretório

Cada arquivo `query_*.py` contém classes para acessar o banco de dados L2:

```
querys/
├── query_acis_v1.py      ← Schema ACIS v1 (High Five)
├── query_l2jpremium.py   ← Schema L2J Premium
├── query_classic.py      ← Schema Classic
├── query_dreamv2.py      ← Schema Dream v2
├── query_lucerav2.py     ← Schema Lucera v2
└── query_*.py            ← Outros schemas customizados
```

---

## 🔨 Como os Arquivos São Gerados

Estes arquivos são **gerados automaticamente** pelo sistema em `../generate_query/`:

```bash
# Para gerar um novo arquivo query_*.py:
cd ../generate_query
python gerar_query.py
```

O arquivo gerado será colocado **aqui** automaticamente.

---

## 📖 Uso dos Arquivos

### Exemplo 1: Importar e Usar

```python
# Em views.py, services.py, etc.
from apps.lineage.server.querys.query_acis_v1 import LineageStats

def ranking_pvp(request):
    # Buscar top 100 PvP
    players = LineageStats.top_pvp(limit=100)
    return render(request, 'ranking.html', {'players': players})
```

### Exemplo 2: Estatísticas do Servidor

```python
from apps.lineage.server.querys.query_acis_v1 import LineageStats

# Jogadores online
online = LineageStats.players_online()

# Top PvP
top_pvp = LineageStats.top_pvp(limit=10)

# Top Clans
top_clans = LineageStats.top_clans(limit=10)

# Olympiad
olympiad = LineageStats.olympiad_ranking()
```

### Exemplo 3: Gerenciar Contas

```python
from apps.lineage.server.querys.query_acis_v1 import LineageAccount

# Buscar conta
account = LineageAccount.get_account_by_login("username")

# Registrar nova conta
LineageAccount.register("newuser", "password123", 0, "email@example.com")

# Atualizar senha
LineageAccount.update_password("newpassword", "username")
```

---

## 🏗️ Estrutura dos Arquivos Query

Cada arquivo `query_*.py` contém classes padronizadas:

### 1. **LineageStats**
Estatísticas e rankings do servidor:
- `players_online()` - Contagem de jogadores online
- `top_pvp(limit)` - Ranking PvP
- `top_pk(limit)` - Ranking PK
- `top_online(limit)` - Ranking tempo online
- `top_level(limit)` - Ranking level
- `top_adena(limit)` - Ranking adena
- `top_clans(limit)` - Ranking clans
- `olympiad_ranking()` - Ranking olympiad
- `olympiad_all_heroes()` - Todos os heróis
- `olympiad_current_heroes()` - Heróis atuais
- `grandboss_status()` - Status dos grandbosses
- `raidboss_status()` - Status dos raidbosses
- `siege()` - Informações de siege
- `boss_jewel_locations()` - Localização de boss jewels

### 2. **LineageServices**
Serviços para personagens:
- `find_chars(login)` - Buscar chars de uma conta
- `check_char(acc, cid)` - Verificar char
- `check_name_exists(name)` - Verificar se nome existe
- `change_nickname(acc, cid, name)` - Trocar nome
- `change_sex(acc, cid, sex)` - Trocar sexo
- `unstuck(acc, cid, x, y, z)` - Desbugar char

### 3. **LineageAccount**
Gerenciamento de contas:
- `get_account_by_login(login)` - Buscar conta
- `find_accounts_by_email(email)` - Buscar por email
- `register(login, password, access_level, email)` - Registrar
- `update_password(password, login)` - Atualizar senha
- `link_account_to_user(login, uuid)` - Vincular ao site
- `validate_credentials(login, password)` - Validar login

### 4. **LineageMarketplace** (alguns schemas)
Sistema de marketplace:
- `get_user_characters(account)` - Chars do usuário
- `verify_character_ownership(char_id, account)` - Verificar dono
- `get_character_details(char_id)` - Detalhes do char
- `transfer_character_to_account(char_id, new_account)` - Transferir

---

## 🔄 Atualizar Arquivos Existentes

Se o schema do banco mudou:

```bash
# 1. Entre na pasta generate_query
cd ../generate_query

# 2. Execute o gerador (fará backup automático)
python gerar_query.py

# 3. O arquivo em querys/ será atualizado
```

---

## 📚 Documentação Completa

Para gerar novos arquivos ou entender o sistema:

👉 **Vá para: `../generate_query/`**

Leia:
- `LEIA-ME.md` - 🇧🇷 Documentação em português
- `QUICK_START.md` - Guia rápido
- `README.md` - Documentação completa

---

## ⚠️ Importante

### ✅ Faça
- Use estes arquivos em suas views/services
- Importe as classes necessárias
- Chame os métodos com os parâmetros corretos

### ❌ Não Faça
- **Não edite estes arquivos manualmente** (serão sobrescritos)
- Se precisar customizar, faça **após gerar** ou edite o gerador
- Sempre faça backup antes de regerar

---

## 🎯 Próximos Passos

1. **Use os arquivos existentes** nas suas views
2. **Gere novos** se precisar de outro schema
3. **Consulte** a documentação em `../generate_query/`

---

## 💡 Exemplo de Integração Completa

```python
# views/tops_views.py
from django.shortcuts import render
from apps.lineage.server.querys.query_acis_v1 import LineageStats

def top_pvp_view(request):
    """View do ranking PvP"""
    limit = request.GET.get('limit', 100)
    
    # Buscar dados
    players = LineageStats.top_pvp(limit=int(limit))
    
    # Renderizar
    return render(request, 'tops/top_pvp.html', {
        'players': players,
        'title': 'Top PvP Players'
    })

def server_status_view(request):
    """View do status do servidor"""
    context = {
        'online': LineageStats.players_online()[0]['quant'],
        'top_clans': LineageStats.top_clans(limit=5),
        'current_heroes': LineageStats.olympiad_current_heroes(),
    }
    return render(request, 'server/status.html', context)
```

---

**🎮 Boa sorte com seu servidor L2!**

Para gerar novos arquivos: `cd ../generate_query && python gerar_query.py`

