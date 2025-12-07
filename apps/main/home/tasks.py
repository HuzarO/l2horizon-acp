import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


def execute_task_sync_or_async(task_func, *args, **kwargs):
    """
    Helper que executa task de forma síncrona em DEBUG ou assíncrona em produção.
    Útil para tasks que não são do Beat (agendadas).
    
    Em DEBUG: executa síncronamente usando .apply() para manter contexto do Celery
    Em produção: executa assincronamente usando .delay()
    """
    if settings.DEBUG:
        # Em DEBUG, executa síncronamente mas mantém contexto do Celery
        # .apply() executa de forma síncrona mas preserva bind=True e outros recursos
        return task_func.apply(args=args, kwargs=kwargs)
    else:
        # Em produção, executa assincronamente
        return task_func.delay(*args, **kwargs)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minuto entre tentativas
    time_limit=300,  # 5 minutos timeout
    soft_time_limit=240,  # 4 minutos soft timeout
)
def send_email_task(self, subject, message, from_email, recipient_list):
    """
    Envia email de forma assíncrona usando Python puro (smtplib)
    Com retry automático em caso de falha
    """
    # Configurações de email do ambiente
    email_enable = os.getenv('CONFIG_EMAIL_ENABLE', 'False').lower() in ['true', '1', 'yes']
    
    if not email_enable:
        logger.info(f"[EMAIL DISABLED] Subject: {subject} | To: {recipient_list}")
        return False
    
    email_host = os.getenv('CONFIG_EMAIL_HOST')
    email_user = os.getenv('CONFIG_EMAIL_HOST_USER')
    email_password = os.getenv('CONFIG_EMAIL_HOST_PASSWORD')
    email_port = int(os.getenv('CONFIG_EMAIL_PORT', 587))
    email_use_tls = os.getenv('CONFIG_EMAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
    default_from = os.getenv('CONFIG_DEFAULT_FROM_EMAIL', email_user)
    
    # Validações
    if not all([email_host, email_user, email_password]):
        logger.error("[EMAIL ERROR] Missing SMTP configuration")
        return False
    
    if not recipient_list:
        logger.error("[EMAIL ERROR] No recipients provided")
        return False
    
    # Configurar email
    msg = MIMEMultipart()
    msg['From'] = from_email or default_from
    msg['To'] = ', '.join(recipient_list) if isinstance(recipient_list, list) else recipient_list
    msg['Subject'] = subject
    
    # Adicionar corpo do email
    msg.attach(MIMEText(message, 'plain', 'utf-8'))
    
    try:
        # Conectar ao servidor SMTP
        logger.info(f"[EMAIL] Connecting to {email_host}:{email_port}")
        server = smtplib.SMTP(email_host, email_port, timeout=30)
        
        # Habilitar TLS se configurado
        if email_use_tls:
            logger.debug("[EMAIL] Starting TLS")
            server.starttls()
        
        # Login
        logger.debug(f"[EMAIL] Logging in as {email_user}")
        server.login(email_user, email_password)
        
        # Enviar email
        text = msg.as_string()
        server.sendmail(
            from_email or default_from, 
            recipient_list, 
            text
        )
        
        # Fechar conexão
        server.quit()
        
        logger.info(f"[EMAIL SUCCESS] Sent to {recipient_list}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[EMAIL ERROR] Authentication failed: {e}")
        # Retry em caso de erro de autenticação (pode ser temporário)
        raise self.retry(exc=e, countdown=60)
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"[EMAIL ERROR] Recipients refused: {e}")
        # Não retry para destinatários inválidos
        return False
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"[EMAIL ERROR] Server disconnected: {e}")
        # Retry em caso de desconexão
        raise self.retry(exc=e, countdown=60)
    except smtplib.SMTPException as e:
        logger.error(f"[EMAIL ERROR] SMTP error: {e}")
        # Retry para outros erros SMTP
        raise self.retry(exc=e, countdown=60)
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Unexpected error: {e}")
        # Retry para erros inesperados
        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_expired_sessions():
    """Remove sessões expiradas do banco de dados"""
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    try:
        expired = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired.count()
        expired.delete()
        
        logger.info(f"Removidas {count} sessões expiradas")
        return count
    except Exception as e:
        logger.error(f"Erro ao limpar sessões expiradas: {e}")
        return 0


@shared_task
def cleanup_old_logs(days=30):
    """Remove logs antigos do sistema"""
    from django.utils import timezone
    from datetime import timedelta
    import os
    
    try:
        cutoff = timezone.now() - timedelta(days=days)
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        
        if not os.path.exists(log_dir):
            logger.info("Diretório de logs não existe")
            return 0
        
        removed = 0
        total_size = 0
        
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            if os.path.isfile(filepath):
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff.timestamp():
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        removed += 1
                        total_size += file_size
                except Exception as e:
                    logger.error(f"Erro ao remover log {filename}: {e}")
        
        size_mb = total_size / (1024 * 1024)
        logger.info(f"Removidos {removed} arquivos de log antigos ({size_mb:.2f} MB liberados)")
        return removed
    except Exception as e:
        logger.error(f"Erro ao limpar logs antigos: {e}")
        return 0


@shared_task(bind=True, max_retries=2)
def process_avatar_image_task(self, user_id, avatar_path):
    """Processa avatar de forma assíncrona"""
    from apps.main.home.models import User
    from utils.media_validators import process_avatar_image
    from utils.notifications import send_notification
    
    try:
        user = User.objects.get(id=user_id)
        
        # Processa a imagem
        processed_path = process_avatar_image(avatar_path, size=400)
        
        logger.info(f"Avatar processado para usuário {user_id}: {processed_path}")
        
        # Notifica o usuário
        try:
            send_notification(
                user=user,
                notification_type='user',
                message='Seu avatar foi processado e otimizado com sucesso!',
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar notificação: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao processar avatar para usuário {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=2)
def process_cover_image_task(self, user_id, cover_image_path):
    """Processa imagem de capa de forma assíncrona"""
    from apps.main.home.models import User
    from utils.media_validators import process_image_for_social_media
    from utils.notifications import send_notification
    
    try:
        user = User.objects.get(id=user_id)
        
        # Processa a imagem
        processed_path = process_image_for_social_media(
            cover_image_path,
            max_width=1200,
            max_height=400,
            quality=90
        )
        
        logger.info(f"Imagem de capa processada para usuário {user_id}: {processed_path}")
        
        # Notifica o usuário
        try:
            send_notification(
                user=user,
                notification_type='user',
                message='Sua imagem de capa foi processada e otimizada com sucesso!',
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar notificação: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao processar imagem de capa para usuário {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=2)
def process_post_image_task(self, post_id, image_path):
    """Processa imagem de post social de forma assíncrona"""
    from apps.main.social.models import Post
    from utils.media_validators import process_image_for_social_media
    
    try:
        post = Post.objects.get(id=post_id)
        
        # Processa a imagem
        processed_path = process_image_for_social_media(
            image_path,
            max_width=1920,
            max_height=1080,
            quality=85
        )
        
        logger.info(f"Imagem de post processada para post {post_id}: {processed_path}")
        return True
    except Post.DoesNotExist:
        logger.error(f"Post {post_id} não encontrado")
        return False
    except Exception as e:
        logger.error(f"Erro ao processar imagem de post {post_id}: {e}")
        raise self.retry(exc=e, countdown=60) 
