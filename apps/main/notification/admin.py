# admin.py

from django.contrib import admin
from .models import Notification, PublicNotificationView, PushSubscription, PushNotificationLog, NotificationReward, PublicNotificationRewardClaim
from core.admin import BaseModelAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class NotificationRewardInline(admin.TabularInline):
    model = NotificationReward
    extra = 1
    fields = ('item_id', 'item_name', 'item_enchant', 'item_amount')


@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    list_display = ('user', 'notification_type', 'message', 'viewed', 'rewards_claimed', 'rewards_expires_status', 'created_at', 'notification_link')
    list_filter = ('notification_type', 'viewed', 'rewards_claimed', 'rewards_expires_at', 'created_at')
    search_fields = ('user__username', 'message', 'link')
    readonly_fields = ('created_at', 'updated_at', 'notification_link', 'rewards_expires_status')
    fields = ('user', 'notification_type', 'message', 'link', 'viewed', 'rewards_claimed', 'rewards_expires_at', 'rewards_expires_status', 'notification_link', 'created_at', 'updated_at')
    inlines = [NotificationRewardInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('rewards')

    def notification_link(self, obj):
        if obj.link:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.link, _("Abrir link"))
        return "-"
    notification_link.short_description = _("Link de Redirecionamento")
    
    def rewards_expires_status(self, obj):
        """Mostra o status de expiração dos prêmios"""
        if not obj.rewards_expires_at:
            return format_html('<span style="color: gray;">{}</span>', _("Sem expiração"))
        
        from django.utils import timezone
        if timezone.now() > obj.rewards_expires_at:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} ({})</span>',
                _("Expirado"),
                obj.rewards_expires_at.strftime('%d/%m/%Y %H:%M')
            )
        else:
            return format_html(
                '<span style="color: green;">{} ({})</span>',
                _("Válido até"),
                obj.rewards_expires_at.strftime('%d/%m/%Y %H:%M')
            )
    rewards_expires_status.short_description = _("Status de Expiração")


@admin.register(PublicNotificationView)
class PublicNotificationViewAdmin(BaseModelAdmin):
    list_display = ('user', 'notification', 'viewed')
    list_filter = ('viewed',)
    search_fields = ('user__username', 'notification__message')


@admin.register(PublicNotificationRewardClaim)
class PublicNotificationRewardClaimAdmin(BaseModelAdmin):
    list_display = ('user', 'notification', 'ip_address', 'created_at')
    list_filter = ('created_at', 'ip_address')
    search_fields = ('user__username', 'notification__message', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'notification')


@admin.register(PushSubscription)
class PushSubscriptionAdmin(BaseModelAdmin):
    list_display = ("user", "endpoint", "created_at")
    search_fields = ("user__username", "endpoint")


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(BaseModelAdmin):
    list_display = ("sent_by", "message", "total_subscribers", "successful_sends", "failed_sends", "created_at")
    list_filter = ("created_at", "sent_by")
    search_fields = ("sent_by__username", "message")
    readonly_fields = ("created_at", "updated_at")
    fields = ("sent_by", "message", "total_subscribers", "successful_sends", "failed_sends", "created_at", "updated_at")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sent_by')
