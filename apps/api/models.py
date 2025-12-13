from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from core.models import BaseModel
from django.utils.translation import gettext_lazy as _


class DiscordServer(BaseModel):
    """
    Modelo para cadastrar instâncias do site vinculadas a servidores Discord
    Permite que o bot global identifique qual instância do site está associada a cada servidor Discord
    """
    discord_guild_id = models.BigIntegerField(
        unique=True,
        verbose_name=_("ID do Servidor Discord"),
        help_text=_("ID único do servidor Discord (ex: 1101010101100)")
    )
    
    site_domain = models.CharField(
        max_length=255,
        verbose_name=_("Domínio do Site"),
        help_text=_("Domínio do site PDL (ex: pdl.denky.dev.br)"),
        db_index=True
    )
    
    server_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Nome do Servidor"),
        help_text=_("Nome do servidor Discord (opcional)")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Ativo"),
        help_text=_("Se o registro está ativo")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Observações"),
        help_text=_("Notas adicionais sobre este registro")
    )
    
    class Meta:
        verbose_name = _("Servidor Discord")
        verbose_name_plural = _("Servidores Discord")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['discord_guild_id']),
            models.Index(fields=['site_domain']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        """Validação do modelo"""
        # Normalizar domínio
        if self.site_domain:
            self.site_domain = self._normalize_domain(self.site_domain)
    
    def _normalize_domain(self, domain: str) -> str:
        """Normaliza o domínio"""
        domain = domain.strip().lower()
        
        # Remover protocolo
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        
        # Remover barras finais
        domain = domain.rstrip('/')
        
        # Remover www (opcional)
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    
    def save(self, *args, **kwargs):
        """Override save para normalizar domínio"""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.site_domain} -> Discord: {self.discord_guild_id}"
