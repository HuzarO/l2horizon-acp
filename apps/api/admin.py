from django.contrib import admin
from core.admin import BaseModelAdmin
from .models import DiscordServer


@admin.register(DiscordServer)
class DiscordServerAdmin(BaseModelAdmin):
    """Admin para servidores Discord"""
    list_display = ['site_domain', 'discord_guild_id', 'server_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['site_domain', 'discord_guild_id', 'server_name']
    readonly_fields = ['uuid', 'created_at', 'created_by', 'updated_at', 'updated_by']
    
    fieldsets = (
        ('Informações Principais', {
            'fields': ('discord_guild_id', 'site_domain', 'server_name', 'is_active')
        }),
        ('Observações', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('uuid', 'created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
