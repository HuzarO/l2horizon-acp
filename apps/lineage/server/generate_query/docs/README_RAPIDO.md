# 🚀 Gerador de Queries L2 - README Rápido

## 📍 Você está em: `generate_query/`

Esta pasta contém as **ferramentas** para gerar automaticamente arquivos `query_*.py`.

---

## ⚡ Uso Super Rápido

### Windows
```batch
# Duplo clique em:
gerar_query.bat
```

### Linux/Mac/Python
```bash
python gerar_query.py
```

---

## 📂 Estrutura

```
generate_query/           ← Você está aqui! (Ferramentas)
├── gerar_query.py        ← EXECUTE ESTE!
├── schema_mapper.py      ← Mapeia banco
├── query_generator.py    ← Gera código
└── schemas/              ← Schemas mapeados
    ├── template_schema.yaml
    └── schema_*.yaml     ← Gerados automaticamente

../querys/                ← Arquivos query_*.py são gerados AQUI!
├── query_acis_v1.py      
├── query_l2jpremium.py
└── query_*.py            ← Saída do gerador
```

---

## 🎯 O que o gerador faz?

1. **Conecta** no banco de dados (config em `../database.py`)
2. **Mapeia** tabelas e colunas automaticamente
3. **Detecta** tipo de schema (ACIS, L2J, etc)
4. **Gera** arquivo `query_*.py` em `../querys/`
5. **Pronto!** Use em suas views

---

## 📖 Documentação Completa

- **[COMECE_AQUI.md](COMECE_AQUI.md)** - 🎯 Início imediato (30 seg)
- **[LEIA-ME.md](LEIA-ME.md)** - 🇧🇷 Documentação em português (RECOMENDADO)
- **[QUICK_START.md](QUICK_START.md)** - Guia rápido 5 minutos
- **[EXEMPLO_USO.md](EXEMPLO_USO.md)** - Exemplos práticos
- **[FLUXO.md](FLUXO.md)** - Como funciona
- **[INDEX.md](INDEX.md)** - Índice navegável

---

## ⚙️ Configuração Mínima

Edite `apps/lineage/server/database.py`:

```python
class LineageDB:
    def __init__(self):
        self.host = "localhost"
        self.database = "l2jdb"
        self.user = "root"
        self.password = "senha"
```

---

## 🎓 Exemplo Completo

```bash
# 1. Entre na pasta
cd apps/lineage/server/generate_query

# 2. Execute
python gerar_query.py

# 3. O sistema gera:
# - schemas/schema_acis_v1.yaml (mapeamento)
# - ../querys/query_acis_v1.py (código)

# 4. Use no projeto:
from apps.lineage.server.querys.query_acis_v1 import LineageStats
players = LineageStats.players_online()
```

---

## ✅ Checklist

- [ ] Python 3.7+ instalado
- [ ] PyYAML instalado (`pip install pyyaml`)
- [ ] Banco de dados acessível
- [ ] Configuração em `database.py` ajustada

---

## 🆘 Ajuda Rápida

### "Connection refused"
→ Verifique host/senha em `database.py`

### "Table not found"
→ Use mapeamento manual: `schemas/template_schema.yaml`

### "Module not found"
→ `pip install pyyaml`

---

## 📊 Resultado

O gerador cria **~1400 linhas** de código Python pronto com:

- ✅ LineageStats (rankings, tops, olympiad)
- ✅ LineageAccount (gerenciamento de contas)
- ✅ Todas as queries adaptadas ao seu schema
- ✅ Cache configurado
- ✅ Documentação inline

---

**🎉 Economize 95% do tempo de desenvolvimento!**

Comece agora: `python gerar_query.py`

