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
    rewards_claimed = models.BooleanField(
        default=False,
        verbose_name=_("Prêmios Reclamados"),
        help_text=_("Indica se os prêmios desta notificação já foram reclamados.")
    )
    rewards_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Prêmios Expirando Em"),
        help_text=_("Data e hora limite para reclamar os prêmios desta notificação. Deixe em branco para prêmios sem expiração.")
    )

    class Meta:
        verbose_name = _("Notificação")
        verbose_name_plural = _("Notificações")

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.message[:50]}..."
    
    def rewards_expired(self):
        """Verifica se os prêmios desta notificação expiraram"""
        if not self.rewards_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.rewards_expires_at
    
    def rewards_available(self):
        """Verifica se ainda é possível reclamar os prêmios (não expirou e tem prêmios)"""
        if not self.rewards.exists():
            return False
        return not self.rewards_expired()


class NotificationReward(BaseModel):
    """Prêmios que podem ser entregues junto com uma notificação"""
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='rewards',
        verbose_name=_("Notificação"),
        help_text=_("Notificação relacionada a este prêmio.")
    )
    item_id = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Item ID"), help_text=_("ID do item (opcional se for ficha)"))
    item_name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Item Name"), help_text=_("Nome do item (opcional se for ficha)"))
    item_enchant = models.PositiveIntegerField(default=0, verbose_name=_("Item Enchant"))
    item_amount = models.PositiveIntegerField(default=1, verbose_name=_("Item Amount"))
    fichas_amount = models.PositiveIntegerField(null=True, blank=True, default=0, verbose_name=_("Fichas Amount"), help_text=_("Quantidade de fichas (opcional se for item)"))

    class Meta:
        verbose_name = _("Prêmio de Notificação")
        verbose_name_plural = _("Prêmios de Notificações")
        ordering = ['created_at']

    def __str__(self):
        if self.fichas_amount and self.fichas_amount > 0:
            return f"{self.fichas_amount} Fichas"
        return f"{self.item_name} +{self.item_enchant} x{self.item_amount}"

    def add_to_user_bag(self, user):
        """Adiciona o prêmio à bag do usuário"""
        from apps.lineage.games.models import Bag, BagItem
        
        # Adiciona fichas se houver
        if self.fichas_amount and self.fichas_amount > 0:
            user.fichas += self.fichas_amount
            user.save()
        
        # Adiciona item se houver
        if self.item_id and self.item_name:
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
        
        return None


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
        unique_together = ['user', 'notification']

    def __str__(self):
        return f"{self.user.username} - {self.notification.message[:30]}..."


class PublicNotificationRewardClaim(BaseModel):
    """Rastreia prêmios reclamados de notificações públicas por usuário"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        help_text=_("Usuário que reclamou os prêmios.")
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        verbose_name=_("Notificação"),
        help_text=_("Notificação pública da qual os prêmios foram reclamados.")
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("Endereço IP usado ao reclamar os prêmios.")
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("User Agent"),
        help_text=_("User agent do navegador usado.")
    )

    class Meta:
        verbose_name = _("Prêmio de Notificação Pública Reclamado")
        verbose_name_plural = _("Prêmios de Notificações Públicas Reclamados")
        unique_together = ['user', 'notification']
        indexes = [
            models.Index(fields=['notification', 'user']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.notification.id} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


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
