from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify

from .models import Roadmap, RoadmapTranslation


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def manager_dashboard(request):
    """Dashboard de gerenciamento do Roadmap"""
    
    # Estatísticas gerais
    total_roadmaps = Roadmap.objects.count()
    published_roadmaps = Roadmap.objects.filter(is_published=True).count()
    planned_roadmaps = Roadmap.objects.filter(status='planned').count()
    in_progress_roadmaps = Roadmap.objects.filter(status='in_progress').count()
    completed_roadmaps = Roadmap.objects.filter(status='completed').count()
    
    # Roadmaps recentes
    recent_roadmaps = Roadmap.objects.select_related('author').prefetch_related('translations').order_by('-created_at')[:5]
    
    context = {
        'total_roadmaps': total_roadmaps,
        'published_roadmaps': published_roadmaps,
        'planned_roadmaps': planned_roadmaps,
        'in_progress_roadmaps': in_progress_roadmaps,
        'completed_roadmaps': completed_roadmaps,
        'recent_roadmaps': recent_roadmaps,
    }
    
    return render(request, 'roadmap/manager/dashboard.html', context)


@staff_required
def roadmap_list(request):
    """Lista todos os roadmaps"""
    roadmaps = Roadmap.objects.select_related('author').prefetch_related('translations').order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        roadmaps = roadmaps.filter(status=status_filter)
    
    published_filter = request.GET.get('published', 'all')
    if published_filter == 'yes':
        roadmaps = roadmaps.filter(is_published=True)
    elif published_filter == 'no':
        roadmaps = roadmaps.filter(is_published=False)
    
    context = {
        'roadmaps': roadmaps,
        'status_filter': status_filter,
        'published_filter': published_filter,
    }
    return render(request, 'roadmap/manager/roadmap_list.html', context)


@staff_required
@transaction.atomic
def roadmap_create(request):
    """Criar novo roadmap"""
    if request.method == 'POST':
        try:
            # Dados básicos
            status = request.POST.get('status', 'planned')
            is_published = request.POST.get('is_published') == 'on'
            is_private = request.POST.get('is_private') == 'on'
            pub_date = request.POST.get('pub_date')
            author_id = request.POST.get('author')
            if not author_id:
                author_id = request.user.id
            
            # Preparar dados do pub_date
            if pub_date:
                from datetime import datetime
                try:
                    pub_date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    pub_date_obj = timezone.now()
            else:
                pub_date_obj = timezone.now()
            
            # Primeiro, obter o título PT para gerar o slug
            pt_title = request.POST.get('title_pt', '').strip()
            
            # Gerar slug baseado no título PT ANTES de criar o roadmap
            if pt_title:
                new_slug = slugify(pt_title)
                # Se o slug já existir, adicionar um sufixo
                base_slug = new_slug
                counter = 1
                while Roadmap.objects.filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
            else:
                # Se não tiver título PT, gerar slug temporário único
                new_slug = f"roadmap-{int(timezone.now().timestamp())}"
            
            # IMPORTANTE: Criar roadmap definindo o slug ANTES de salvar
            # O método save() customizado só acessa traduções se self.slug estiver vazio
            # Como já definimos o slug, ele não tentará acessar as traduções
            roadmap = Roadmap(
                author_id=int(author_id),
                status=status,
                is_published=is_published,
                is_private=is_private,
                pub_date=pub_date_obj,
                slug=new_slug  # CRUCIAL: Definir slug antes de salvar
            )
            
            # Salvar usando o manager normal - o save() não acessará traduções porque slug já está definido
            roadmap.save()
            roadmap_id = roadmap.id
            
            # Agora criar as traduções usando roadmap_id diretamente
            pt_translation = None
            translations_to_create = []
            for lang_code in ['pt', 'en', 'es']:
                title_key = f'title_{lang_code}'
                content_key = f'content_{lang_code}'
                summary_key = f'summary_{lang_code}'
                
                title_value = request.POST.get(title_key, '').strip()
                if title_value:  # Só criar se tiver título
                    translation = RoadmapTranslation(
                        roadmap_id=roadmap_id,  # Usar roadmap_id diretamente
                        language=lang_code,
                        title=title_value,
                        content=request.POST.get(content_key, '').strip(),
                        summary=request.POST.get(summary_key, '').strip()
                    )
                    translation.save()
                    if lang_code == 'pt':
                        pt_translation = translation
            
            messages.success(request, _('Roadmap criado com sucesso!'))
            return redirect('roadmap:manager_roadmap_detail', roadmap_id=roadmap.id)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messages.error(request, _('Erro ao criar roadmap: {}').format(str(e)))
            # Log para debug (remover em produção)
            print(f"Erro detalhado: {error_details}")
    
    from apps.main.home.models import User
    users = User.objects.all().order_by('username')
    context = {
        'users': users,
        'status_choices': Roadmap.STATUS_CHOICES,
    }
    return render(request, 'roadmap/manager/roadmap_create.html', context)


@staff_required
@transaction.atomic
def roadmap_edit(request, roadmap_id):
    """Editar roadmap existente"""
    roadmap = get_object_or_404(
        Roadmap.objects.prefetch_related('translations'),
        id=roadmap_id
    )
    
    if request.method == 'POST':
        try:
            roadmap.status = request.POST.get('status', roadmap.status)
            roadmap.is_published = request.POST.get('is_published') == 'on'
            roadmap.is_private = request.POST.get('is_private') == 'on'
            pub_date = request.POST.get('pub_date')
            if pub_date:
                roadmap.pub_date = pub_date
            
            roadmap.save()
            
            # Atualizar traduções
            for lang_code in ['pt', 'en', 'es']:
                title_key = f'title_{lang_code}'
                content_key = f'content_{lang_code}'
                summary_key = f'summary_{lang_code}'
                
                translation, created = RoadmapTranslation.objects.get_or_create(
                    roadmap=roadmap,
                    language=lang_code,
                    defaults={
                        'title': request.POST.get(title_key, ''),
                        'content': request.POST.get(content_key, ''),
                        'summary': request.POST.get(summary_key, '')
                    }
                )
                
                if not created:
                    translation.title = request.POST.get(title_key, translation.title)
                    translation.content = request.POST.get(content_key, translation.content)
                    translation.summary = request.POST.get(summary_key, translation.summary)
                    translation.save()
            
            # Atualizar slug se necessário
            pt_translation = roadmap.translations.filter(language='pt').first()
            if pt_translation and pt_translation.title:
                new_slug = slugify(pt_translation.title)
                if new_slug != roadmap.slug:
                    # Verificar se slug já existe
                    if not Roadmap.objects.filter(slug=new_slug).exclude(id=roadmap.id).exists():
                        roadmap.slug = new_slug
                        roadmap.save()
            
            messages.success(request, _('Roadmap atualizado com sucesso!'))
            return redirect('roadmap:manager_roadmap_detail', roadmap_id=roadmap.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar roadmap: {}').format(str(e)))
    
    from apps.main.home.models import User
    users = User.objects.all().order_by('username')
    
    # Organizar traduções por idioma
    translations = {t.language: t for t in roadmap.translations.all()}
    
    context = {
        'roadmap': roadmap,
        'users': users,
        'status_choices': Roadmap.STATUS_CHOICES,
        'translations': translations,
    }
    return render(request, 'roadmap/manager/roadmap_edit.html', context)


@staff_required
def roadmap_detail(request, roadmap_id):
    """Detalhes do roadmap"""
    roadmap = get_object_or_404(
        Roadmap.objects.select_related('author').prefetch_related('translations'),
        id=roadmap_id
    )
    
    # Organizar traduções
    translations = {t.language: t for t in roadmap.translations.all()}
    
    context = {
        'roadmap': roadmap,
        'translations': translations,
    }
    return render(request, 'roadmap/manager/roadmap_detail.html', context)


@staff_required
@transaction.atomic
def roadmap_delete(request, roadmap_id):
    """Deletar roadmap"""
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    if request.method == 'POST':
        pt_translation = roadmap.translations.filter(language='pt').first()
        roadmap_title = pt_translation.title if pt_translation else f"Roadmap #{roadmap.id}"
        roadmap.delete()
        messages.success(request, _('Roadmap "{}" deletado com sucesso!').format(roadmap_title))
        return redirect('roadmap:manager_roadmap_list')
    
    pt_translation = roadmap.translations.filter(language='pt').first()
    context = {
        'roadmap': roadmap,
        'roadmap_title': pt_translation.title if pt_translation else f"Roadmap #{roadmap.id}",
    }
    return render(request, 'roadmap/manager/roadmap_delete.html', context)

