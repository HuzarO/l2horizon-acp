import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


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
