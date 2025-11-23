# Painel Definitivo Lineage [1.16](https://pdl.denky.dev.br)

<img align="right" height="180" src="https://i.imgur.com/0tL4OQ7.png"/>

O PDL é um painel que nasceu com a missão de oferecer ferramentas poderosas para administradores de servidores privados de Lineage 2. Inicialmente voltado à análise de riscos e estabilidade dos servidores, o projeto evoluiu e se consolidou como uma solução completa para prospecção, gerenciamento e operação de servidores — tudo em código aberto.

## Tecnologias Utilizadas

- **Django**: Framework web principal que permite a construção de aplicações rapidamente, com suporte a autenticação, gerenciamento de banco de dados e muito mais.
- **Daphne**: Servidor WSGI/ASGI responsável por servir a aplicação Django, oferecendo alta performance e capacidade para lidar com múltiplas requisições simultâneas.
- **Celery**: Biblioteca que permite a execução de tarefas assíncronas em segundo plano, como envio de e-mails e processamento de dados.
- **Redis**: Sistema de gerenciamento de dados em memória utilizado como broker de mensagens para o Celery, melhorando o desempenho da aplicação.
- **Nginx**: Servidor web reverso que gerencia requisições HTTP e serve arquivos estáticos e de mídia.
- **Docker**: Utilizado para containerização da aplicação, garantindo consistência e facilidade de deployment em diferentes ambientes.
- **Docker Compose**: Ferramenta que orquestra múltiplos containers, facilitando a configuração e execução dos serviços.

## Estrutura do Projeto

### Serviços Definidos no Docker Compose

- **site**: Serviço principal que roda o Django com Daphne.
- **celery**: Worker do Celery que processa tarefas em segundo plano.
- **celery-beat**: Agendador de tarefas do Celery que executa tarefas em horários programados.
- **flower**: Interface de monitoramento para o Celery.
- **nginx**: Servidor web que atua como proxy reverso para o serviço Django.
- **redis**: Banco de dados em memória utilizado como broker de mensagens.

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
4. Backup do banco
5. Configurar proxy reverso
6. Instalar Nginx
7. Gerar arquivo .env
8. Listar scripts disponíveis

#### Comandos Individuais

**Atualizar o projeto (após git pull):**
```bash
./install.sh build
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
# 1. Atualizar código
git pull origin main

# 2. Rebuild e deploy
./install.sh build
```

**Dica:** Se você for staff, o painel mostrará automaticamente quando houver uma nova versão disponível no GitHub!

### 📚 Documentação Completa

Para mais detalhes sobre o `install.sh`, consulte:
- [Guia Completo do install.sh](docs/INSTALL_SH_GUIDE.md)


## 🔄 Como Atualizar o Projeto

### Atualização Simples
```bash
cd /var/pdl/lineage  # ou caminho onde está o projeto
git pull origin main
./install.sh build
```

### Com Backup Antes
```bash
cd /var/pdl/lineage
./install.sh backup        # Fazer backup primeiro
git pull origin main        # Atualizar código
./install.sh build          # Rebuild e deploy
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

# Adicionar esta linha:
0 3 * * * cd /var/pdl/lineage && bash setup/backup.sh >> /var/pdl/backup.log 2>&1
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

### Gerenciar Containers
```bash
# Iniciar containers
docker compose up -d

# Parar containers
docker compose down

# Ver logs
docker compose logs -f

# Reiniciar containers
docker compose restart
```

### Verificar Status
```bash
# Status dos containers
docker compose ps

# Verificar versão atual
grep VERSION core/settings.py
```

### Scripts Disponíveis
```bash
# Ver todos os scripts disponíveis
./install.sh list

# Ver ajuda completa
./install.sh help
```


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
   |    |-- main/
   |    |    |-- administrator/              # Administração
   |    |    |-- auditor/                    # Auditoria do sistema
   |    |    |-- faq/                        # FAQ (Perguntas Frequentes)
   |    |    |-- home/                       # App principal - Página inicial
   |    |    |-- message/                    # Mensagens e Amigos
   |    |    |-- news/                       # Notícias e Blog
   |    |    |-- notification/               # Notificações do sistema
   |    |    |-- solicitation/               # Solicitações e Suporte
   |    |
   |    |-- lineage/
   |    |    |-- accountancy/                # Módulo de contabilidade e registros financeiros do servidor Lineage 2
   |    |    |-- auction/                    # Sistema de leilões de itens entre jogadores no servidor Lineage 2
   |    |    |-- games/                      # Funcionalidades relacionadas a minigames, roletas e caixas de prêmios
   |    |    |-- inventory/                  # Gerenciamento de inventário dos personagens e movimentações de itens
   |    |    |-- payment/                    # Integração com sistemas de pagamento (ex: PayPal) para compras no servidor
   |    |    |-- reports/                    # Geração de relatórios administrativos e estatísticas do servidor
   |    |    |-- server/                     # Ferramentas de administração e monitoramento do status do servidor Lineage 2
   |    |    |-- shop/                       # Loja virtual de itens e serviços do servidor Lineage 2
   |    |    |-- wallet/                     # Sistema de carteira virtual para saldo e transações dos jogadores
   |
   |-- core/
   |    |-- settings.py                      # Configurações do projeto
   |    |-- urls.py                          # Roteamento do projeto
   |    |-- *.py                             # Demais Arquivos
   |
   |-- requirements.txt                      # Dependências do projeto
   |-- manage.py                             # Script de inicialização do Django
   |-- ...                                   # Demais Arquivos
   |
   |-- ************************************************************************
```

<br />

## Como Customizar 

Quando um arquivo de template é carregado no controlador, o `Django` escaneia todos os diretórios de templates, começando pelos definidos pelo usuário, e retorna o primeiro encontrado ou um erro caso o template não seja encontrado. O tema utilizado para estilizar esse projeto inicial fornece os seguintes arquivos:

```bash
< RAIZ_DA_BIBLIOTECA_UI >                      
   |
   |-- templates/                     # Pasta Raiz dos Templates
   |    |          
   |    |-- accounts_custom/          # (pasta no app home)    
   |    |    |-- auth-signin.html     # Página de Login
   |    |    |-- auth-signup.html     # Página de Cadastro
   |    |    |-- *.html               # Demais Paginas
   |    |
   |    |-- includes/       
   |    |    |-- footer.html          # Componente de Rodapé
   |    |    |-- sidebar.html         # Componente da Barra Lateral
   |    |    |-- navigation.html      # Barra de Navegação
   |    |    |-- scripts.html         # Componente de Scripts
   |    |    |-- *.html               # Demais includes
   |    |
   |    |-- layouts/       
   |    |    |-- base.html            # Página Mestra
   |    |    |-- base-auth.html       # Página Mestra para Páginas de Autenticação
   |    |    |-- *.html               # Demais layouts
   |    |
   |    |-- pages/       
   |         |-- *.html               # Todas as outras páginas
   |    
   |-- ************************************************************************
```
