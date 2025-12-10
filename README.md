# Painel Definitivo Lineage [1.17](https://pdl.denky.dev.br)

<img align="right" height="180" src="https://i.imgur.com/0tL4OQ7.png"/>

O PDL é um painel que nasceu com a missão de oferecer ferramentas poderosas para administradores de servidores privados de Lineage 2. Inicialmente voltado à análise de riscos e estabilidade dos servidores, o projeto evoluiu e se consolidou como uma solução completa para prospecção, gerenciamento e operação de servidores — tudo em código aberto.

## Tecnologias Utilizadas

- **Python 3.14**: Linguagem de programação moderna e robusta utilizada como base do projeto.
- **Django 5.2+**: Framework web principal que permite a construção de aplicações rapidamente, com suporte a autenticação, gerenciamento de banco de dados e muito mais.
- **Gunicorn**: Servidor WSGI para servir requisições HTTP síncronas com alta performance.
- **Daphne**: Servidor ASGI para servir WebSockets e requisições assíncronas.
- **Celery**: Biblioteca que permite a execução de tarefas assíncronas em segundo plano, como envio de e-mails e processamento de dados.
- **Redis**: Sistema de gerenciamento de dados em memória utilizado como broker de mensagens para o Celery, melhorando o desempenho da aplicação.
- **Nginx**: Servidor web reverso que gerencia requisições HTTP e serve arquivos estáticos e de mídia.
- **Docker**: Utilizado para containerização da aplicação, garantindo consistência e facilidade de deployment em diferentes ambientes.
- **Docker Compose**: Ferramenta que orquestra múltiplos containers, facilitando a configuração e execução dos serviços.

## Estrutura do Projeto

### Serviços Definidos no Docker Compose

- **site_http**: Serviço HTTP que roda o Django com Gunicorn (requisições síncronas).
- **site_asgi**: Serviço ASGI que roda o Django com Daphne (WebSockets e requisições assíncronas).
- **celery**: Worker do Celery que processa tarefas em segundo plano.
- **celery-beat**: Agendador de tarefas do Celery que executa tarefas em horários programados.
- **flower**: Interface de monitoramento para o Celery.
- **nginx**: Servidor web que atua como proxy reverso para os serviços Django.
- **redis**: Banco de dados em memória utilizado como broker de mensagens.
- **postgres**: Banco de dados PostgreSQL para armazenamento de dados.

### Volumes Utilizados

- `logs`: Para armazenar logs da aplicação.
- `static`: Para armazenar arquivos estáticos da aplicação.
- `media`: Para armazenar arquivos de mídia enviados pelos usuários.

### Rede

- **lineage_network**: Rede criada para interconectar todos os serviços.

#

<p align="center">
<img height="280" src="https://i.imgur.com/gdB0k6o.jpeg">
</p>

[![Supported Python versions](https://img.shields.io/pypi/pyversions/Django.svg)](https://www.djangoproject.com/)


## ⚡ Início Rápido

```bash
# Clone e instale em 3 comandos
git clone https://github.com/D3NKYT0/lineage.git
cd lineage
chmod +x install.sh && ./install.sh
```

Pronto! O script `install.sh` cuida de tudo automaticamente. 🎉

**Nota:** O projeto inclui um `.gitattributes` que garante line endings consistentes. Se você encontrar problemas com `git pull` detectando mudanças no `install.sh`, execute:

```bash
# Normalizar line endings (apenas uma vez)
git add --renormalize .
git commit -m "Normalizar line endings"
```

---

## 🚀 Como Instalar

### Instalação Rápida (Recomendado)

O PDL agora possui um script de instalação automatizado que facilita todo o processo:

```bash
# 1. Clone o repositório
git clone https://github.com/D3NKYT0/lineage.git
cd lineage

# 2. Execute o script de instalação
chmod +x install.sh
./install.sh
```

O script `install.sh` irá:
- ✅ Verificar pré-requisitos automaticamente
- ✅ Instalar Docker e Docker Compose
- ✅ Configurar ambiente Python
- ✅ Gerar arquivo `.env` interativamente
- ✅ Fazer build e iniciar os containers
- ✅ Aplicar migrações do banco de dados

### 📋 Mini Tutorial do install.sh

O `install.sh` é o ponto central para gerenciar o PDL. Ele oferece várias opções:

#### Instalação Completa (Primeira Vez)
```bash
./install.sh
# ou
./install.sh install
```
Executa a instalação completa do zero.

#### Menu Interativo
```bash
./install.sh menu
```
Abre um menu para escolher qual ação executar:
1. Instalação completa
2. Apenas setup
3. Apenas build
4. Atualizar repositório (git pull)
5. Backup do banco
6. Configurar proxy reverso
7. Instalar Nginx
8. Gerar arquivo .env
9. Configurar FTP para launcher
10. Configurar Nginx para launcher
11. Listar scripts disponíveis

#### Comandos Individuais

**Atualizar o projeto:**
```bash
./install.sh update        # Atualiza repositório e faz rebuild (recomendado)
# ou
./install.sh build         # Apenas rebuild (após git pull manual)
```

**Fazer backup:**
```bash
./install.sh backup          # Criar backup
./install.sh backup list     # Listar backups
./install.sh backup restore  # Restaurar backup
```

**Configurar domínio personalizado:**
```bash
./install.sh nginx-proxy
```

**Instalar/Atualizar Nginx:**
```bash
./install.sh install-nginx        # Versão mainline (padrão)
./install.sh install-nginx stable # Versão stable
```

**Gerar arquivo .env:**
```bash
./install.sh generate-env
```

**Configurar FTP para launcher:**
```bash
./install.sh setup-ftp
```

**Configurar Nginx com index of para launcher:**
```bash
./install.sh setup-nginx-launcher
```

**Atualizar repositório:**
```bash
./install.sh update
```

**Ver ajuda:**
```bash
./install.sh help
```

### 📝 Fluxo de Instalação Completa

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/D3NKYT0/lineage.git
   cd lineage
   ```

2. **Execute a instalação:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Configure o arquivo .env:**
   - O script irá gerar o `.env` interativamente
   - Você pode escolher quais categorias incluir (Email, AWS S3, Pagamentos, etc.)
   - Ou editar manualmente depois: `nano .env`

4. **Acesse o painel:**
   - URL: `http://localhost:6085`
   - Crie seu usuário administrador quando solicitado

### 🔄 Atualizar o Projeto

Quando uma nova versão for lançada:

```bash
# Opção 1: Usar o comando update do install.sh (recomendado)
./install.sh update

# Opção 2: Manualmente
git pull origin main
./install.sh build
```

**Dica:** Se você for staff, o painel mostrará automaticamente quando houver uma nova versão disponível no GitHub!

### 📚 Documentação Completa

Para mais detalhes sobre o `install.sh`, consulte:
- [Guia Completo do install.sh](docs/INSTALL_SH_GUIDE.md)


## 🔄 Como Atualizar o Projeto

### Atualização Simples (Recomendado)
```bash
cd /var/pdl/lineage  # ou caminho onde está o projeto
./install.sh update  # Atualiza repositório e faz rebuild automaticamente
```

### Atualização Manual
```bash
cd /var/pdl/lineage
git pull origin main
./install.sh build
```

### Com Backup Antes
```bash
cd /var/pdl/lineage
./install.sh backup        # Fazer backup primeiro
./install.sh update        # Atualizar código e fazer rebuild
```

## 💾 Como Fazer Backup do Banco de Dados

### Backup Manual
```bash
cd /var/pdl/lineage
./install.sh backup
```

### Backup Automático (Cron)
```bash
# Adicionar ao crontab para backup diário às 3h
crontab -e

# Adicionar esta linha (usando install.sh):
0 3 * * * cd /var/pdl/lineage && ./install.sh backup >> /var/pdl/backup.log 2>&1
```

### Outras Opções de Backup
```bash
# Listar backups disponíveis
./install.sh backup list

# Restaurar backup
./install.sh backup restore
```

## 🔔 Verificação de Atualizações

O PDL possui um sistema automático de verificação de atualizações:

- **Para Staffs**: O painel verifica automaticamente se há novas versões no GitHub
- **Indicador Visual**: 
  - 🟢 **Verde** = Versão atualizada
  - 🟡 **Amarelo** = Nova versão disponível
- **Notificação**: Um botão aparece no sidebar quando há atualização disponível
- **Instruções**: Ao clicar, um modal mostra como atualizar passo a passo

### Verificar Manualmente
```bash
# A verificação é automática no painel para staffs
# Mas você também pode verificar tags no GitHub:
curl https://api.github.com/repos/D3NKYT0/lineage/tags | grep '"name"'
```

## 🔧 Comandos Úteis

### Gerenciar o Projeto (via install.sh)

**Ver todos os scripts disponíveis:**
```bash
./install.sh list
```

**Ver ajuda completa:**
```bash
./install.sh help
```

**Menu interativo:**
```bash
./install.sh menu
```

### Gerenciar Containers Docker

**Nota:** Para operações básicas, use o `install.sh`. Para operações avançadas, use os comandos diretos:

```bash
# Iniciar containers (após build)
docker compose up -d

# Parar containers
docker compose down

# Ver logs
docker compose logs -f

# Reiniciar containers
docker compose restart

# Status dos containers
docker compose ps
```

### Verificar Status
```bash
# Status dos containers
docker compose ps

# Verificar versão atual
grep VERSION core/settings.py
```

### Scripts Disponíveis via install.sh

Todos os scripts podem ser executados através do `install.sh`:

- `./install.sh install` - Instalação completa
- `./install.sh setup` - Apenas setup inicial
- `./install.sh build` - Build e deploy
- `./install.sh update` - Atualizar repositório e rebuild
- `./install.sh backup` - Backup do banco de dados
- `./install.sh backup list` - Listar backups
- `./install.sh backup restore` - Restaurar backup
- `./install.sh nginx-proxy` - Configurar proxy reverso
- `./install.sh install-nginx` - Instalar/atualizar Nginx
- `./install.sh generate-env` - Gerar arquivo .env
- `./install.sh setup-ftp` - Configurar servidor FTP para launcher
- `./install.sh setup-nginx-launcher` - Configurar Nginx com index of para launcher
- `./install.sh list` - Listar todos os scripts
- `./install.sh help` - Ver ajuda completa


## Como testar (produção)

```bash
https://pdl.denky.dev.br/
```

## Sobre Mim
>Desenvolvedor - Daniel Amaral Recife/PE
- Emails:  contato@denky.dev.br
- Discord: denkyto


## Grupo de Staffs:

**Núcleo de Programação**

- Daniel Amaral (Desenvolvedor - FullStack/FullCycle)

**Apoio e Testers**

- Daniel Amaral (Desenvolvedor - FullStack/FullCycle)

**Gestão**

- Daniel Amaral (Desenvolvedor - FullStack/FullCycle)

## Estrutura do Código

O projeto é codificado utilizando uma estrutura simples e intuitiva, apresentada abaixo:

```bash
< RAIZ DO PROJETO >
   |
   |-- apps/
   |    |
   |    |-- api/                             # API REST para integrações externas
   |    |
   |    |-- main/
   |    |    |-- administrator/              # Painel administrativo e configurações
   |    |    |-- auditor/                    # Sistema de auditoria e logs
   |    |    |-- calendary/                  # Calendário de eventos e agendamentos
   |    |    |-- downloads/                  # Sistema de downloads (launcher, patches)
   |    |    |-- faq/                        # FAQ (Perguntas Frequentes)
   |    |    |-- home/                       # App principal - Dashboard e autenticação
   |    |    |-- licence/                    # Sistema de licenciamento e ativação
   |    |    |-- management/                 # Comandos customizados do Django
   |    |    |-- message/                    # Sistema de mensagens e amigos
   |    |    |-- news/                       # Notícias e Blog
   |    |    |-- notification/               # Sistema de notificações (push, email, in-app)
   |    |    |-- resources/                  # Recursos compartilhados e utilitários
   |    |    |-- social/                     # Rede social integrada e moderação
   |    |    |-- solicitation/               # Solicitações e Sistema de Suporte
   |    |
   |    |-- lineage/
   |    |    |-- accountancy/                # Contabilidade e registros financeiros
   |    |    |-- auction/                    # Sistema de leilões entre jogadores
   |    |    |-- games/                      # Minigames (roleta, caixas, dados, pesca)
   |    |    |-- inventory/                  # Gerenciamento de inventário e itens
   |    |    |-- marketplace/                # Marketplace de itens entre jogadores
   |    |    |-- payment/                    # Pagamentos (Mercado Pago, Stripe, PayPal)
   |    |    |-- reports/                    # Relatórios e estatísticas administrativas
   |    |    |-- roadmap/                    # Roadmap público de funcionalidades
   |    |    |-- server/                     # Gerenciamento e integração com servidor L2
   |    |    |-- shop/                       # Loja virtual de itens e serviços
   |    |    |-- tops/                       # Rankings (PvP, PK, Clan, Online)
   |    |    |-- wallet/                     # Carteira virtual e transações
   |    |    |-- wiki/                       # Wiki de itens, monstros e quests
   |    |
   |    |-- media_storage/                   # Gerenciamento de mídia e arquivos
   |
   |-- core/
   |    |-- settings.py                      # Configurações do projeto
   |    |-- urls.py                          # Roteamento principal
   |    |-- wsgi.py                          # Servidor WSGI (Gunicorn)
   |    |-- asgi.py                          # Servidor ASGI (Daphne)
   |    |-- celery.py                        # Configuração do Celery
   |    |-- *.py                             # Demais arquivos de configuração
   |
   |-- requirements.txt                      # Dependências Python do projeto
   |-- docker-compose.yml                    # Orquestração de containers
   |-- Dockerfile                            # Imagem Docker da aplicação
   |-- manage.py                             # Script de gerenciamento do Django
   |-- gunicorn-cfg.py                       # Configuração do Gunicorn
   |-- ...                                   # Demais arquivos
   |
   |-- ************************************************************************
```

<br />

## Como Customizar 

Quando um arquivo de template é carregado no controlador, o `Django` escaneia todos os diretórios de templates, começando pelos definidos pelo usuário, e retorna o primeiro encontrado ou um erro caso o template não seja encontrado. O tema utilizado para estilizar esse projeto inicial fornece os seguintes arquivos:

```bash
< ESTRUTURA DE TEMPLATES E TEMAS >

1. TEMPLATES BASE DO SISTEMA
   |-- templates/                            # Templates padrão do PDL
   |    |-- admin/                           # Customizações do Django Admin (Jazzmin)
   |    |-- config/                          # Páginas de configuração
   |    |-- errors/                          # Páginas de erro (400, 403, 404, 500)
   |    |-- includes/                        # Componentes reutilizáveis
   |    |    |-- head.html                   # Meta tags, favicon, CSS
   |    |    |-- nav.html                    # Navegação principal
   |    |    |-- sidebar.html                # Menu lateral (dashboard)
   |    |    |-- footer.html                 # Rodapé
   |    |    |-- scripts.html                # Scripts JavaScript
   |    |    |-- floating-notifications.html # Notificações flutuantes
   |    |    |-- analytics.html              # Scripts de analytics
   |    |-- layouts/                         # Layouts base
   |    |    |-- base.html                   # Layout principal (dashboard)
   |    |    |-- base-auth.html              # Layout para autenticação
   |    |    |-- base-default.html           # Layout padrão (landing page)
   |    |    |-- public.html                 # Layout para páginas públicas
   |    |-- public/                          # Páginas públicas
   |    |    |-- index.html                  # Landing page padrão
   |    |    |-- downloads.html              # Página de downloads
   |    |    |-- faq.html                    # FAQ padrão
   |    |    |-- news_index.html             # Lista de notícias
   |    |    |-- news_detail.html            # Detalhes da notícia
   |    |    |-- privacy_policy.html         # Política de privacidade
   |    |    |-- terms.html                  # Termos de serviço
   |    |    |-- user_agreement.html         # Acordo do usuário

2. SISTEMA DE TEMAS PERSONALIZADOS
   |-- themes/                               # Sistema de temas instaláveis
   |    |-- installed/                       # Temas instalados e ativos
   |    |    |
   |    |    |-- <slug-do-tema>/             # Diretório do tema (nome único)
   |    |    |    |
   |    |    |    |-- theme.json             # OBRIGATÓRIO - Metadados e configuração
   |    |    |    |-- base.html              # OBRIGATÓRIO - Template base do tema
   |    |    |    |
   |    |    |    |-- index.html             # Landing page customizada
   |    |    |    |-- news_index.html        # Lista de notícias (tema)
   |    |    |    |-- news_detail.html       # Detalhes da notícia (tema)
   |    |    |    |-- faq.html               # FAQ customizada
   |    |    |    |-- terms.html             # Termos de serviço (tema)
   |    |    |    |-- privacy_policy.html    # Política de privacidade (tema)
   |    |    |    |-- user_agreement.html    # Acordo do usuário (tema)
   |    |    |    |-- *.html                 # Outros templates customizados
   |    |    |    |
   |    |    |    |-- css/                   # Estilos do tema
   |    |    |    |    |-- style.css         # Estilos principais
   |    |    |    |    |-- custom.css        # Customizações adicionais
   |    |    |    |    |-- responsive.css    # Estilos responsivos
   |    |    |    |    |-- *.css             # Outros arquivos CSS
   |    |    |    |
   |    |    |    |-- js/                    # Scripts do tema
   |    |    |    |    |-- script.js         # Scripts principais
   |    |    |    |    |-- custom.js         # Scripts customizados
   |    |    |    |    |-- *.js              # Outros scripts
   |    |    |    |
   |    |    |    |-- images/                # Imagens e assets visuais
   |    |    |    |    |-- logo.png          # Logo do servidor
   |    |    |    |    |-- favicon.png       # Ícone do site
   |    |    |    |    |-- bg/               # Imagens de background
   |    |    |    |    |-- icons/            # Ícones diversos
   |    |    |    |    |-- gallery/          # Galeria de screenshots
   |    |    |    |    |-- characters/       # Imagens de personagens
   |    |    |    |    |-- *.png, *.jpg      # Outras imagens
   |    |    |    |
   |    |    |    |-- fonts/                 # Fontes customizadas (.woff, .ttf)
   |    |    |    |-- libs/                  # Bibliotecas JavaScript externas
   |    |    |    |-- video/                 # Vídeos e trailers (.mp4, .webm)
   |    |    |    |-- assets/                # Outros recursos (opcional)
   |    |    |
   |    |    |-- <outro-tema>/               # Outros temas instalados
   |    |         |-- (mesma estrutura)

3. FUNCIONAMENTO DO SISTEMA DE TEMAS
   - Upload via Django Admin como arquivo ZIP
   - Validação automática do theme.json e estrutura
   - Extração para /themes/installed/<slug>/
   - Apenas um tema ativo por vez
   - Variáveis internacionalizadas (PT, EN, ES)
   - Fallback automático para templates padrão
   - Hot-reload sem necessidade de restart

4. VARIÁVEIS DE TEMA (theme.json)
   - Suporte a múltiplos idiomas (valor_pt, valor_en, valor_es)
   - Tipos: string, integer, boolean, color
   - Acessíveis em todos os templates via context processor
   - Customizáveis via painel administrativo

📚 Documentação completa: docs/THEME_SYSTEM.md, docs/GUIDE_CREATE_THEME.md
   
|-- ************************************************************************
```
