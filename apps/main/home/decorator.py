import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse
from django_otp.decorators import otp_required
from functools import wraps

logger = logging.getLogger(__name__)


def conditional_otp_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            # Log para debug
            logger.info(f"[conditional_otp_required] Path: {request.path}")
            logger.info(f"[conditional_otp_required] User authenticated: {request.user.is_authenticated}")
            logger.info(f"[conditional_otp_required] User: {request.user}")
            logger.info(f"[conditional_otp_required] Session key: {request.session.session_key if hasattr(request, 'session') else 'No session'}")
            logger.info(f"[conditional_otp_required] Session exists: {hasattr(request, 'session')}")
            
            # Verifica autenticação manualmente (mais explícito que @login_required)
            is_authenticated = request.user.is_authenticated
            logger.info(f"[conditional_otp_required] is_authenticated check result: {is_authenticated}")
            
            if not is_authenticated:
                logger.warning(f"[conditional_otp_required] Usuário não autenticado - redirecionando para login")
                path = request.get_full_path()
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(path)
            
            logger.info(f"[conditional_otp_required] Verificando 2FA...")
            # Verifica se o usuário ativou 2FA e ainda não está verificado via OTP
            is_2fa_enabled = getattr(request.user, 'is_2fa_enabled', False)
            is_verified = True
            try:
                if hasattr(request.user, 'is_verified'):
                    is_verified = request.user.is_verified()
            except Exception as e:
                logger.warning(f"[conditional_otp_required] Erro ao verificar OTP: {e}")
                is_verified = True  # Assume verificado se houver erro
                
            logger.info(f"[conditional_otp_required] 2FA enabled: {is_2fa_enabled}, Verified: {is_verified}")
            
            if is_2fa_enabled and not is_verified:
                logger.info(f"[conditional_otp_required] Usuário autenticado mas OTP não verificado - redirecionando para verify_2fa")
                # Redireciona para a página de verificação OTP em vez de usar otp_required
                # que redirecionaria para login
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(f"{reverse('verify_2fa')}?next={request.get_full_path()}")
            
            logger.info(f"[conditional_otp_required] Chamando view_func - TUDO OK!")
            result = view_func(request, *args, **kwargs)
            logger.info(f"[conditional_otp_required] View retornou: {type(result)}, status: {getattr(result, 'status_code', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"[conditional_otp_required] ERRO: {e}", exc_info=True)
            raise
    return _wrapped_view
