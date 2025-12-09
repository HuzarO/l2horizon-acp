from django.db import models
from core.models import BaseModel
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from encrypted_fields.encrypted_fields import *
from encrypted_fields.encrypted_files import *
from utils.choices import *


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Usuário"),
        help_text=_("Usuário relacionado à notificação (pode ser nulo para notificações públicas).")
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name=_("Tipo de Notificação"),
        help_text=_("Tipo ou categoria da notificação.")
    )
    message = EncryptedCharField(
        max_length=255,
        verbose_name=_("Mensagem"),
        help_text=_("Mensagem da notificação (criptografada).")
    )
    viewed = models.BooleanField(
        default=False,
        verbose_name=_("Visualizada"),
        help_text=_("Indica se a notificação foi visualizada pelo usuário.")
    )
    link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("Link da Notificação"),
        help_text=_("URL opcional para redirecionar ao clicar na notificação.")
    )

    class Meta:
        verbose_name = _("Notificação")
        verbose_name_plural = _("Notificações")

    rewards_claimed = models.BooleanField(
        default=False,
        verbose_name=_("Prêmios Reclamados"),
        help_text=_("Indica se os prêmios desta notificação já foram reclamados.")
    )

    class Meta:
        verbose_name = _("Notificação")
        verbose_name_plural = _("Notificações")

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.message[:50]}..."


class NotificationReward(BaseModel):
    """Prêmios que podem ser entregues junto com uma notificação"""
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='rewards',
        verbose_name=_("Notificação"),
        help_text=_("Notificação relacionada a este prêmio.")
    )
    item_id = models.PositiveIntegerField(verbose_name=_("Item ID"))
    item_name = models.CharField(max_length=100, verbose_name=_("Item Name"))
    item_enchant = models.PositiveIntegerField(default=0, verbose_name=_("Item Enchant"))
    item_amount = models.PositiveIntegerField(default=1, verbose_name=_("Item Amount"))

    class Meta:
        verbose_name = _("Prêmio de Notificação")
        verbose_name_plural = _("Prêmios de Notificações")
        ordering = ['created_at']

    def __str__(self):
        return f"{self.item_name} +{self.item_enchant} x{self.item_amount}"

    def add_to_user_bag(self, user):
        """Adiciona o prêmio à bag do usuário"""
        from apps.lineage.games.models import Bag, BagItem
        
        bag, created = Bag.objects.get_or_create(user=user)
        bag_item, created = BagItem.objects.get_or_create(
            bag=bag,
            item_id=self.item_id,
            enchant=self.item_enchant,
            defaults={
                'item_name': self.item_name,
                'quantity': self.item_amount,
            }
        )
        if not created:
            bag_item.quantity += self.item_amount
            bag_item.save()
        return bag_item


class PublicNotificationView(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        help_text=_("Usuário que visualizou a notificação pública.")
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        verbose_name=_("Notificação"),
        help_text=_("Referência à notificação visualizada.")
    )
    viewed = models.BooleanField(
        default=False,
        verbose_name=_("Visualizada"),
        help_text=_("Indica se o usuário visualizou essa notificação pública.")
    )

    class Meta:
        verbose_name = _("Visualização de Notificação Pública")
        verbose_name_plural = _("Visualizações de Notificações Públicas")

    def __str__(self):
        return f"{self.user.username} - {self.notification.message[:30]}..."


class PushSubscription(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Usuário'),
        help_text=_('Usuário dono do subscription.')
    )
    endpoint = models.URLField(max_length=500)
    auth = models.CharField(max_length=255)
    p256dh = models.CharField(max_length=255)

    class Meta:
        verbose_name = _('Push Subscription')
        verbose_name_plural = _('Push Subscriptions')

    def __str__(self):
        return f"{self.user} - {self.endpoint[:30]}..."


class PushNotificationLog(BaseModel):
    message = models.TextField(
        verbose_name=_("Mensagem"),
        help_text=_("Mensagem enviada via push.")
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Enviado por"),
        help_text=_("Usuário que enviou a notificação push.")
    )
    total_subscribers = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total de Inscritos"),
        help_text=_("Número total de usuários inscritos no momento do envio.")
    )
    successful_sends = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Enviados com Sucesso"),
        help_text=_("Número de notificações enviadas com sucesso.")
    )
    failed_sends = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Falhas no Envio"),
        help_text=_("Número de notificações que falharam ao enviar.")
    )

    class Meta:
        verbose_name = _("Log de Notificação Push")
        verbose_name_plural = _("Logs de Notificações Push")
        ordering = ['-created_at']

    def __str__(self):
        return f"Push enviado por {self.sent_by} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
