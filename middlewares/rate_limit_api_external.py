import logging

from django_ratelimit.core import is_ratelimited, get_usage
from django.http import JsonResponse
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

    def process_request(self, request):
        logger.debug("Middleware foi chamada para verificar rate limit")
        
        for path, config in self.URL_RATE_LIMITS.items():
            logger.debug(f"Checking path {request.path} against {path}")
            
            # Verificar se o path corresponde (exato ou começa com o padrão)
            request_path = request.path.rstrip('/')
            pattern_path = path.rstrip('/')
            
            # Match exato ou match de prefixo (para rotas com parâmetros dinâmicos)
            path_matches = (
                request_path == pattern_path or
                request_path.startswith(pattern_path + '/') or
                (pattern_path.endswith('/') and request_path.startswith(pattern_path))
            )
            
            if path_matches:
                method = config.get("method", None)
                
                # Se method está especificado, verificar se corresponde
                if method and request.method != method:
                    continue

                # Preparar a chave para rate limiting
                key_type = config["key"]
                
                # Se for 'user_or_ip', usar função callable
                if key_type == 'user_or_ip':
                    def rate_limit_key_func(r):
                        if r.user.is_authenticated:
                            return f"user_{r.user.pk}"
                        x_forwarded_for = r.META.get('HTTP_X_FORWARDED_FOR')
                        if x_forwarded_for:
                            ip = x_forwarded_for.split(',')[0].strip()
                        else:
                            ip = r.META.get('REMOTE_ADDR', 'unknown')
                        return f"ip_{ip}"
                    rate_limit_key = rate_limit_key_func
                else:
                    # Usar string diretamente ('ip' ou 'user')
                    rate_limit_key = key_type
                
                # Preparar parâmetros para is_ratelimited
                rate_limit_kwargs = {
                    'request': request,
                    'group': config["group"],
                    'key': rate_limit_key,
                    'rate': config["rate"],
                    'increment': True,
                }
                
                # Adicionar method apenas se especificado
                if method:
                    rate_limit_kwargs['method'] = method

                was_limited = is_ratelimited(**rate_limit_kwargs)

                if was_limited:
                    logger.warning(f"Rate limit exceeded for path {path}")

                    # Preparar parâmetros para get_usage (usar a mesma chave)
                    usage_kwargs = {
                        'request': request,
                        'group': config["group"],
                        'key': rate_limit_key,
                        'rate': config["rate"],
                        'increment': False
                    }
                    
                    # Adicionar method apenas se especificado
                    if method:
                        usage_kwargs['method'] = method

                    usage = get_usage(**usage_kwargs)

                    reset_time = usage['time_left']

                    return JsonResponse(
                        {"error": "Rate limit exceeded", "retry_after": reset_time},
                        status=429
                    )
        return None
