from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(app_label)s_%(class)s_created',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(app_label)s_%(class)s_updated',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )

    def delete_old_media_files(self):
        """Remove arquivos de mídia antigos antes de salvar novos"""
        from django.core.files.storage import default_storage
        
        try:
            # Se já existe no banco (é uma edição), verificar arquivos antigos
            if self.pk:
                # Obter a classe atual para fazer a query
                model_class = self.__class__
                old_instance = model_class.objects.get(pk=self.pk)
                
                # Percorrer todos os campos do modelo
                for field in self._meta.fields:
                    # Verificar se é um campo de arquivo (ImageField ou FileField)
                    if isinstance(field, (models.ImageField, models.FileField)):
                        field_name = field.name
                        old_file = getattr(old_instance, field_name, None)
                        new_file = getattr(self, field_name, None)
                        
                        # Se o arquivo antigo existe e é diferente do novo
                        if old_file and (not new_file or old_file.name != new_file.name):
                            try:
                                # Verificar se o arquivo existe no storage antes de tentar deletar
                                if default_storage.exists(old_file.name):
                                    default_storage.delete(old_file.name)
                            except Exception:
                                # Ignorar erros de remoção para não quebrar o fluxo principal
                                pass
        except Exception:
            # Ignorar erros gerais para não quebrar o sistema
            pass

    def save(self, *args, **kwargs):
        """Override save para remover arquivos antigos automaticamente"""
        # Remover arquivos antigos antes de salvar
        self.delete_old_media_files()
        
        # Chamar o save original
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class BaseModelAbstract(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_created',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_updated',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )

    class Meta:
        abstract = True
