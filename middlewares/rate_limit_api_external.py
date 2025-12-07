import logging

from django_ratelimit.core import is_ratelimited, get_usage
from django.http import JsonResponse, HttpResponse
from utils.urls_rate_limits import URL_RATE_LIMITS_DICT


logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware para aplicar rate limiting em URLs específicas com configurações customizadas.
    """

    URL_RATE_LIMITS = URL_RATE_LIMITS_DICT

    def __init__(self, get_response):
        """
        Middleware de inicialização.
        Recebe get_response, necessário para os middlewares do Django.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Método chamado para processar as requisições.
        """
        response = self.process_request(request)
        if response:
            return response

        # Continue com o fluxo normal
        return self.get_response(request)

    def is_browser_request(self, request):
        """
        Detecta se a requisição vem de um navegador.
        Verifica o header Accept para ver se aceita HTML/text.
        """
        accept_header = request.META.get('HTTP_ACCEPT', '').lower()
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Se aceita HTML/text/html, provavelmente é navegador
        accepts_html = 'text/html' in accept_header or 'text/*' in accept_header
        
        # Se não aceita application/json explicitamente e aceita HTML, é navegador
        accepts_json_only = 'application/json' in accept_header and not accepts_html
        
        # User-Agent comum de navegadores
        is_browser_ua = any(browser in user_agent for browser in [
            'mozilla', 'chrome', 'safari', 'firefox', 'edge', 'opera', 'webkit'
        ])
        
        # Se não tem User-Agent ou é claramente um navegador, retorna HTML
        if accepts_html or (is_browser_ua and not accepts_json_only):
            return True
        
        # API clients geralmente especificam apenas JSON ou têm User-Agent específico
        if accepts_json_only or not is_browser_ua:
            return False
        
        # Padrão: se tem User-Agent de navegador, assume navegador
        return is_browser_ua

    def format_time_remaining(self, seconds):
        """
        Formata o tempo restante de forma amigável.
        """
        if seconds < 60:
            return f"{int(seconds)} segundo{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            if secs == 0:
                return f"{minutes} minuto{'s' if minutes != 1 else ''}"
            return f"{minutes} minuto{'s' if minutes != 1 else ''} e {secs} segundo{'s' if secs != 1 else ''}"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            if minutes == 0:
                return f"{hours} hora{'s' if hours != 1 else ''}"
            return f"{hours} hora{'s' if hours != 1 else ''} e {minutes} minuto{'s' if minutes != 1 else ''}"

    def get_rate_limit_html(self, rate_config, reset_time):
        """
        Gera uma página HTML bonita e informativa para rate limit.
        """
        rate = rate_config.get('rate', 'N/A')
        time_remaining = self.format_time_remaining(reset_time)
        
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Limite de Requisições Excedido - Rate Limit</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            padding: 50px 40px;
            text-align: center;
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .icon {{
            width: 120px;
            height: 120px;
            margin: 0 auto 30px;
            background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7);
            }}
            50% {{
                transform: scale(1.05);
                box-shadow: 0 0 0 20px rgba(255, 107, 107, 0);
            }}
        }}
        
        .icon svg {{
            width: 60px;
            height: 60px;
            fill: white;
        }}
        
        h1 {{
            color: #2d3748;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 15px;
        }}
        
        .subtitle {{
            color: #718096;
            font-size: 18px;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        
        .info-box {{
            background: #f7fafc;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            text-align: left;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .info-item:last-child {{
            margin-bottom: 0;
        }}
        
        .info-label {{
            color: #4a5568;
            font-weight: 600;
            font-size: 14px;
        }}
        
        .info-value {{
            color: #2d3748;
            font-weight: 700;
            font-size: 16px;
        }}
        
        .timer {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin: 30px 0;
            font-size: 24px;
            font-weight: 700;
        }}
        
        .message {{
            color: #718096;
            font-size: 16px;
            line-height: 1.8;
            margin-top: 30px;
        }}
        
        .actions {{
            margin-top: 40px;
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 14px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #e2e8f0;
            color: #4a5568;
        }}
        
        .btn-secondary:hover {{
            background: #cbd5e0;
        }}
        
        @media (max-width: 600px) {{
            .container {{
                padding: 30px 20px;
            }}
            
            h1 {{
                font-size: 24px;
            }}
            
            .subtitle {{
                font-size: 16px;
            }}
            
            .icon {{
                width: 100px;
                height: 100px;
            }}
            
            .icon svg {{
                width: 50px;
                height: 50px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">
            <svg viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
        </div>
        
        <h1>Limite de Requisições Excedido</h1>
        <p class="subtitle">Você fez muitas requisições em um curto período de tempo</p>
        
        <div class="timer">
            ⏱️ Tente novamente em: {time_remaining}
        </div>
        
        <div class="info-box">
            <div class="info-item">
                <span class="info-label">Limite de taxa:</span>
                <span class="info-value">{rate}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Tempo restante:</span>
                <span class="info-value">{time_remaining}</span>
            </div>
        </div>
        
        <p class="message">
            Por favor, aguarde antes de fazer novas requisições. Este limite ajuda a manter 
            o serviço estável e disponível para todos os usuários.
        </p>
        
        <div class="actions">
            <button class="btn btn-primary" onclick="window.location.reload()">
                ↻ Tentar Novamente
            </button>
            <button class="btn btn-secondary" onclick="window.history.back()">
                ← Voltar
            </button>
        </div>
    </div>
    
    <script>
        // Auto-refresh quando o tempo expirar (aproximadamente)
        setTimeout(function() {{
            const reloadBtn = document.querySelector('.btn-primary');
            reloadBtn.textContent = '⏱️ Tempo esgotado! Clique para recarregar';
            reloadBtn.style.background = 'linear-gradient(135deg, #48bb78, #38a169)';
        }}, {int(reset_time * 1000)});
    </script>
</body>
</html>
"""
        return html

    def process_request(self, request):
        logger.debug("Middleware foi chamada para verificar rate limit")
        
        for path, config in self.URL_RATE_LIMITS.items():
            logger.debug(f"Checking path {request.path} against {path}")
            # Suporta match exato ou match com parâmetros dinâmicos (quando path termina com /)
            path_match = (
                request.path.rstrip('/') == path.rstrip('/') or
                (path.endswith('/') and request.path.startswith(path))
            )
            if path_match:

                method = config.get("method", "GET")

                was_limited = is_ratelimited(
                    request=request,
                    group=config["group"],
                    key=config["key"],
                    rate=config["rate"],
                    method=method,
                    increment=True,
                )

                if was_limited:
                    logger.warning(f"Rate limit exceeded for path {path}")

                    usage = get_usage(
                        request=request,
                        group=config["group"],
                        key=config["key"],
                        rate=config["rate"],
                        method=method,
                        increment=False
                    )

                    reset_time = usage['time_left']

                    # Para rotas de autenticação web, sempre retornar HTML
                    # Para outras rotas, detecta se é requisição de navegador ou app
                    group = config.get('group', '')
                    is_auth_web = group == 'auth-web'
                    
                    if is_auth_web or self.is_browser_request(request):
                        # Retorna HTML bonito para navegador ou rotas web
                        html_content = self.get_rate_limit_html(config, reset_time)
                        return HttpResponse(html_content, status=429, content_type='text/html')
                    else:
                        # Retorna JSON para apps/APIs
                        return JsonResponse(
                            {
                                "error": "Rate limit exceeded",
                                "message": "Limite de requisições excedido. Tente novamente mais tarde.",
                                "retry_after": reset_time,
                                "rate": config.get('rate', 'N/A')
                            },
                            status=429
                        )
        return None
