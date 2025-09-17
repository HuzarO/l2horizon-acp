from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import DownloadCategory, DownloadLink
from utils.render_theme_page import render_theme_page

class DownloadListView(ListView):
    model = DownloadCategory
    template_name = 'public/downloads.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return DownloadCategory.objects.filter(is_active=True).prefetch_related(
            'downloads'
        ).filter(downloads__is_active=True).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Downloads')
        return context

    def get(self, request, *args, **kwargs):
        # Obter dados usando a lógica da ListView
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        
        # Usar render_theme_page para renderizar com suporte a temas
        return render_theme_page(request, 'public', 'downloads.html', context)

class InternalDownloadListView(LoginRequiredMixin, ListView):
    model = DownloadCategory
    template_name = 'downloads/internal_downloads.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return DownloadCategory.objects.filter(is_active=True).prefetch_related(
            'downloads'
        ).filter(downloads__is_active=True).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Downloads')
        context['segment'] = 'downloads'
        return context

def download_redirect(request, pk):
    download = get_object_or_404(DownloadLink, pk=pk, is_active=True)
    
    # Incrementa o contador de downloads
    download.increment_download_count()
    
    # Redireciona para a URL do download
    return redirect(download.url) 