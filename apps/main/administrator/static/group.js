const isLocalhost = ['127.0.0.1', 'localhost'].includes(window.location.hostname);
const wsUrlBase = window.location.origin.replace(/^http/, 'ws');
const chatSocket = new WebSocket(
    wsUrlBase + '/ws/chat/' + groupName + '/'
);    

chatSocket.onerror = function(e) {
    console.error('WebSocket error:', e);
};

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.error) {
        console.error('Chat error:', data.error);
        return;
    }
    appendMessage(data.message, data.sender, data.avatar_url, data.sender === currentUser, data.timestamp);
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
    showConnectionStatus('Desconectado', 'danger');
};

chatSocket.onopen = function(e) {
    console.log('Chat socket connected');
    showConnectionStatus('Conectado', 'success');
};

document.querySelector('#chat-message-input').focus();

document.querySelector('#chat-message-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.querySelector('#chat-message-submit').click();
    }
});

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    if (message.trim()) {
        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'message': message,
                'sender': currentUser
            }));
        } else {
            console.warn('WebSocket not open yet. Current state:', chatSocket.readyState);
            return; // evita InvalidStateError
        }
        appendMessage(message, currentUser, currentUserAvatar, true, null);
        messageInputDom.value = '';
        // Ajusta altura do textarea após limpar
        if (messageInputDom.tagName === 'TEXTAREA') {
            messageInputDom.style.height = 'auto';
        }
    }
};

function appendMessage(message, sender, avatarUrl, isSent, timestamp = null) {
    const messagesContainer = document.getElementById('messages-container');
    const chatLog = document.getElementById('chat-log');

    // Usa o timestamp fornecido ou gera um novo
    const messageTimestamp = timestamp || new Date().toLocaleString([], { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false
    });
    
    // Escapar todos os dados do usuário para prevenir XSS
    const senderName = escapeHtml(sender);
    const escapedAvatarUrl = escapeHtml(avatarUrl || '');
    const escapedMessage = escapeHtml(message);

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', isSent ? 'sent' : 'received');
    messageDiv.style.animation = 'fadeInUp 0.3s ease-out';

    const avatarContainer = document.createElement('div');
    avatarContainer.className = 'admin-avatar-container';
    const avatarImg = document.createElement('img');
    avatarImg.src = escapedAvatarUrl;
    avatarImg.alt = senderName;
    avatarImg.loading = 'lazy';
    avatarContainer.appendChild(avatarImg);

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';

    const senderStrong = document.createElement('strong');
    senderStrong.className = 'sender-name';
    senderStrong.textContent = senderName;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = messageTimestamp;

    messageHeader.appendChild(senderStrong);
    messageHeader.appendChild(timeSpan);

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = message; // Usar textContent em vez de innerHTML

    messageContent.appendChild(messageHeader);
    messageContent.appendChild(messageText);

    messageDiv.appendChild(avatarContainer);
    messageDiv.appendChild(messageContent);

    messagesContainer.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Função para escapar HTML e prevenir XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Função para mostrar status da conexão
function showConnectionStatus(message, type) {
    const statusDiv = document.getElementById('connection-status');
    if (statusDiv) {
        statusDiv.className = `alert alert-${type} alert-dismissible fade show`;
        // Escapar a mensagem para prevenir XSS
        const escapedMessage = escapeHtml(message);
        statusDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
            ${escapedMessage}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        statusDiv.style.display = 'block';
        
        // Auto-hide after 3 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.querySelector('#chat-message-input');
    const emojiButton = document.querySelector('#emoji-button');
    
    // Inicialize o Emoji Button
    const picker = new EmojiButton();

    // Mostra o seletor de emojis ao clicar no botão
    emojiButton.addEventListener('click', () => {
        picker.togglePicker(emojiButton);
    });

    // Insere o emoji no campo de texto quando selecionado
    picker.on('emoji', emoji => {
        chatInput.value += emoji;
        chatInput.focus(); // Foca no campo de texto após inserir o emoji
    });

    const chatLog = document.getElementById('chat-log');
    chatLog.scrollTop = chatLog.scrollHeight;

    // Auto-ajuste de altura do textarea conforme digita
    if (chatInput && chatInput.tagName === 'TEXTAREA') {
        const autoResize = () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
        };
        chatInput.addEventListener('input', autoResize);
        autoResize();
    }

    // Garantir que o input fique visível ao abrir o teclado no mobile
    if (chatInput) {
        chatInput.addEventListener('focus', () => {
            setTimeout(() => {
                chatLog.scrollTop = chatLog.scrollHeight;
                chatInput.scrollIntoView({ block: 'end', behavior: 'smooth' });
            }, 100);
        });
    }
});
