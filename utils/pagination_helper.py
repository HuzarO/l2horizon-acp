"""
Helper para preparar dados de paginação para o template includes/pagination.html
"""
from django.core.paginator import Page


def prepare_pagination_context(page_obj: Page):
    """
    Prepara o contexto de paginação para o template includes/pagination.html
    
    Args:
        page_obj: Objeto Page do Django Paginator
        
    Returns:
        dict: Dicionário com todas as variáveis necessárias para o template
    """
    if not page_obj or not hasattr(page_obj, 'paginator'):
        return {}
    
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages
    has_previous = page_obj.has_previous()
    has_next = page_obj.has_next()
    previous_page_number = page_obj.previous_page_number() if has_previous else None
    next_page_number = page_obj.next_page_number() if has_next else None
    
    # Calcula o range de páginas a mostrar (máximo 5 páginas ao redor da atual)
    if total_pages <= 7:
        # Se tem 7 ou menos páginas, mostra todas
        page_range = list(page_obj.paginator.page_range)
        show_first = False
        show_last = False
        show_first_ellipsis = False
        show_last_ellipsis = False
    else:
        # Se tem mais de 7 páginas, mostra range inteligente
        if current_page <= 4:
            # Perto do início: mostra primeiras 5 páginas
            page_range = list(range(1, 6))
            show_first = False
            show_last = True
            show_first_ellipsis = False
            show_last_ellipsis = True
        elif current_page >= total_pages - 3:
            # Perto do fim: mostra últimas 5 páginas
            page_range = list(range(total_pages - 4, total_pages + 1))
            show_first = True
            show_last = False
            show_first_ellipsis = True
            show_last_ellipsis = False
        else:
            # No meio: mostra 2 antes e 2 depois da atual
            page_range = list(range(current_page - 2, current_page + 3))
            show_first = True
            show_last = True
            show_first_ellipsis = True
            show_last_ellipsis = True
    
    return {
        'current_page': current_page,
        'total_pages': total_pages,
        'has_previous': has_previous,
        'has_next': has_next,
        'previous_page_number': previous_page_number,
        'next_page_number': next_page_number,
        'page_range': page_range,
        'show_first': show_first,
        'show_last': show_last,
        'show_first_ellipsis': show_first_ellipsis,
        'show_last_ellipsis': show_last_ellipsis,
    }
