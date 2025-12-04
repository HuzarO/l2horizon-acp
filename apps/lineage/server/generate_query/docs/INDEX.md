# 📚 Índice da Documentação

## 🚀 Início Rápido
Leia primeiro se você quer começar já!

1. **[COMECE_AQUI.md](COMECE_AQUI.md)** 🎯
   - Guia ultra-rápido (30 segundos)
   - Ação imediata
   - Links para tudo

2. **[QUICK_START.md](QUICK_START.md)** ⚡
   - Guia rápido de 5 minutos
   - Comandos essenciais
   - Troubleshooting básico

## 📖 Documentação Principal

3. **[LEIA-ME.md](LEIA-ME.md)** 📘 🇧🇷
   - Documentação completa em português (RECOMENDADO)
   - Todos os recursos
   - Configuração detalhada
   - Resolução de problemas

4. **[README_RAPIDO.md](README_RAPIDO.md)** 📄
   - Resumo executivo
   - Referência rápida

## 🎓 Tutoriais e Exemplos

5. **[EXEMPLO_USO.md](EXEMPLO_USO.md)** 💡
   - Exemplos práticos passo a passo
   - Casos de uso reais
   - Dicas e truques
   - Troubleshooting avançado

6. **[FLUXO.md](FLUXO.md)** 🔄
   - Como o sistema funciona internamente
   - Arquitetura e design
   - Fluxos de dados
   - Estatísticas e comparações

## 🗂️ Schemas e Templates

7. **[../schemas/README.md](../schemas/README.md)** 📊
   - Informações sobre schemas
   - Schemas suportados

8. **[../schemas/template_schema.yaml](../schemas/template_schema.yaml)** 📝
   - Template para mapeamento manual
   - Documentação de cada campo
   - Exemplos de uso

## 🛠️ Scripts e Ferramentas

### Scripts Principais

- **`gerar_query.py`** - Script Python unificado (recomendado)
- **`gerar_query.bat`** - Atalho para Windows
- **`gerar_query.sh`** - Atalho para Linux/Mac

### Ferramentas Internas

- **`schema_mapper.py`** - Mapeia banco de dados
- **`query_generator.py`** - Gera arquivos query_*.py

## 📋 Arquivos de Referência

### Queries Existentes (Exemplos)
- `query_acis_v1.py` - ACIS v1 (High Five)
- `query_l2jpremium.py` - L2J Premium
- `query_classic.py` - Classic
- `query_dreamv2.py` - Dream v2
- `query_lucerav2.py` - Lucera v2
- `query_ruacis.py` - RU ACIS

## 🎯 Guias por Objetivo

### Quero começar agora!
→ Leia: **[COMECE_AQUI.md](COMECE_AQUI.md)**
→ Execute: `python gerar_query.py`

### Quero entender como funciona
→ Leia: **[FLUXO.md](FLUXO.md)**
→ Depois: **[LEIA-ME.md](LEIA-ME.md)**

### Preciso mapear manualmente
→ Leia: **[EXEMPLO_USO.md](EXEMPLO_USO.md)** (Caso de Uso 2)
→ Use: **[../schemas/template_schema.yaml](../schemas/template_schema.yaml)**

### Preciso customizar algo
→ Leia: **[LEIA-ME.md](LEIA-ME.md)** (seção Customização)
→ Edite: `../query_generator.py`

### Tenho um problema
→ Leia: **[QUICK_START.md](QUICK_START.md)** (seção Ajuda Rápida)
→ Leia: **[EXEMPLO_USO.md](EXEMPLO_USO.md)** (seção Problemas Comuns)

## 📊 Ordem de Leitura Sugerida

### Para Iniciantes
```
1. COMECE_AQUI.md       (30 seg)
2. QUICK_START.md       (5 min)
3. EXEMPLO_USO.md       (15 min)
4. Use o sistema!       (30 min)
5. LEIA-ME.md (consulta) (quando precisar)
```

### Para Avançados
```
1. README_RAPIDO.md     (1 min - overview)
2. FLUXO.md             (10 min - entender arquitetura)
3. LEIA-ME.md           (20 min - recursos completos)
4. Código fonte         (quando precisar customizar)
```

### Para Resolução de Problemas
```
1. QUICK_START.md → Ajuda Rápida
2. EXEMPLO_USO.md → Problemas Comuns
3. LEIA-ME.md → Resolução de Problemas
4. Código fonte → Debug profundo
```

## 🔗 Links Rápidos

### Configuração
- [Configurar Banco de Dados](LEIA-ME.md#configuração)
- [Instalar Dependências](QUICK_START.md#pré-requisitos)

### Uso
- [Primeiro Uso](QUICK_START.md#tutorial-1-primeira-vez)
- [Mapeamento Manual](EXEMPLO_USO.md#caso-de-uso-2-mapeamento-manual)
- [Atualizar Schema](EXEMPLO_USO.md#caso-de-uso-3-atualizar-schema-existente)

### Referência
- [Schemas Suportados](LEIA-ME.md#schemas-suportados)
- [Classes Geradas](LEIA-ME.md#classes-geradas)
- [Comandos Úteis](QUICK_START.md#comandos-úteis)

### Troubleshooting
- [FAQ Rápido](QUICK_START.md#faq-rápido)
- [Problemas Comuns](EXEMPLO_USO.md#problemas-comuns)
- [Resolução de Problemas](LEIA-ME.md#resolução-de-problemas)

## 📦 Estrutura do Projeto

```
generate_query/
│
├── 📚 docs/                  ← Você está aqui!
│   ├── INDEX.md              ← Este arquivo
│   ├── COMECE_AQUI.md        ← Início rápido
│   ├── LEIA-ME.md            ← 🇧🇷 Português completo
│   ├── QUICK_START.md        ← Guia 5 min
│   ├── README_RAPIDO.md      ← Resumo executivo
│   ├── EXEMPLO_USO.md        ← Tutoriais práticos
│   └── FLUXO.md              ← Como funciona
│
├── 🛠️ FERRAMENTAS
│   ├── README.md             ← Documentação principal
│   ├── gerar_query.py        ← Script principal
│   ├── gerar_query.bat       ← Windows
│   ├── gerar_query.sh        ← Linux/Mac
│   ├── schema_mapper.py      ← Mapear banco
│   └── query_generator.py    ← Gerar queries
│
├── 📊 schemas/
│   ├── README.md
│   └── template_schema.yaml
│
└── ../querys/                ← Arquivos gerados (saída)
    ├── query_acis_v1.py
    ├── query_l2jpremium.py
    └── ...
```

## 🎓 Recursos de Aprendizado

### Vídeos (Criar no futuro)
- [ ] Tutorial básico (5 min)
- [ ] Mapeamento manual (10 min)
- [ ] Customização avançada (15 min)

### Artigos
- [x] Guia de início rápido
- [x] Casos de uso práticos
- [x] Arquitetura do sistema

### Exemplos
- [x] Mapeamento automático
- [x] Mapeamento manual
- [x] Atualização de schema
- [x] Múltiplos servidores

## 💬 Suporte e Comunidade

### Obtendo Ajuda
1. Consulte a documentação
2. Procure em exemplos similares
3. Verifique o código dos queries existentes
4. Abra uma issue no repositório

### Contribuindo
- Compartilhe seus schemas customizados
- Reporte bugs encontrados
- Sugira melhorias
- Envie pull requests

## 📝 Changelog

### v1.0.0 (2025-12-04)
- ✅ Sistema inicial de mapeamento
- ✅ Gerador automático de queries
- ✅ Detecção de schemas ACIS, L2J, Classic
- ✅ Documentação completa
- ✅ Scripts de automação
- ✅ Template para mapeamento manual

### Próximas Versões
- [ ] Suporte a mais tipos de schemas
- [ ] Interface web para mapeamento
- [ ] Geração de testes automáticos
- [ ] Mais classes de serviços

---

## 🎯 Navegação Rápida

| Preciso... | Vá para... |
|------------|------------|
| Começar AGORA (30 seg) | [COMECE_AQUI.md](COMECE_AQUI.md) |
| Começar rápido (5 min) | [QUICK_START.md](QUICK_START.md) |
| Ver exemplos | [EXEMPLO_USO.md](EXEMPLO_USO.md) |
| Entender como funciona | [FLUXO.md](FLUXO.md) |
| Consultar detalhes | [LEIA-ME.md](LEIA-ME.md) |
| Mapear manualmente | [../schemas/template_schema.yaml](../schemas/template_schema.yaml) |
| Resolver problemas | [QUICK_START.md#ajuda-rápida](QUICK_START.md#ajuda-rápida) |

---

**📖 Boa leitura e bom desenvolvimento!**

*Sistema criado para facilitar a vida dos desenvolvedores de projetos Lineage 2* 🎮

