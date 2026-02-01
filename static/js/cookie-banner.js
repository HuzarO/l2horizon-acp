/**
 * Cookie Banner - Injeção automática via JavaScript
 * Funciona independente do tema usado
 */
(function() {
  'use strict';

  // Verifica se já aceitou os cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Verifica se já existe o banner (evita duplicação)
  if (document.getElementById('cookie-banner')) {
    return;
  }

  // Verifica se já aceitou
  const cookieConsent = getCookie('cookie_consent');
  if (cookieConsent === 'accepted') {
    return;
  }

  // Cria o HTML do banner
  function createBannerHTML() {
    // Tenta obter as traduções do Django ou usa padrão
    // Se não estiverem definidas, tenta buscar do DOM ou usa padrões
    const acceptText = window.djangoCookieAcceptText || document.querySelector('meta[name="cookie-accept-text"]')?.content || 'Aceitar';
    const messageText = window.djangoCookieMessageText || document.querySelector('meta[name="cookie-message-text"]')?.content || 'Este site utiliza cookies para melhorar sua experiência de navegação. Ao continuar navegando, você concorda com nossa política de cookies.';
    const learnMoreText = window.djangoCookieLearnMoreText || document.querySelector('meta[name="cookie-learn-more-text"]')?.content || 'Saiba mais';
    const privacyUrl = window.djangoCookiePrivacyUrl || document.querySelector('meta[name="cookie-privacy-url"]')?.content || '/privacy/';

    return `
      <div id="cookie-banner" class="cookie-banner" style="display: none;">
        <div class="cookie-banner-content">
          <div class="cookie-banner-text">
            <i class="fa-solid fa-cookie-bite" style="margin-right: 10px; font-size: 1.2em;"></i>
            <span>
              ${messageText}
              <a href="${privacyUrl}" target="_blank" style="color: #4a9eff; text-decoration: underline; margin-left: 5px;">
                ${learnMoreText}
              </a>
            </span>
          </div>
          <div class="cookie-banner-actions">
            <button type="button" id="accept-cookies-btn" class="cookie-btn cookie-btn-accept">
              ${acceptText}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Adiciona os estilos CSS
  function addBannerStyles() {
    if (document.getElementById('cookie-banner-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'cookie-banner-styles';
    style.textContent = `
      .cookie-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #fff;
        padding: 20px;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        border-top: 2px solid rgba(255, 255, 255, 0.1);
        animation: cookieSlideUp 0.3s ease-out;
        pointer-events: none; /* Permite cliques através do banner */
      }

      @keyframes cookieSlideUp {
        from {
          transform: translateY(100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }

      @keyframes cookieSlideDown {
        from {
          transform: translateY(0);
          opacity: 1;
        }
        to {
          transform: translateY(100%);
          opacity: 0;
        }
      }

      .cookie-banner-content {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        flex-wrap: wrap;
        pointer-events: auto; /* Permite interação com o conteúdo do banner */
      }

      .cookie-banner-text {
        flex: 1;
        min-width: 250px;
        display: flex;
        align-items: center;
        font-size: 14px;
        line-height: 1.6;
      }

      .cookie-banner-text a {
        color: #4a9eff;
        text-decoration: none;
        pointer-events: auto; /* Garante que o link seja clicável */
      }

      .cookie-banner-text a:hover {
        text-decoration: underline;
      }

      .cookie-banner-actions {
        display: flex;
        gap: 10px;
        flex-shrink: 0;
      }

      .cookie-btn {
        padding: 12px 24px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        pointer-events: auto !important; /* Garante que o botão seja clicável */
        position: relative;
        z-index: 10001; /* Garante que o botão esteja acima de outros elementos */
      }

      .cookie-btn-accept {
        background: linear-gradient(135deg, #4a9eff 0%, #357abd 100%);
        color: #fff;
      }

      .cookie-btn-accept:hover {
        background: linear-gradient(135deg, #357abd 0%, #2a5f8f 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 158, 255, 0.4);
      }

      .cookie-btn-accept:active {
        transform: translateY(0);
      }

      @media (max-width: 768px) {
        .cookie-banner {
          padding: 15px;
        }

        .cookie-banner-content {
          flex-direction: column;
          align-items: stretch;
        }

        .cookie-banner-text {
          margin-bottom: 15px;
          text-align: center;
        }

        .cookie-banner-actions {
          justify-content: center;
        }

        .cookie-btn {
          flex: 1;
          max-width: 200px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Função para aceitar cookies
  function acceptCookies() {
    const banner = document.getElementById('cookie-banner');
    if (!banner) return;

    // Tenta fazer requisição para o servidor
    const csrfToken = getCookie('csrftoken');
    const acceptUrl = window.djangoCookieAcceptUrl || document.querySelector('meta[name="cookie-accept-url"]')?.content || '/accept-cookies/';

    fetch(acceptUrl, {
      method: 'GET',
      headers: {
        'X-CSRFToken': csrfToken || '',
      },
      credentials: 'same-origin'
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      if (data.status === 'success') {
        hideBanner();
      } else {
        // Mesmo com erro, salva localmente e esconde
        document.cookie = 'cookie_consent=accepted; path=/; max-age=31536000'; // 1 ano
        hideBanner();
      }
    })
    .catch(function(error) {
      console.error('Erro ao aceitar cookies:', error);
      // Mesmo com erro, salva localmente e esconde
      document.cookie = 'cookie_consent=accepted; path=/; max-age=31536000'; // 1 ano
      hideBanner();
    });
  }

  // Função para esconder o banner
  function hideBanner() {
    const banner = document.getElementById('cookie-banner');
    if (banner) {
      banner.style.animation = 'cookieSlideDown 0.3s ease-out';
      setTimeout(function() {
        banner.style.display = 'none';
        banner.remove();
      }, 300);
    }
  }

  // Inicializa quando o DOM estiver pronto
  function init() {
    // Adiciona estilos
    addBannerStyles();

    // Cria e adiciona o banner ao body
    const bannerHTML = createBannerHTML();
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = bannerHTML;
    const banner = tempDiv.firstElementChild;
    document.body.appendChild(banner);

    // Usa event delegation no banner para garantir que funcione sempre
    // Isso funciona mesmo se o botão for adicionado dinamicamente
    banner.addEventListener('click', function(e) {
      const target = e.target;
      if (target && (target.id === 'accept-cookies-btn' || target.closest('#accept-cookies-btn'))) {
        e.preventDefault();
        e.stopPropagation();
        acceptCookies();
      }
    });

    // Também adiciona event listener direto no botão como fallback
    function attachButtonListener() {
      const acceptBtn = document.getElementById('accept-cookies-btn');
      if (acceptBtn && !acceptBtn.dataset.listenerAttached) {
        acceptBtn.dataset.listenerAttached = 'true';
        acceptBtn.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          acceptCookies();
        });
      }
    }

    // Tenta anexar o listener imediatamente
    attachButtonListener();

    // Mostra o banner após um pequeno delay
    setTimeout(function() {
      banner.style.display = 'block';
      // Tenta anexar o listener novamente após mostrar o banner
      attachButtonListener();
    }, 1000);
  }

  // Aguarda o DOM estar pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM já está pronto
    init();
  }
})();

