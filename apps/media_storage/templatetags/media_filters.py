from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """Divide uma string usando o delimitador especificado"""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]


@register.filter
def filesizeformat_mb(value):
    """Formata tamanho de arquivo em MB"""
    if not value:
        return '0 MB'
    
    try:
        size_mb = int(value) / 1024 / 1024
        if size_mb < 1:
            size_kb = int(value) / 1024
            return f'{size_kb:.1f} KB'
        return f'{size_mb:.1f} MB'
    except (ValueError, TypeError):
        return '0 MB'


@register.filter
def get_file_icon(file_type):
    """Retorna ícone baseado no tipo de arquivo"""
    icons = {
        'image': 'fas fa-image',
        'video': 'fas fa-video',
        'audio': 'fas fa-music',
        'document': 'fas fa-file-pdf',
        'other': 'fas fa-file'
    }
    return icons.get(file_type, 'fas fa-file')


@register.filter
def get_file_color(file_type):
    """Retorna cor baseada no tipo de arquivo"""
    colors = {
        'image': 'text-primary',
        'video': 'text-purple',
        'audio': 'text-success',
        'document': 'text-danger',
        'other': 'text-muted'
    }
    return colors.get(file_type, 'text-muted')
