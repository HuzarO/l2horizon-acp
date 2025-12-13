# Assistente Virtual de IA - PDL

Sistema de pré-atendimento com IA integrado ao Painel Definitivo Lineage (PDL).

## 🎯 Funcionalidades

- **Chat em tempo real** via WebSocket com interface moderna
- **Integração com IA** usando Anthropic Claude para respostas inteligentes
- **Integração com FAQ** - utiliza FAQs públicas para responder perguntas frequentes
- **Sugestão automática de solicitações** - identifica quando criar uma solicitação de suporte
- **Histórico de conversas** - todas as conversas são salvas para referência futura
- **Categorização inteligente** - sugere categoria e prioridade para solicitações

## 🚀 Configuração

### 1. Variáveis de Ambiente

Adicione a chave da API da Anthropic no arquivo `.env`:

```env
ANTHROPIC_API_KEY=sua_chave_aqui
```

Ou configure diretamente em `settings.py`:

```python
ANTHROPIC_API_KEY = 'sua_chave_aqui'
```

### 2. Migrações do Banco de Dados

Execute as migrações para criar as tabelas necessárias:

```bash
python manage.py makemigrations ai_assistant
python manage.py migrate
```

### 3. Configuração do WebSocket

O WebSocket já está configurado no `core/asgi.py`. Certifique-se de que o servidor ASGI (Daphne) está rodando:

```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

Ou use o Docker Compose que já está configurado.

## 📖 Uso

### Acessando o Chatbot

Após fazer login, acesse:

```
/app/ai-assistant/
```

### Como Funciona

1. **Usuário faz uma pergunta** no chat
2. **IA analisa** a pergunta usando:
   - FAQs públicas do sistema
   - Contexto de categorias e prioridades de solicitação
   - Histórico da conversa
3. **IA responde** de forma inteligente e contextualizada
4. **Se necessário**, sugere criar uma solicitação de suporte com:
   - Categoria sugerida
   - Prioridade sugerida
   - Contexto da conversa

### Criar Solicitação a partir do Chat

Quando a IA sugerir criar uma solicitação:

1. Clique no botão "Criar Solicitação"
2. Você será redirecionado para o formulário de criação
3. Os dados sugeridos pela IA serão pré-preenchidos (se implementado)

## 🔧 Estrutura do Código

```
apps/main/ai_assistant/
├── models.py          # ChatSession, ChatMessage
├── services.py        # AIAssistantService - lógica da IA
├── consumers.py       # ChatBotConsumer - WebSocket handler
├── views.py           # Views Django
├── urls.py            # URLs do app
├── admin.py           # Admin Django
├── routing.py         # WebSocket routing
├── templates/         # Templates HTML
├── static/            # CSS e JavaScript
└── migrations/        # Migrações do banco
```

## 🎨 Personalização

### Ajustar Comportamento da IA

Edite o método `create_system_prompt()` em `services.py` para personalizar o comportamento da IA.

### Modificar Interface

Os estilos estão em:
- Template: `templates/pages/chatbot.html`
- CSS: `static/css/chatbot.css`
- JavaScript: `static/js/chatbot.js`

### Adicionar FAQs

As FAQs são carregadas automaticamente do app `faq`. Certifique-se de ter FAQs públicas cadastradas.

## 🔒 Segurança

- Apenas usuários autenticados podem acessar o chatbot
- Cada sessão está vinculada ao usuário logado
- WebSocket usa autenticação via `AuthMiddlewareStack`
- Mensagens são armazenadas no banco de dados com controle de acesso

## 📊 Monitoramento

O admin Django permite visualizar:
- Todas as sessões de chat
- Todas as mensagens trocadas
- Tokens usados pela IA
- Metadados das mensagens

Acesse: `/admin/ai_assistant/`

## 🐛 Troubleshooting

### WebSocket não conecta

1. Verifique se o servidor ASGI está rodando
2. Verifique se o routing está configurado em `core/asgi.py`
3. Verifique os logs do servidor

### IA não responde

1. Verifique se `ANTHROPIC_API_KEY` está configurada
2. Verifique os logs para erros de API
3. Verifique se há créditos na conta Anthropic

### FAQs não aparecem nas respostas

1. Verifique se existem FAQs públicas cadastradas
2. Verifique o idioma configurado (pt, en, es)
3. Verifique os logs para erros ao buscar FAQs

## 🔄 Próximas Melhorias

- [ ] Suporte a múltiplos idiomas nas respostas da IA
- [ ] Interface de criação de solicitação integrada no chat
- [ ] Análise de sentimento para priorizar urgências
- [ ] Respostas rápidas (quick replies)
- [ ] Upload de arquivos/imagens no chat
- [ ] Estatísticas e analytics de uso

## 📝 Licença

Este módulo faz parte do projeto PDL e segue a mesma licença do projeto principal.
