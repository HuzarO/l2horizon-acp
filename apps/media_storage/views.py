import os
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import MediaFile, MediaCategory
from .forms import MediaFileForm, MediaFileFilterForm, BulkUploadForm


@method_decorator(staff_member_required, name='dispatch')
class MediaListView(ListView):
    """View para listar arquivos de mídia"""
    model = MediaFile
    template_name = 'media_storage/list.html'
    context_object_name = 'media_files'
    paginate_by = 20

    def get_queryset(self):
        queryset = MediaFile.objects.select_related('category', 'uploaded_by').filter(is_active=True)
        
        # Filtros
        search = self.request.GET.get('search')
        category = self.request.GET.get('category')
        file_type = self.request.GET.get('file_type')
        is_public = self.request.GET.get('is_public')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )

        if category:
            queryset = queryset.filter(category_id=category)

        if file_type:
            queryset = queryset.filter(file_type=file_type)

        if is_public:
            queryset = queryset.filter(is_public=is_public == 'true')

        return queryset.order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MediaCategory.objects.all()
        context['file_types'] = MediaFile.FILE_TYPES
        context['filter_form'] = MediaFileFilterForm(self.request.GET)
        
        # Estatísticas
        context['stats'] = {
            'total_files': MediaFile.objects.filter(is_active=True).count(),
            'total_size': sum(f.file_size for f in MediaFile.objects.filter(is_active=True)),
            'by_type': dict(MediaFile.objects.filter(is_active=True).values_list('file_type').annotate(Count('file_type'))),
        }
        
        return context


@method_decorator(staff_member_required, name='dispatch')
class MediaDetailView(DetailView):
    """View para detalhes de um arquivo de mídia"""
    model = MediaFile
    template_name = 'media_storage/detail.html'
    context_object_name = 'media_file'

    def get_queryset(self):
        return MediaFile.objects.select_related('category', 'uploaded_by').prefetch_related('usages')


@staff_member_required
def media_upload(request):
    """View para upload de arquivos"""
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES)
        if form.is_valid():
            media_file = form.save(commit=False)
            media_file.uploaded_by = request.user
            media_file.save()
            messages.success(request, f'Arquivo "{media_file.title}" enviado com sucesso!')
            return redirect('media_storage:detail', pk=media_file.pk)
    else:
        form = MediaFileForm()

    return render(request, 'media_storage/upload.html', {'form': form})


@staff_member_required
def media_edit(request, pk):
    """View para editar arquivo de mídia"""
    media_file = get_object_or_404(MediaFile, pk=pk)
    
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES, instance=media_file)
        if form.is_valid():
            form.save()
            messages.success(request, f'Arquivo "{media_file.title}" atualizado com sucesso!')
            return redirect('media_storage:detail', pk=media_file.pk)
    else:
        form = MediaFileForm(instance=media_file)

    return render(request, 'media_storage/edit.html', {
        'form': form,
        'media_file': media_file
    })


@staff_member_required
@require_http_methods(["POST"])
def media_delete(request, pk):
    """View para deletar arquivo de mídia"""
    media_file = get_object_or_404(MediaFile, pk=pk)
    title = media_file.title
    media_file.delete()
    messages.success(request, f'Arquivo "{title}" deletado com sucesso!')
    return redirect('media_storage:list')


@staff_member_required
def bulk_upload(request):
    """View para upload em lote"""
    if request.method == 'POST':
        # Debug: verificar se há arquivos
        files = request.FILES.getlist('files')
        print(f"DEBUG: Arquivos recebidos: {len(files)}")
        print(f"DEBUG: request.FILES keys: {list(request.FILES.keys())}")
        print(f"DEBUG: request.POST keys: {list(request.POST.keys())}")
        
        if not files:
            messages.error(request, 'Nenhum arquivo foi selecionado. Por favor, selecione pelo menos um arquivo.')
            form = BulkUploadForm()
            return render(request, 'media_storage/bulk_upload.html', {'form': form})
        
        # Processar dados do formulário manualmente
        category_id = request.POST.get('category')
        category = None
        if category_id:
            try:
                category = MediaCategory.objects.get(id=category_id)
            except MediaCategory.DoesNotExist:
                pass
        
        is_public = request.POST.get('is_public') == 'on'
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Validar tamanho do arquivo
                if file.size > 100 * 1024 * 1024:
                    errors.append(f'Arquivo {file.name} é muito grande (máximo: 100MB)')
                    continue
                
                # Criar título baseado no nome do arquivo
                title = os.path.splitext(file.name)[0].replace('_', ' ').replace('-', ' ').title()
                
                media_file = MediaFile.objects.create(
                    title=title,
                    file=file,
                    category=category,
                    is_public=is_public,
                    uploaded_by=request.user
                )
                uploaded_files.append(media_file)
                print(f"DEBUG: Arquivo criado: {media_file.title}")
                
            except Exception as e:
                errors.append(f'Erro ao processar {file.name}: {str(e)}')
                print(f"DEBUG: Erro ao processar {file.name}: {e}")
        
        # Mensagens de resultado
        if uploaded_files:
            messages.success(request, f'{len(uploaded_files)} arquivos enviados com sucesso!')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        
        if uploaded_files:
            return redirect('media_storage:list')
        else:
            # Se não houve uploads bem-sucedidos, mostrar o formulário novamente
            form = BulkUploadForm()
            return render(request, 'media_storage/bulk_upload.html', {'form': form})
    else:
        form = BulkUploadForm()

    return render(request, 'media_storage/bulk_upload.html', {'form': form})


@staff_member_required
@csrf_exempt
def ajax_upload(request):
    """View AJAX para upload de arquivos"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Nenhum arquivo enviado'}, status=400)

    file = request.FILES['file']
    title = request.POST.get('title', os.path.splitext(file.name)[0])
    description = request.POST.get('description', '')
    category_id = request.POST.get('category_id')
    is_public = request.POST.get('is_public', 'true') == 'true'

    try:
        category = None
        if category_id:
            category = MediaCategory.objects.get(id=category_id)

        media_file = MediaFile.objects.create(
            title=title,
            description=description,
            file=file,
            category=category,
            is_public=is_public,
            uploaded_by=request.user
        )

        return JsonResponse({
            'success': True,
            'id': media_file.id,
            'title': media_file.title,
            'url': media_file.file.url,
            'file_type': media_file.file_type,
            'file_size': media_file.file_size_human
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
def media_browser(request):
    """View para navegador de mídia (popup)"""
    media_files = MediaFile.objects.filter(is_active=True, is_public=True).order_by('-uploaded_at')
    
    # Filtros
    search = request.GET.get('search')
    category = request.GET.get('category')
    file_type = request.GET.get('file_type')

    if search:
        media_files = media_files.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )

    if category:
        media_files = media_files.filter(category_id=category)

    if file_type:
        media_files = media_files.filter(file_type=file_type)

    # Paginação
    paginator = Paginator(media_files, 12)
    page = request.GET.get('page')
    media_files = paginator.get_page(page)

    context = {
        'media_files': media_files,
        'categories': MediaCategory.objects.all(),
        'file_types': MediaFile.FILE_TYPES,
        'is_popup': True
    }

    return render(request, 'media_storage/browser.html', context)


@staff_member_required
def get_media_info(request, pk):
    """API para obter informações de um arquivo de mídia"""
    try:
        media_file = MediaFile.objects.get(pk=pk, is_active=True)
        return JsonResponse({
            'id': media_file.id,
            'title': media_file.title,
            'description': media_file.description,
            'url': media_file.file.url,
            'file_type': media_file.file_type,
            'file_size': media_file.file_size_human,
            'width': media_file.width,
            'height': media_file.height,
            'mime_type': media_file.mime_type,
            'tags': media_file.tags,
            'category': media_file.category.name if media_file.category else None,
            'uploaded_at': media_file.uploaded_at.isoformat(),
        })
    except MediaFile.DoesNotExist:
        return JsonResponse({'error': 'Arquivo não encontrado'}, status=404)


@staff_member_required
def cleanup_unused(request):
    """View para limpeza de arquivos não utilizados"""
    from .utils import get_media_usage_stats, find_orphaned_files
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'scan_usage':
            # Escanear e registrar usos automaticamente
            from .utils import scan_and_register_media_usage
            stats = scan_and_register_media_usage()
            
            messages.info(request, 
                f'Escaneamento concluído: {stats["usages_registered"]} usos registrados '
                f'em {stats["models_scanned"]} modelos.'
            )
            
            if stats['errors']:
                messages.warning(request, f'{len(stats["errors"])} erros encontrados durante o escaneamento.')
            
            return redirect('media_storage:cleanup')
        
        elif action == 'delete_unused':
            # Encontrar arquivos sem uso
            unused_files = MediaFile.objects.filter(usages__isnull=True, is_active=True)
            count = unused_files.count()
            
            if request.POST.get('confirm') == 'yes':
                # Deletar arquivos não utilizados
                deleted_count = 0
                for media_file in unused_files:
                    media_file.delete()
                    deleted_count += 1
                
                messages.success(request, f'{deleted_count} arquivos não utilizados foram deletados.')
                return redirect('media_storage:list')
            else:
                return render(request, 'media_storage/cleanup_confirm.html', {
                    'unused_files': unused_files,
                    'count': count,
                    'cleanup_type': 'unused'
                })
        
        elif action == 'cleanup_orphaned':
            # Encontrar arquivos órfãos
            orphaned_files = find_orphaned_files()
            
            if request.POST.get('confirm') == 'yes':
                # Deletar arquivos órfãos
                from .utils import cleanup_orphaned_files
                stats = cleanup_orphaned_files(dry_run=False)
                
                messages.success(request, f'{stats["deleted"]} arquivos órfãos foram deletados.')
                if stats['errors']:
                    messages.warning(request, f'{len(stats["errors"])} erros ocorreram durante a limpeza.')
                
                return redirect('media_storage:cleanup')
            else:
                return render(request, 'media_storage/cleanup_orphaned_confirm.html', {
                    'orphaned_files': orphaned_files,
                    'count': len(orphaned_files)
                })
    
    # Obter estatísticas completas
    stats = get_media_usage_stats()
    orphaned_files = find_orphaned_files()
    
    return render(request, 'media_storage/cleanup.html', {
        'stats': stats,
        'orphaned_count': len(orphaned_files),
        'unused_count': stats['unused_files'],
        'total_count': stats['total_files'],
    })


def serve_media(request, path):
    """View para servir arquivos de mídia com controle de acesso"""
    try:
        # Encontrar o arquivo
        media_file = MediaFile.objects.get(file=f'media_storage/{path}', is_active=True)
        
        # Verificar permissões
        if not media_file.is_public and not request.user.is_staff:
            raise Http404("Arquivo não encontrado")
        
        # Servir o arquivo
        if settings.DEBUG:
            # Em desenvolvimento, servir diretamente
            response = HttpResponse(media_file.file.read(), content_type=media_file.mime_type)
            response['Content-Disposition'] = f'inline; filename="{media_file.file.name.split("/")[-1]}"'
            return response
        else:
            # Em produção, usar X-Sendfile ou similar
            response = HttpResponse()
            response['X-Sendfile'] = media_file.file.path
            response['Content-Type'] = media_file.mime_type
            return response
            
    except MediaFile.DoesNotExist:
        raise Http404("Arquivo não encontrado")
