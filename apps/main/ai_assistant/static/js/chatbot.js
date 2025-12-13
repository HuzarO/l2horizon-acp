/**
 * Chatbot WebSocket Client
 * Gerencia a conexão WebSocket e interface do chatbot de IA
 */

class ChatBotClient {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.isTyping = false;
        
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.solicitationSuggestion = document.getElementById('solicitationSuggestion');
        this.solicitationMessage = document.getElementById('solicitationMessage');
        this.btnCreateSolicitation = document.getElementById('btnCreateSolicitation');
        
        this.init();
    }

    init() {
        // Conectar WebSocket
        this.connect();
        
        // Event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
        });

        // Botão criar solicitação
        this.btnCreateSolicitation.addEventListener('click', () => {
            this.showCreateSolicitationModal();
        });
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chatbot/`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus('Conectado', true);
                console.log('WebSocket conectado');
                
                // Criar nova sessão
                this.createSession();
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.socket.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus('Desconectado', false);
                console.log('WebSocket desconectado');
                
                // Tentar reconectar após 3 segundos
                setTimeout(() => this.connect(), 3000);
            };
            
            this.socket.onerror = (error) => {
                console.error('Erro no WebSocket:', error);
                this.updateConnectionStatus('Erro de conexão', false);
            };
            
        } catch (error) {
            console.error('Erro ao conectar WebSocket:', error);
            this.updateConnectionStatus('Erro de conexão', false);
        }
    }

    updateConnectionStatus(text, connected) {
        if (this.connectionStatus) {
            this.connectionStatus.textContent = text;
            const statusDot = document.querySelector('.status-dot');
            if (statusDot) {
                statusDot.style.background = connected ? '#4ade80' : '#ef4444';
            }
        }
    }

    createSession() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'create_session'
            }));
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || !this.isConnected) {
            return;
        }

        // Adicionar mensagem do usuário na interface
        this.addMessage('user', message);
        
        // Limpar input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Enviar via WebSocket
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'message',
                message: message
            }));
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'welcome':
                this.addMessage('assistant', data.message);
                break;
                
            case 'message':
                this.addMessage('assistant', data.message.content, data.message.metadata);
                if (data.message.metadata && data.message.metadata.suggest_create_solicitation) {
                    this.showSolicitationSuggestion(data.message.metadata);
                }
                break;
                
            case 'typing':
                this.setTypingIndicator(data.status);
                break;
                
            case 'session_created':
                this.sessionId = data.session_id;
                break;
                
            case 'error':
                this.addMessage('system', `Erro: ${data.message}`);
                break;
                
            default:
                console.log('Tipo de mensagem desconhecido:', data.type);
        }
    }

    addMessage(role, content, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (role === 'user') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else if (role === 'assistant') {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        } else {
            avatar.innerHTML = '<i class="fas fa-info-circle"></i>';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Salvar metadados como data attribute para uso posterior
        if (metadata) {
            messageDiv.dataset.metadata = JSON.stringify(metadata);
        }
        
        // Processar conteúdo (markdown básico ou HTML)
        contentDiv.innerHTML = this.formatMessage(content);
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        contentDiv.appendChild(timeDiv);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Formatação básica de mensagem
        // Converter quebras de linha
        content = content.replace(/\n/g, '<br>');
        
        // Links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        // Negrito e itálico básico
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        return content;
    }

    setTypingIndicator(show) {
        this.isTyping = show;
        
        // Remover indicador existente
        const existing = document.getElementById('typingIndicator');
        if (existing) {
            existing.remove();
        }
        
        if (show) {
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typingIndicator';
            typingDiv.className = 'message assistant';
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
            
            const indicator = document.createElement('div');
            indicator.className = 'typing-indicator';
            indicator.innerHTML = '<span></span><span></span><span></span>';
            
            typingDiv.appendChild(avatar);
            typingDiv.appendChild(indicator);
            this.messagesContainer.appendChild(typingDiv);
            this.scrollToBottom();
        }
    }

    showSolicitationSuggestion(metadata) {
        if (!this.solicitationSuggestion || !metadata.suggest_create_solicitation) {
            return;
        }
        
        // Verificar se há mensagens suficientes na conversa (pelo menos 2 - user + assistant)
        const userMessages = this.messagesContainer.querySelectorAll('.message.user');
        const assistantMessages = this.messagesContainer.querySelectorAll('.message.assistant');
        
        // Só mostrar se houver pelo menos uma interação real
        if (userMessages.length < 1 || assistantMessages.length < 1) {
            return;
        }
        
        const categoryMap = {
            'technical': 'Técnico',
            'billing': 'Faturamento',
            'account': 'Conta',
            'game_support': 'Suporte ao Jogo',
            'bug_report': 'Relatório de Bug',
            'feature_request': 'Solicitação de Funcionalidade',
            'general': 'Geral',
            'security': 'Segurança',
            'performance': 'Performance',
            'other': 'Outros'
        };
        
        const priorityMap = {
            'low': 'Baixa',
            'medium': 'Média',
            'high': 'Alta',
            'urgent': 'Urgente',
            'critical': 'Crítica'
        };
        
        const category = categoryMap[metadata.category_suggestion] || metadata.category_suggestion || 'Geral';
        const priority = priorityMap[metadata.priority_suggestion] || metadata.priority_suggestion || 'Média';
        
        // Construir mensagem mais contextual
        let messageText = `Para continuarmos com essa questão, recomendamos criar uma solicitação de suporte `;
        
        if (metadata.suggestion_reason) {
            messageText += `(${metadata.suggestion_reason}). `;
        }
        
        messageText += `Categoria sugerida: **${category}** | Prioridade: **${priority}**`;
        
        this.solicitationMessage.innerHTML = messageText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        this.solicitationSuggestion.classList.add('show');
        this.scrollToBottom();
    }

    showCreateSolicitationModal() {
        // Obter última mensagem do usuário para sugerir título
        const userMessages = this.messagesContainer.querySelectorAll('.message.user');
        const lastUserMessage = userMessages[userMessages.length - 1];
        const suggestedTitle = lastUserMessage 
            ? lastUserMessage.querySelector('.message-content').textContent.trim().substring(0, 100)
            : '';
        
        // Obter metadados da última resposta da IA (se houver sugestão de categoria/prioridade)
        const assistantMessages = this.messagesContainer.querySelectorAll('.message.assistant');
        let category = '';
        let priority = '';
        
        // Tentar encontrar metadados na última mensagem da IA
        if (assistantMessages.length > 0) {
            const lastAssistantMsg = assistantMessages[assistantMessages.length - 1];
            const messageData = lastAssistantMsg.dataset.metadata;
            if (messageData) {
                try {
                    const metadata = JSON.parse(messageData);
                    category = metadata.category_suggestion || '';
                    priority = metadata.priority_suggestion || '';
                } catch (e) {
                    console.error('Erro ao parsear metadados:', e);
                }
            }
        }
        
        // Redirecionar para criar solicitação com dados pré-preenchidos
        const params = new URLSearchParams({
            from_chatbot: 'true',
            suggested_title: suggestedTitle
        });
        
        if (category) {
            params.append('category', category);
        }
        if (priority) {
            params.append('priority', priority);
        }
        
        window.location.href = `/app/solicitation/create/?${params.toString()}`;
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new ChatBotClient();
});
