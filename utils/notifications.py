from apps.main.notification.models import Notification, NotificationReward, PublicNotificationRewardClaim
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from django.db import transaction
from django.utils import timezone
from datetime import timedelta


def send_notification(user=None, notification_type='user', message='', created_by=None, link=None, rewards=None, rewards_expires_at=None):
    """
    Cria uma notificação segura.

    - Se `user` for None, será considerada uma notificação pública.
    - Notificações do tipo 'staff' só podem ser enviadas para usuários com is_staff ou is_superuser.
    - `created_by` é opcional e pode ser usado para validar permissões de quem está criando.
    - `link` é uma URL opcional que será incluída na notificação.
    - `rewards` é uma lista opcional de dicionários com prêmios. Cada dicionário deve conter:
        - item_id: ID do item (opcional se for ficha)
        - item_name: Nome do item (opcional se for ficha)
        - item_enchant: Nível de encantamento (padrão: 0)
        - item_amount: Quantidade (padrão: 1)
        - fichas_amount: Quantidade de fichas (opcional se for item)
    - `rewards_expires_at` é uma data/hora opcional para definir quando os prêmios expiram.
    """

    if notification_type == 'staff':
        if user:
            if not (user.is_staff or user.is_superuser):
                raise PermissionDenied(_("Notificações staff só podem ser enviadas para usuários staff ou superusuários."))
        else:
            # Notificação pública staff — só deve ser criada se quem envia tem permissão
            if created_by and not (created_by.is_staff or created_by.is_superuser):
                raise PermissionDenied(_("Você não tem permissão para criar notificações públicas staff."))

    # Criação da notificação
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
        link=link,
        rewards_expires_at=rewards_expires_at
    )

    # Adiciona prêmios se fornecidos
    if rewards:
        for reward_data in rewards:
            NotificationReward.objects.create(
                notification=notification,
                item_id=reward_data.get('item_id'),
                item_name=reward_data.get('item_name'),
                item_enchant=reward_data.get('item_enchant', 0),
                item_amount=reward_data.get('item_amount', 1),
                fichas_amount=reward_data.get('fichas_amount', 0) or None
            )

    return notification


def validate_reward_claim_security(notification, user, request=None):
    """
    Valida se um usuário pode reclamar prêmios de uma notificação pública.
    Retorna (True, None) se permitido, ou (False, mensagem_erro) se bloqueado.
    """
    # Notificações privadas não precisam dessa validação
    if notification.user is not None:
        return True, None
    
    # Para notificações públicas, verifica várias camadas de segurança
    
    # 1. Verifica se o usuário já reclamou esta notificação
    if PublicNotificationRewardClaim.objects.filter(user=user, notification=notification).exists():
        return False, _("Você já reclamou os prêmios desta notificação.")
    
    # 2. Verifica contas muito recentes (menos de 1 hora)
    if user.date_joined > timezone.now() - timedelta(hours=1):
        # Conta muito recente - verifica se há múltiplas contas do mesmo IP/email
        if request:
            from python_ipware import IpWare
            ipw = IpWare(precedence=("X_FORWARDED_FOR", "HTTP_X_FORWARDED_FOR"))
            ip_address, is_routable = ipw.get_client_ip(meta=request.META)
            
            if ip_address:
                # Verifica quantas contas do mesmo IP reclamaram esta notificação
                accounts_same_ip = PublicNotificationRewardClaim.objects.filter(
                    notification=notification,
                    ip_address=ip_address
                ).values('user').distinct().count()
                
                if accounts_same_ip > 0:
                    return False, _("Múltiplas contas do mesmo IP não podem reclamar os mesmos prêmios.")
        
        # Verifica se há múltiplas contas com o mesmo domínio de email (ex: test1@tempmail.com, test2@tempmail.com)
        email_domain = user.email.split('@')[1] if '@' in user.email else None
        if email_domain:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Conta quantos usuários do mesmo domínio de email reclamaram esta notificação
            same_domain_users = User.objects.filter(
                email__endswith=f'@{email_domain}',
                date_joined__gt=timezone.now() - timedelta(hours=24)
            ).exclude(id=user.id).values_list('id', flat=True)
            
            same_domain_claims = PublicNotificationRewardClaim.objects.filter(
                notification=notification,
                user_id__in=same_domain_users
            ).count()
            
            if same_domain_claims > 0:
                return False, _("Múltiplas contas com emails do mesmo domínio não podem reclamar os mesmos prêmios.")
    
    # 3. Verifica limite de prêmios reclamados por IP em um período (últimas 24h)
    if request:
        from python_ipware import IpWare
        ipw = IpWare(precedence=("X_FORWARDED_FOR", "HTTP_X_FORWARDED_FOR"))
        ip_address, is_routable = ipw.get_client_ip(meta=request.META)
        
        if ip_address:
            # Conta quantas reivindicações este IP fez nas últimas 24h
            recent_claims = PublicNotificationRewardClaim.objects.filter(
                ip_address=ip_address,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Limite de 3 reivindicações por IP em 24h
            if recent_claims >= 3:
                return False, _("Limite de prêmios reclamados atingido para este endereço IP. Tente novamente mais tarde.")
    
    return True, None


def claim_notification_rewards(notification, user, request=None):
    """
    Reclama os prêmios de uma notificação e adiciona à bag do usuário.
    Retorna (True, None) se prêmios foram reclamados, ou (False, mensagem_erro) caso contrário.
    """
    if not notification.rewards.exists():
        return False, _("Esta notificação não possui prêmios.")

    # Verifica se os prêmios expiraram
    if notification.rewards_expired():
        expires_at_str = notification.rewards_expires_at.strftime('%d/%m/%Y às %H:%M') if notification.rewards_expires_at else ''
        return False, _("Os prêmios desta notificação expiraram em {}.").format(expires_at_str)

    # Verifica se o usuário tem permissão para reclamar
    if notification.user and notification.user != user:
        return False, _("Você não tem permissão para reclamar prêmios desta notificação.")

    # Para notificações públicas, usa rastreamento individual
    if notification.user is None:
        # Validações de segurança para notificações públicas
        is_valid, error_message = validate_reward_claim_security(notification, user, request)
        if not is_valid:
            return False, error_message
        
        # Verifica se já reclamou (verificação adicional com lock)
        with transaction.atomic():
            # Usa select_for_update para evitar race conditions
            claim_exists = PublicNotificationRewardClaim.objects.select_for_update().filter(
                user=user, 
                notification=notification
            ).exists()
            
            if claim_exists:
                return False, _("Você já reclamou os prêmios desta notificação.")
            
            # Adiciona todos os prêmios à bag
            for reward in notification.rewards.all():
                reward.add_to_user_bag(user)
            
            # Registra a reivindicação
            from python_ipware import IpWare
            ipw = IpWare(precedence=("X_FORWARDED_FOR", "HTTP_X_FORWARDED_FOR"))
            ip_address, is_routable = ipw.get_client_ip(meta=request.META) if request else (None, False)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
            
            PublicNotificationRewardClaim.objects.create(
                user=user,
                notification=notification,
                ip_address=ip_address or None,
                user_agent=user_agent or None
            )
    else:
        # Para notificações privadas, mantém comportamento antigo
        if notification.rewards_claimed:
            return False, _("Os prêmios desta notificação já foram reclamados.")
        
        # Adiciona todos os prêmios à bag
        for reward in notification.rewards.all():
            reward.add_to_user_bag(user)
        
        # Marca como reclamado
        notification.rewards_claimed = True
        notification.save()

    return True, None
