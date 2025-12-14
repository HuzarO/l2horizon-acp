from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel
from apps.main.home.models import User
from apps.main.solicitation.models import Solicitation


class AIProviderConfig(BaseModel):
    """Configuração do provedor de IA"""
    PROVIDER_CHOICES = [
        ('anthropic', _('Anthropic (Claude)')),
        ('gemini', _('Google Gemini')),
        ('grok', _('xAI Grok')),
    ]
    
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='anthropic',
        verbose_name=_("Provedor"),
        help_text=_("Provedor de IA a ser usado para o assistente virtual.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Ativo"),
        help_text=_("Indica se esta configuração está ativa.")
    )
    
    class Meta:
        verbose_name = _("Configuração de Provedor de IA")
        verbose_name_plural = _("Configurações de Provedor de IA")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_provider_display()} - {'Ativo' if self.is_active else 'Inativo'}"
    
    @classmethod
    def get_active_provider(cls):
        """Retorna o provedor ativo atual"""
        config = cls.objects.filter(is_active=True).first()
        if config:
            return config.provider
        return 'anthropic'  # Default


class ChatSession(BaseModel):
    """Sessão de conversa com o assistente de IA"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        verbose_name=_("Usuário"),
        help_text=_("Usuário que iniciou a conversa.")
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Título"),
        help_text=_("Título da conversa (gerado automaticamente pela primeira mensagem).")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Ativo"),
        help_text=_("Indica se a sessão está ativa.")
    )
    solicitation = models.ForeignKey(
        Solicitation,
        on_delete=models.SET_NULL,
        related_name='chat_sessions',
        blank=True,
        null=True,
        verbose_name=_("Solicitação"),
        help_text=_("Solicitação relacionada a esta conversa, se houver.")
    )

    class Meta:
        verbose_name = _("Sessão de Chat")
        verbose_name_plural = _("Sessões de Chat")
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat {self.id} - {self.user.username if self.user else 'Anônimo'}"


class ChatMessage(BaseModel):
    """Mensagem individual em uma sessão de chat"""
    ROLE_CHOICES = [
        ('user', _('Usuário')),
        ('assistant', _('Assistente')),
        ('system', _('Sistema')),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Sessão"),
        help_text=_("Sessão de chat à qual esta mensagem pertence.")
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name=_("Papel"),
        help_text=_("Papel do remetente da mensagem.")
    )
    content = models.TextField(
        verbose_name=_("Conteúdo"),
        help_text=_("Conteúdo da mensagem.")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadados"),
        help_text=_("Informações adicionais sobre a mensagem (ex: FAQ relacionado, categoria sugerida).")
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=_("Tokens Usados"),
        help_text=_("Número de tokens usados pela IA para gerar esta resposta.")
    )

    class Meta:
        verbose_name = _("Mensagem do Chat")
        verbose_name_plural = _("Mensagens do Chat")
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
