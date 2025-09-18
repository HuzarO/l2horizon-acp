from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import MediaCategory, MediaFile, MediaUsage


@admin.register(MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'file_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    def file_count(self, obj):
        count = obj.mediafile_set.count()
        if count > 0:
            url = reverse('admin:media_storage_mediafile_changelist')
            return format_html('<a href="{}?category__id={}">{} arquivos</a>', url, obj.id, count)
        return '0 arquivos'
    file_count.short_description = 'Arquivos'


class MediaUsageInline(admin.TabularInline):
    model = MediaUsage
    extra = 0
    readonly_fields = ['content_type', 'object_id', 'field_name', 'created_at']


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'file_type', 
        'category', 
        'file_size_display', 
        'preview_image',
        'is_public', 
        'is_active', 
        'uploaded_by', 
        'uploaded_at'
    ]
    list_filter = [
        'file_type', 
        'category', 
        'is_public', 
        'is_active', 
        'uploaded_at',
        'uploaded_by'
    ]
    search_fields = ['title', 'description', 'tags', 'file']
    readonly_fields = [
        'file_size', 
        'mime_type', 
        'width', 
        'height', 
        'uploaded_at', 
        'updated_at',
        'file_size_display',
        'file_info',
        'preview_display'
    ]
    fieldsets = [
        ('Informações Básicas', {
            'fields': ('title', 'description', 'file', 'category', 'tags')
        }),
        ('Metadados do Arquivo', {
            'fields': ('file_type', 'file_size_display', 'mime_type', 'width', 'height', 'duration'),
            'classes': ('collapse',)
        }),
        ('Thumbnail', {
            'fields': ('thumbnail', 'thumbnail_width', 'thumbnail_height'),
            'classes': ('collapse',)
        }),
        ('Controle de Acesso', {
            'fields': ('is_public', 'is_active', 'uploaded_by')
        }),
        ('Preview', {
            'fields': ('preview_display',),
            'classes': ('collapse',)
        }),
        ('Informações do Sistema', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
    inlines = [MediaUsageInline]
    actions = ['make_public', 'make_private', 'activate', 'deactivate']

    def file_size_display(self, obj):
        return obj.file_size_human
    file_size_display.short_description = 'Tamanho'

    def preview_image(self, obj):
        if obj.is_image and obj.file:
            # Usar thumbnail se disponível, senão usar imagem original
            image_url = obj.get_display_image() or obj.file.url
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                image_url
            )
        elif obj.is_video:
            return format_html('<span style="color: #007cba;">🎥 Vídeo</span>')
        elif obj.is_audio:
            return format_html('<span style="color: #007cba;">🎵 Áudio</span>')
        elif obj.is_document:
            return format_html('<span style="color: #007cba;">📄 Documento</span>')
        else:
            return format_html('<span style="color: #666;">📎 Arquivo</span>')
    preview_image.short_description = 'Preview'

    def preview_display(self, obj):
        if not obj.file:
            return 'Nenhum arquivo'
        
        html = f'<div style="margin: 10px 0;">'
        
        if obj.is_image:
            html += f'''
                <img src="{obj.file.url}" 
                     style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; border-radius: 4px;" 
                     alt="{obj.title}" />
            '''
        elif obj.is_video:
            html += f'''
                <video controls style="max-width: 300px; max-height: 300px;">
                    <source src="{obj.file.url}" type="{obj.mime_type}">
                    Seu navegador não suporta o elemento de vídeo.
                </video>
            '''
        elif obj.is_audio:
            html += f'''
                <audio controls>
                    <source src="{obj.file.url}" type="{obj.mime_type}">
                    Seu navegador não suporta o elemento de áudio.
                </audio>
            '''
        else:
            html += f'''
                <a href="{obj.file.url}" target="_blank" 
                   style="display: inline-block; padding: 10px; background: #f0f0f0; 
                          border: 1px solid #ddd; border-radius: 4px; text-decoration: none;">
                    📎 {obj.file.name.split('/')[-1]}
                </a>
            '''
        
        html += '</div>'
        return mark_safe(html)
    preview_display.short_description = 'Preview do Arquivo'

    def file_info(self, obj):
        if not obj.file:
            return 'Nenhum arquivo'
        
        info = f'''
        <div style="font-family: monospace; background: #f9f9f9; padding: 10px; border-radius: 4px;">
            <strong>Nome:</strong> {obj.file.name}<br>
            <strong>Tamanho:</strong> {obj.file_size_human}<br>
            <strong>Tipo MIME:</strong> {obj.mime_type}<br>
        '''
        
        if obj.width and obj.height:
            info += f'<strong>Dimensões:</strong> {obj.width}x{obj.height}px<br>'
        
        if obj.duration:
            info += f'<strong>Duração:</strong> {obj.duration}<br>'
        
        info += f'<strong>URL:</strong> <a href="{obj.file.url}" target="_blank">{obj.file.url}</a>'
        info += '</div>'
        
        return mark_safe(info)
    file_info.short_description = 'Informações do Arquivo'

    def make_public(self, request, queryset):
        count = queryset.update(is_public=True)
        self.message_user(request, f'{count} arquivos tornados públicos.')
    make_public.short_description = 'Tornar público'

    def make_private(self, request, queryset):
        count = queryset.update(is_public=False)
        self.message_user(request, f'{count} arquivos tornados privados.')
    make_private.short_description = 'Tornar privado'

    def activate(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} arquivos ativados.')
    activate.short_description = 'Ativar'

    def deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} arquivos desativados.')
    deactivate.short_description = 'Desativar'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'uploaded_by')


@admin.register(MediaUsage)
class MediaUsageAdmin(admin.ModelAdmin):
    list_display = ['media_file', 'content_type', 'object_id', 'field_name', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['media_file__title', 'content_type', 'field_name']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('media_file')
