# 🎯 COMECE AQUI!

## 👋 Bem-vindo ao Gerador de Queries L2

Você está em: `apps/lineage/server/generate_query/`

---

## ⚡ Ação Rápida (30 segundos)

### 1️⃣ Configure o Banco

Edite: `../database.py`

```python
self.host = "localhost"      # ← Seu IP
self.database = "l2jdb"      # ← Seu banco
self.user = "root"           # ← Usuário
self.password = "senha"      # ← Senha
```

### 2️⃣ Execute

**Windows:** Duplo clique em `gerar_query.bat`

**Linux/Mac/Python:**
```bash
python gerar_query.py
```

### 3️⃣ Pronto! ✅

O arquivo foi gerado em: `../querys/query_*.py`

---

## 📚 Próximos Passos

### Quer entender melhor?

1. **[LEIA-ME.md](LEIA-ME.md)** - 🇧🇷 Leia em português (RECOMENDADO)
2. **[QUICK_START.md](QUICK_START.md)** - Guia rápido de 5 minutos
3. **[README_RAPIDO.md](README_RAPIDO.md)** - Resumo executivo
4. **[EXEMPLO_USO.md](EXEMPLO_USO.md)** - Exemplos práticos

### Quer customizar?

- **[../schemas/template_schema.yaml](../schemas/template_schema.yaml)** - Para mapeamento manual
- **[../query_generator.py](../query_generator.py)** - Para personalizar o gerador

---

## 🎯 O Que Este Sistema Faz

```
Você → Configura banco → Execute script
                              ↓
                    Mapeia automaticamente
                              ↓
                    Gera query_*.py (1400 linhas!)
                              ↓
                    Pronto para usar! ✅
```

**Economia:** 8-12 horas → 30 segundos 🚀

---

## 📂 Estrutura

```
generate_query/        ← Ferramentas (você está aqui)
├── gerar_query.py     ← EXECUTE!
├── *.md               ← Documentação
└── schemas/           ← Schemas

../querys/             ← Arquivos gerados (saída)
└── query_*.py         ← Use estes!
```

---

## 💡 Exemplo de Uso

Após gerar, use assim:

```python
from apps.lineage.server.querys.query_acis_v1 import LineageStats

# Buscar jogadores online
online = LineageStats.players_online()

# Top PvP
top = LineageStats.top_pvp(limit=100)
```

---

## 🆘 Problemas?

- **Connection refused:** Verifique `../database.py`
- **Module not found:** `pip install pyyaml`
- **Table not found:** Use mapeamento manual

Mais ajuda em: **[LEIA-ME.md](LEIA-ME.md)** ou **[QUICK_START.md](QUICK_START.md)**

---

**🚀 Comece agora: `python gerar_query.py`**

