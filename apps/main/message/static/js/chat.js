document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.querySelector('#message-input');
    const emojiButton = document.querySelector('#emoji-button');
    const toggleButton = document.getElementById('toggle-friend-list');
    const friendListContent = document.getElementById('friend-list-content');
    const chatSection = toggleButton.closest('.row').querySelector('.col-lg-9');
    const sendMessageButton = document.getElementById('send-message');
    const messageInput = document.getElementById('message-input');
    const messageContainer = document.getElementById('message-container');
    const messageInputGroup = document.getElementById('message-input-group');
    const friendItems = document.querySelectorAll('.friend-item');

    let activeFriendId = null;
    let messageReloadInterval = null;

    // EMOJI PICKER
    const picker = new EmojiButton();
    emojiButton.addEventListener('click', () => picker.togglePicker(emojiButton));
    picker.on('emoji', emoji => {
        chatInput.value += emoji;
        chatInput.focus();
    });

    // TOGGLE AMIGOS
    toggleButton.addEventListener('click', () => {
        friendListContent.classList.toggle('hidden');
        chatSection.classList.toggle('col-lg-9');
        chatSection.classList.toggle('col-lg-12');
        toggleButton.classList.toggle('fa-plus');
        toggleButton.classList.toggle('fa-times');
    });

    // ENVIAR MENSAGEM
    sendMessageButton.addEventListener('click', sendMessage);

    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || !activeFriendId) return;
    
        fetch('/app/message/api/send-message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ message, friend_id: activeFriendId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Escapar HTML antes de processar quebras de linha
                const escapedMessage = escapeHtml(message);
                const formatted = escapedMessage.replace(/\n/g, '<br>');
                const escapedCurrentUser = escapeHtml(currentUser);
                const escapedAvatarUrl = escapeHtml(avatarUrl || '');
                
                const messageDiv = document.createElement('div');
                messageDiv.className = 'media mb-3 d-flex justify-content-end text-end';
                messageDiv.style.gap = '5px';
                
                const mediaBody = document.createElement('div');
                mediaBody.className = 'media-body';
                mediaBody.style.maxWidth = '80%';
                
                const messageContent = document.createElement('div');
                messageContent.className = 'current-user';
                
                const messageHeader = document.createElement('div');
                messageHeader.className = 'title-current';
                
                const usernameH6 = document.createElement('h6');
                usernameH6.className = 'm-0 fw-bold';
                usernameH6.textContent = escapedCurrentUser;
                
                const timestampSmall = document.createElement('small');
                timestampSmall.className = 'text-dark';
                timestampSmall.textContent = new Date().toLocaleString();
                
                messageHeader.appendChild(usernameH6);
                messageHeader.appendChild(timestampSmall);
                
                const messageP = document.createElement('p');
                messageP.className = 'm-0';
                messageP.style.fontSize = '12pt';
                messageP.style.wordBreak = 'break-word';
                messageP.style.whiteSpace = 'pre-wrap';
                messageP.innerHTML = formatted;
                
                messageContent.appendChild(messageHeader);
                messageContent.appendChild(messageP);
                mediaBody.appendChild(messageContent);
                messageDiv.appendChild(mediaBody);
                
                const avatarImg = document.createElement('img');
                avatarImg.src = escapedAvatarUrl;
                avatarImg.className = 'rounded-circle ms-3';
                avatarImg.alt = 'Avatar';
                avatarImg.width = 40;
                avatarImg.height = 40;
                messageDiv.appendChild(avatarImg);
                
                messageContainer.appendChild(messageDiv);
                messageInput.value = '';
                messageContainer.scrollTop = messageContainer.scrollHeight;
            }
        })
        .catch(console.error);
    }    

    // TECLA ENTER / SHIFT
    messageInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        } else if (e.key === 'Enter' && e.shiftKey) {
            e.preventDefault();
            const pos = messageInput.selectionStart;
            messageInput.value = messageInput.value.slice(0, pos) + '\n' + messageInput.value.slice(pos);
            messageInput.selectionEnd = pos + 1;
        }
    });

    // CARREGAR MENSAGENS
    friendItems.forEach(item => {
        const friendId = item.getAttribute('data-friend-id');

        item.addEventListener('click', () => {
            activeFriendId = friendId;
            loadMessages(friendId);

            friendItems.forEach(f => {
                f.classList.remove('active');
                f.querySelector('.friend-status')?.classList.remove('shadow-text');
            });

            item.classList.add('active');
            item.querySelector('.friend-status')?.classList.add('shadow-text');
            messageInputGroup.style.display = 'flex';

            if (messageReloadInterval) clearInterval(messageReloadInterval);
            messageReloadInterval = setInterval(() => loadMessages(friendId), 3000);
        });

        // CHECK ONLINE STATUS
        fetch(`/app/message/api/check-user-activity/${friendId}/`)
            .then(res => res.json())
            .then(data => {
                const status = item.querySelector('.friend-status');
                if (status) {
                    status.classList.toggle('text-success', data.is_online);
                    status.classList.toggle('text-danger', !data.is_online);
                    status.innerText = data.is_online ? 'Online' : 'Offline';
                }
            })
            .catch(console.error);
    });

    // Função para escapar HTML e prevenir XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function loadMessages(friendId) {
        fetch(`/app/message/api/load-messages/${friendId}/`)
            .then(res => res.json())
            .then(data => {
                messageContainer.innerHTML = '';

                data.messages.forEach(msg => {
                    const isUser = msg.sender.username === currentUser;
                    // Escapar HTML antes de processar quebras de linha
                    const escapedText = escapeHtml(msg.text);
                    const formatted = escapedText.replace(/\n/g, '<br>');
                    const escapedUsername = escapeHtml(msg.sender.username);
                    const escapedAvatarUrl = escapeHtml(msg.sender.avatar_url || '');
                
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `media mb-3 d-flex ${isUser ? 'justify-content-end text-end' : 'justify-content-start text-start'}`;
                    messageDiv.style.gap = '5px';
                    
                    if (!isUser) {
                        const avatarImg = document.createElement('img');
                        avatarImg.src = escapedAvatarUrl;
                        avatarImg.className = 'rounded-circle me-3';
                        avatarImg.alt = escapedUsername;
                        avatarImg.width = 40;
                        avatarImg.height = 40;
                        messageDiv.appendChild(avatarImg);
                    }
                    
                    const mediaBody = document.createElement('div');
                    mediaBody.className = 'media-body';
                    mediaBody.style.maxWidth = '80%';
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = isUser ? 'current-user' : 'current-friend';
                    
                    const messageHeader = document.createElement('div');
                    messageHeader.className = isUser ? 'title-current' : 'title-friend';
                    
                    const usernameH6 = document.createElement('h6');
                    usernameH6.className = 'm-0 fw-bold';
                    usernameH6.textContent = escapedUsername;
                    
                    const timestampSmall = document.createElement('small');
                    timestampSmall.className = 'text-dark';
                    timestampSmall.textContent = new Date(msg.timestamp).toLocaleString();
                    
                    messageHeader.appendChild(usernameH6);
                    messageHeader.appendChild(timestampSmall);
                    
                    const messageP = document.createElement('p');
                    messageP.className = 'm-0';
                    messageP.style.fontSize = '12pt';
                    messageP.style.wordBreak = 'break-word';
                    messageP.style.whiteSpace = 'pre-wrap';
                    messageP.innerHTML = formatted;
                    
                    messageContent.appendChild(messageHeader);
                    messageContent.appendChild(messageP);
                    mediaBody.appendChild(messageContent);
                    messageDiv.appendChild(mediaBody);
                    
                    if (isUser) {
                        const avatarImg = document.createElement('img');
                        avatarImg.src = escapedAvatarUrl;
                        avatarImg.className = 'rounded-circle ms-3';
                        avatarImg.alt = escapedUsername;
                        avatarImg.width = 40;
                        avatarImg.height = 40;
                        messageDiv.appendChild(avatarImg);
                    }
                    
                    messageContainer.appendChild(messageDiv);
                });                

                if (data.has_unread_messages) {
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                }
            })
            .catch(console.error);
    }

    // CONTADORES DE MENSAGENS NÃO LIDAS
    function updateUnreadCounts() {
        fetch('/app/message/api/get_unread_count/')
            .then(res => res.json())
            .then(response => {
                for (const [friendId, count] of Object.entries(response.unread_counts)) {
                    const el = document.getElementById(`unread-count-${friendId}`);
                    if (!el) continue;

                    el.textContent = count > 0 ? count : "";
                    el.classList.toggle('bg-success', count > 0);
                    el.classList.toggle('text-white', count > 0);
                }
            })
            .catch(err => console.error('Erro ao carregar contadores:', err));
    }

    setInterval(updateUnreadCounts, 5000);
    updateUnreadCounts();

    // STATUS DE ATIVIDADE
    function setUserActive() {
        fetch('/app/message/api/set-user-active/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(res => res.json())
        .then(data => console.log('Atividade registrada:', data))
        .catch(console.error);
    }

    setInterval(setUserActive, 300000);
    setUserActive();
});

// FILTRO DE AMIGOS
function filterFriends() {
    const input = document.getElementById('msg-friends').value.toLowerCase();
    const items = document.querySelectorAll('.friend-item');

    document.getElementById("smileys").style.display = "block";

    items.forEach(item => {
        const name = item.querySelector('.friend-name').textContent.toLowerCase();
        item.classList.toggle('desativar', !name.includes(input));
    });
}

// TABS
function openTab(evt, tabName) {
    document.querySelectorAll(".tab-content").forEach(el => el.style.display = "none");
    document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));

    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.classList.add("active");
}
