# ⚡ Quick Start - Guia Rápido

## 🎯 Objetivo

Gerar automaticamente arquivos `query_*.py` para integrar diferentes bancos de dados L2.

---

## 🚀 Uso Simples (Recomendado)

### Windows

```batch
# Duplo clique no arquivo:
gerar_query.bat

# Ou no terminal:
cd apps\lineage\server\generate_query
gerar_query.bat
```

### Linux/Mac

```bash
cd apps/lineage/server/generate_query
chmod +x gerar_query.sh
./gerar_query.sh
```

### Python (Multiplataforma)

```bash
cd apps/lineage/server/generate_query
python gerar_query.py
```

---

## 📋 O que acontece?

```
1. 🔍 Conecta no banco de dados (configurado em database.py)
2. 📊 Mapeia automaticamente as tabelas e colunas
3. 🎯 Detecta o tipo de schema (ACIS, L2J, etc)
4. 💾 Salva o mapeamento em schemas/schema_*.yaml
5. 🔨 Gera o arquivo query_*.py automaticamente
6. ✅ Pronto para usar!
```

---

## 📁 Estrutura de Arquivos Criados

```
apps/lineage/server/
├── generate_query/      ← Ferramentas (você está aqui!)
│   ├── gerar_query.py        ← Script principal
│   ├── gerar_query.bat       ← Atalho Windows
│   ├── gerar_query.sh        ← Atalho Linux/Mac
│   └── schemas/              ← Schemas mapeados
│       ├── schema_*.yaml     ← Gerados aqui
│       └── template_schema.yaml
│
└── querys/              ← Arquivos query_*.py (SAÍDA)
    └── query_*.py       ← Gerados aqui! ✨
```

---

## 🎓 Tutoriais

### Tutorial 1: Primeira Vez

```bash
# 1. Configure o banco em database.py
# 2. Execute o gerador
python gerar_query.py

# 3. Pronto! Use o arquivo gerado:
from apps.lineage.server.querys.query_acis_v1 import LineageStats
players = LineageStats.players_online()
```

### Tutorial 2: Usar Schema Existente

```bash
# Se você já tem um schema mapeado:
python gerar_query.py schemas/schema_acis_v1.yaml
```

### Tutorial 3: Mapeamento Manual

```bash
# 1. Copie o template
cp schemas/template_schema.yaml schemas/meu_schema.yaml

# 2. Edite meu_schema.yaml conforme seu banco

# 3. Gere o query
python gerar_query.py schemas/meu_schema.yaml
```

---

## ⚙️ Pré-requisitos

### Mínimo

- ✅ Python 3.7+
- ✅ PyYAML (`pip install pyyaml`)
- ✅ Acesso ao banco de dados L2
- ✅ Configuração em `database.py`

### Verificar Instalação

```bash
# Python instalado?
python --version

# PyYAML instalado?
python -c "import yaml; print('✅ PyYAML OK')"

# Banco acessível?
python -c "from apps.lineage.server.database import LineageDB; db = LineageDB(); print('✅ Database OK')"
```

---

## 🔧 Configuração Rápida do Banco

Edite `apps/lineage/server/database.py`:

```python
class LineageDB:
    def __init__(self):
        # ⚠️ AJUSTE ESTAS CONFIGURAÇÕES
        self.host = "localhost"       # ou IP do servidor
        self.port = 3306              # porta do MySQL
        self.database = "l2jdb"       # nome do banco
        self.user = "root"            # usuário
        self.password = "senha"       # senha
        self.enabled = True           # ativar?
```

---

## 📊 Schemas Suportados

| Schema | Detecção | ID Column | Nível |
|--------|----------|-----------|--------|
| ACIS v1 | ✅ Auto | `obj_Id` | Base + Subclass |
| L2J Premium | ✅ Auto | `charId` | characters.level |
| Classic | ✅ Auto | `char_id` | characters.level |
| Outros | ⚠️ Manual | Custom | Custom |

---

## 🎯 Uso no Projeto

Após gerar, use assim:

```python
# views.py
from apps.lineage.server.querys.query_acis_v1 import LineageStats

def top_pvp_view(request):
    # Buscar top 100 PvP
    players = LineageStats.top_pvp(limit=100)
    
    return render(request, 'top_pvp.html', {
        'players': players
    })
```

---

## ❓ FAQ Rápido

**Q: Quanto tempo demora?**  
A: ~30 segundos para mapear + ~5 segundos para gerar

**Q: Preciso configurar algo?**  
A: Só a conexão do banco em `database.py`

**Q: Funciona com qualquer L2?**  
A: Sim! Se não detectar automaticamente, use mapeamento manual

**Q: Posso editar o arquivo gerado?**  
A: Sim! O gerador faz o trabalho pesado, mas você pode customizar

**Q: E se o banco mudar?**  
A: Execute novamente. O script faz backup automático

---

## 🆘 Ajuda Rápida

### Erro: "Connection refused"
```bash
# Verifique:
1. Banco está rodando? (systemctl status mysql)
2. Host e porta corretos?
3. Firewall liberado?
```

### Erro: "Table not found"
```bash
# Seu banco usa nomes diferentes
# Solução: Use mapeamento manual
cp schemas/template_schema.yaml schemas/custom.yaml
# Edite custom.yaml e execute:
python gerar_query.py schemas/custom.yaml
```

### Erro: "Module not found"
```bash
# Instale as dependências:
pip install pyyaml
```

---

## 📚 Documentação Completa

- 🎯 **[COMECE_AQUI.md](COMECE_AQUI.md)** - Início ultra-rápido (30 seg)
- 🇧🇷 **[LEIA-ME.md](LEIA-ME.md)** - Documentação completa em português
- 📋 **[EXEMPLO_USO.md](EXEMPLO_USO.md)** - Exemplos práticos passo a passo
- 🔄 **[FLUXO.md](FLUXO.md)** - Como o sistema funciona
- 🗺️ **[../schemas/template_schema.yaml](../schemas/template_schema.yaml)** - Template documentado
- 📖 **[INDEX.md](INDEX.md)** - Índice completo

---

## 🎯 Comandos Úteis

```bash
# Mapear e gerar (automático)
python gerar_query.py

# Usar schema existente
python gerar_query.py schemas/schema_acis_v1.yaml

# Só mapear (sem gerar)
python schema_mapper.py

# Só gerar (com schema existente)
python query_generator.py schemas/schema_acis_v1.yaml

# Backup do arquivo atual
cp query_acis_v1.py query_acis_v1.backup.py

# Verificar diferenças
git diff query_acis_v1.py
```

---

## ✅ Checklist

Antes de usar em produção:

- [ ] Banco de dados acessível
- [ ] Schema mapeado corretamente
- [ ] Arquivo query_*.py gerado
- [ ] Testes básicos passaram
- [ ] Backup feito (se necessário)

---

**🎉 Pronto! Em menos de 1 minuto você tem queries prontas!**

*Economize horas de trabalho manual* ⏰

