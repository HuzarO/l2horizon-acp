import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO


class MediaCategory(models.Model):
    """Categorias para organizar os arquivos de mídia"""
    name = models.CharField('Nome', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Categoria de Mídia'
        verbose_name_plural = 'Categorias de Mídia'
        ordering = ['name']

    def __str__(self):
        return self.name


class MediaFile(models.Model):
    """Modelo para gerenciar arquivos de mídia"""
    
    FILE_TYPES = [
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('document', 'Documento'),
        ('other', 'Outro'),
    ]

    title = models.CharField('Título', max_length=255)
    description = models.TextField('Descrição', blank=True)
    file = models.FileField(
        'Arquivo',
        upload_to='media_storage/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',  # Imagens
                    'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',   # Vídeos
                    'mp3', 'wav', 'ogg', 'flac', 'aac',          # Áudios
                    'pdf', 'doc', 'docx', 'txt', 'rtf',          # Documentos
                    'zip', 'rar', '7z', 'tar', 'gz'              # Arquivos
                ]
            )
        ]
    )
    file_type = models.CharField('Tipo de Arquivo', max_length=20, choices=FILE_TYPES, default='other')
    category = models.ForeignKey(
        MediaCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Categoria'
    )
    file_size = models.PositiveIntegerField('Tamanho do Arquivo (bytes)', default=0)
    mime_type = models.CharField('Tipo MIME', max_length=100, blank=True)
    width = models.PositiveIntegerField('Largura', null=True, blank=True)
    height = models.PositiveIntegerField('Altura', null=True, blank=True)
    duration = models.DurationField('Duração', null=True, blank=True)
    
    # Thumbnails
    thumbnail = models.ImageField(
        'Miniatura',
        upload_to='media_storage/thumbnails/%Y/%m/',
        null=True,
        blank=True,
        help_text='Miniatura gerada automaticamente para imagens'
    )
    thumbnail_width = models.PositiveIntegerField('Largura da Miniatura', null=True, blank=True)
    thumbnail_height = models.PositiveIntegerField('Altura da Miniatura', null=True, blank=True)
    
    # Metadados
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Enviado por'
    )
    uploaded_at = models.DateTimeField('Enviado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    # Controle de acesso
    is_public = models.BooleanField('Público', default=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Tags para busca
    tags = models.CharField('Tags', max_length=500, blank=True, help_text='Separar tags por vírgula')

    class Meta:
        verbose_name = 'Arquivo de Mídia'
        verbose_name_plural = 'Arquivos de Mídia'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['file_type']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public', 'is_active']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            # Definir tamanho do arquivo
            self.file_size = self.file.size
            
            # Definir tipo MIME
            import mimetypes
            self.mime_type = mimetypes.guess_type(self.file.name)[0] or ''
            
            # Definir tipo de arquivo baseado na extensão
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                self.file_type = 'image'
            elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                self.file_type = 'video'
            elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac']:
                self.file_type = 'audio'
            elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                self.file_type = 'document'
            else:
                self.file_type = 'other'
            
            # Para imagens, obter dimensões
            if self.file_type == 'image' and ext != '.svg':
                try:
                    with Image.open(self.file) as img:
                        self.width, self.height = img.size
                except Exception:
                    pass
        
        super().save(*args, **kwargs)
        
        # Criar thumbnail para imagens após salvar
        if self.file_type == 'image' and self.file and not self.thumbnail:
            self.create_thumbnail()
            if self.thumbnail:
                # Salvar novamente para incluir o thumbnail
                super().save(update_fields=['thumbnail', 'thumbnail_width', 'thumbnail_height'])

    def delete(self, *args, **kwargs):
        # Deletar o arquivo físico e thumbnail ao deletar o registro
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        
        # Deletar thumbnail
        self.delete_thumbnail()
        
        super().delete(*args, **kwargs)

    @property
    def file_size_human(self):
        """Retorna o tamanho do arquivo em formato legível"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        """Retorna a extensão do arquivo"""
        return os.path.splitext(self.file.name)[1].lower()

    def get_absolute_url(self):
        return reverse('media_storage:detail', kwargs={'pk': self.pk})

    @property
    def is_image(self):
        return self.file_type == 'image'

    @property
    def is_video(self):
        return self.file_type == 'video'

    @property
    def is_audio(self):
        return self.file_type == 'audio'

    @property
    def is_document(self):
        return self.file_type == 'document'

    @property
    def tags_list(self):
        """Retorna lista de tags"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def create_thumbnail(self, size=(300, 300)):
        """Cria thumbnail para imagens"""
        if not self.is_image or not self.file:
            return False
            
        try:
            # Abrir a imagem original
            with Image.open(self.file.path) as image:
                # Converter RGBA para RGB se necessário
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                
                # Criar thumbnail mantendo proporção
                image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Salvar thumbnail
                thumb_io = BytesIO()
                image.save(thumb_io, format='JPEG', quality=85, optimize=True)
                thumb_io.seek(0)
                
                # Nome do arquivo thumbnail
                base_name = os.path.splitext(os.path.basename(self.file.name))[0]
                thumb_name = f"{base_name}_thumb.jpg"
                
                # Salvar no modelo
                self.thumbnail.save(
                    thumb_name,
                    ContentFile(thumb_io.read()),
                    save=False
                )
                
                # Salvar dimensões do thumbnail
                self.thumbnail_width = image.width
                self.thumbnail_height = image.height
                
                return True
                
        except Exception as e:
            print(f"Erro ao criar thumbnail: {e}")
            return False

    def get_thumbnail_url(self):
        """Retorna URL do thumbnail ou da imagem original se não houver thumbnail"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.is_image and self.file:
            return self.file.url
        return None

    def get_display_image(self):
        """Retorna a melhor imagem para exibição (thumbnail ou original)"""
        return self.get_thumbnail_url()

    def delete_thumbnail(self):
        """Remove o arquivo de thumbnail"""
        if self.thumbnail:
            if os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)
            self.thumbnail.delete(save=False)


class MediaUsage(models.Model):
    """Rastreia onde os arquivos de mídia são utilizados"""
    
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        verbose_name='Arquivo de Mídia',
        related_name='usages'
    )
    content_type = models.CharField('Tipo de Conteúdo', max_length=100)
    object_id = models.PositiveIntegerField('ID do Objeto')
    field_name = models.CharField('Nome do Campo', max_length=100)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Uso de Mídia'
        verbose_name_plural = 'Usos de Mídia'
        unique_together = ['media_file', 'content_type', 'object_id', 'field_name']

    def __str__(self):
        return f"{self.media_file.title} usado em {self.content_type}"
