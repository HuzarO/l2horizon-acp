from apps.main.notification.models import Notification, NotificationReward
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _


def send_notification(user=None, notification_type='user', message='', created_by=None, link=None, rewards=None):
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
        link=link
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


def claim_notification_rewards(notification, user):
    """
    Reclama os prêmios de uma notificação e adiciona à bag do usuário.
    Retorna True se prêmios foram reclamados, False caso contrário.
    """
    if notification.rewards_claimed:
        return False

    if not notification.rewards.exists():
        return False

    # Verifica se o usuário tem permissão para reclamar
    if notification.user and notification.user != user:
        return False

    # Adiciona todos os prêmios à bag
    for reward in notification.rewards.all():
        reward.add_to_user_bag(user)

    # Marca como reclamado
    notification.rewards_claimed = True
    notification.save()

    return True
