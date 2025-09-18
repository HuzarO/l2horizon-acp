"""
Utilitários para gerenciamento de mídia e rastreamento de uso
"""
from django.apps import apps
from django.db import models
from .models import MediaFile, MediaUsage


def register_media_usage(media_file, content_object, field_name):
    """
    Registra o uso de um arquivo de mídia em um objeto específico
    
    Args:
        media_file: Instância do MediaFile
        content_object: Objeto que está usando o arquivo
        field_name: Nome do campo que contém o arquivo
    
    Returns:
        MediaUsage: Instância criada ou existente
    """
    if not isinstance(media_file, MediaFile):
        return None
    
    content_type = content_object._meta.label_lower
    object_id = content_object.pk
    
    usage, created = MediaUsage.objects.get_or_create(
        media_file=media_file,
        content_type=content_type,
        object_id=object_id,
        field_name=field_name
    )
    
    return usage


def unregister_media_usage(media_file, content_object, field_name):
    """
    Remove o registro de uso de um arquivo de mídia
    
    Args:
        media_file: Instância do MediaFile
        content_object: Objeto que não usa mais o arquivo
        field_name: Nome do campo
    """
    if not isinstance(media_file, MediaFile):
        return False
    
    content_type = content_object._meta.label_lower
    object_id = content_object.pk
    
    MediaUsage.objects.filter(
        media_file=media_file,
        content_type=content_type,
        object_id=object_id,
        field_name=field_name
    ).delete()
    
    return True


def scan_and_register_media_usage():
    """
    Escaneia todos os modelos do projeto em busca de campos FileField/ImageField
    que referenciam arquivos do media storage e registra os usos
    
    Returns:
        dict: Estatísticas do escaneamento
    """
    stats = {
        'models_scanned': 0,
        'files_found': 0,
        'usages_registered': 0,
        'errors': []
    }
    
    # Obter todos os modelos do projeto
    all_models = apps.get_models()
    
    for model in all_models:
        try:
            stats['models_scanned'] += 1
            
            # Encontrar campos de arquivo/imagem
            file_fields = []
            for field in model._meta.get_fields():
                if isinstance(field, (models.FileField, models.ImageField)):
                    file_fields.append(field)
            
            if not file_fields:
                continue
            
            # Escanear instâncias do modelo
            for instance in model.objects.all():
                for field in file_fields:
                    try:
                        file_value = getattr(instance, field.name)
                        if file_value and hasattr(file_value, 'url'):
                            stats['files_found'] += 1
                            
                            # Tentar encontrar o MediaFile correspondente
                            try:
                                # Extrair o caminho do arquivo
                                file_path = file_value.name
                                media_file = MediaFile.objects.filter(
                                    file__icontains=file_path.split('/')[-1]
                                ).first()
                                
                                if media_file:
                                    usage = register_media_usage(
                                        media_file, 
                                        instance, 
                                        field.name
                                    )
                                    if usage:
                                        stats['usages_registered'] += 1
                                        
                            except Exception as e:
                                stats['errors'].append(f'Erro ao processar {model.__name__}.{field.name}: {e}')
                                
                    except Exception as e:
                        stats['errors'].append(f'Erro ao acessar {model.__name__}.{field.name}: {e}')
                        
        except Exception as e:
            stats['errors'].append(f'Erro ao processar modelo {model.__name__}: {e}')
    
    return stats


def find_unused_files():
    """
    Encontra arquivos de mídia que não estão sendo utilizados
    
    Returns:
        QuerySet: MediaFiles não utilizados
    """
    return MediaFile.objects.filter(
        usages__isnull=True, 
        is_active=True
    ).select_related('category', 'uploaded_by')


def find_orphaned_files():
    """
    Encontra arquivos físicos que não têm registro no banco de dados
    
    Returns:
        list: Lista de caminhos de arquivos órfãos
    """
    import os
    from django.conf import settings
    
    orphaned_files = []
    media_root = settings.MEDIA_ROOT
    media_storage_path = os.path.join(media_root, 'media_storage')
    
    if not os.path.exists(media_storage_path):
        return orphaned_files
    
    # Obter todos os arquivos registrados no banco
    registered_files = set()
    for media_file in MediaFile.objects.all():
        if media_file.file:
            registered_files.add(os.path.join(media_root, media_file.file.name))
        if media_file.thumbnail:
            registered_files.add(os.path.join(media_root, media_file.thumbnail.name))
    
    # Escanear diretório físico
    for root, dirs, files in os.walk(media_storage_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path not in registered_files:
                orphaned_files.append(file_path)
    
    return orphaned_files


def cleanup_orphaned_files(dry_run=True):
    """
    Remove arquivos físicos órfãos
    
    Args:
        dry_run: Se True, apenas lista os arquivos sem deletar
    
    Returns:
        dict: Estatísticas da limpeza
    """
    import os
    
    orphaned_files = find_orphaned_files()
    stats = {
        'found': len(orphaned_files),
        'deleted': 0,
        'errors': []
    }
    
    if dry_run:
        return stats
    
    for file_path in orphaned_files:
        try:
            os.remove(file_path)
            stats['deleted'] += 1
        except Exception as e:
            stats['errors'].append(f'Erro ao deletar {file_path}: {e}')
    
    return stats


def get_media_usage_stats():
    """
    Retorna estatísticas detalhadas sobre uso de mídia
    
    Returns:
        dict: Estatísticas completas
    """
    total_files = MediaFile.objects.filter(is_active=True).count()
    used_files = MediaFile.objects.filter(
        usages__isnull=False, 
        is_active=True
    ).distinct().count()
    unused_files = total_files - used_files
    
    # Estatísticas por tipo
    usage_by_type = {}
    for content_type in MediaUsage.objects.values_list('content_type', flat=True).distinct():
        count = MediaUsage.objects.filter(content_type=content_type).count()
        usage_by_type[content_type] = count
    
    # Top arquivos mais utilizados
    top_used = MediaFile.objects.annotate(
        usage_count=models.Count('usages')
    ).filter(
        usage_count__gt=0
    ).order_by('-usage_count')[:10]
    
    return {
        'total_files': total_files,
        'used_files': used_files,
        'unused_files': unused_files,
        'usage_percentage': (used_files / total_files * 100) if total_files > 0 else 0,
        'usage_by_type': usage_by_type,
        'top_used_files': [
            {
                'title': f.title,
                'usage_count': f.usage_count,
                'file_type': f.file_type
            } for f in top_used
        ],
        'orphaned_files': len(find_orphaned_files())
    }
