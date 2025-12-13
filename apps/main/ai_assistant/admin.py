from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_active', 'solicitation', 'created_at')
    list_filter = ('is_active', 'created_at', 'user')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'title', 'is_active', 'solicitation')
        }),
        ('Metadados', {
            'fields': ('uuid', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'content_preview', 'tokens_used', 'created_at')
    list_filter = ('role', 'created_at', 'session__user')
    search_fields = ('content', 'session__user__username')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'tokens_used')
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Conteúdo'

    fieldsets = (
        ('Mensagem', {
            'fields': ('session', 'role', 'content', 'metadata', 'tokens_used')
        }),
        ('Metadados', {
            'fields': ('uuid', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
