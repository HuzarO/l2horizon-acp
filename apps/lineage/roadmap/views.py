from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Roadmap
from apps.main.home.decorator import conditional_otp_required
from django.utils import translation


@conditional_otp_required
def index(request):
    # Exibe apenas itens publicados, não privados, e tradução em português
    language = translation.get_language()
    roadmaps = (
        Roadmap.objects.filter(is_published=True, is_private=False)
        .order_by('-pub_date')  # Ordenar por data mais recente primeiro
        .prefetch_related('translations')
    )
    
    # Paginação - 12 itens por página
    paginator = Paginator(roadmaps, 12)
    page = request.GET.get('page')
    
    try:
        roadmaps_page = paginator.page(page)
    except PageNotAnInteger:
        # Se a página não for um número, mostra a primeira página
        roadmaps_page = paginator.page(1)
    except EmptyPage:
        # Se a página estiver fora do range, mostra a última página
        roadmaps_page = paginator.page(paginator.num_pages)
    
    # Para cada roadmap, pega a tradução no idioma atual ou português
    items = []
    for roadmap in roadmaps_page:
        translation_obj = roadmap.translations.filter(language=language).first() or roadmap.translations.filter(language='pt').first()
        if translation_obj:
            items.append({
                'roadmap': roadmap,
                'translation': translation_obj,
            })
    
    context = {
        'items': items,
        'segment': 'roadmap',
        'roadmaps_page': roadmaps_page,
        'has_other_pages': roadmaps_page.has_other_pages(),
        'has_previous': roadmaps_page.has_previous(),
        'has_next': roadmaps_page.has_next(),
        'previous_page_number': roadmaps_page.previous_page_number() if roadmaps_page.has_previous() else None,
        'next_page_number': roadmaps_page.next_page_number() if roadmaps_page.has_next() else None,
        'current_page': roadmaps_page.number,
        'num_pages': paginator.num_pages,
        'total_items': paginator.count,
    }
    
    return render(request, 'pages/roadmap_index.html', context)


@conditional_otp_required
def detail(request, slug):
    language = translation.get_language()
    roadmap = get_object_or_404(Roadmap, slug=slug, is_published=True, is_private=False)
    translation_obj = roadmap.translations.filter(language=language).first() or roadmap.translations.filter(language='pt').first()
    return render(request, 'pages/roadmap_detail.html', {
        'roadmap': roadmap,
        'translation': translation_obj,
    })
