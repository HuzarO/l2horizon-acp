from django.urls import path
from . import views

app_name = 'media_storage'

urlpatterns = [
    # Views principais
    path('', views.MediaListView.as_view(), name='list'),
    path('upload/', views.media_upload, name='upload'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('<int:pk>/', views.MediaDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.media_edit, name='edit'),
    path('<int:pk>/delete/', views.media_delete, name='delete'),
    
    # Views AJAX/API
    path('ajax/upload/', views.ajax_upload, name='ajax_upload'),
    path('api/<int:pk>/', views.get_media_info, name='api_info'),
    
    # Navegador de mídia (popup)
    path('browser/', views.media_browser, name='browser'),
    
    # Utilitários
    path('cleanup/', views.cleanup_unused, name='cleanup'),
    
    # Servir arquivos (apenas em desenvolvimento)
    path('serve/<path:path>/', views.serve_media, name='serve'),
]
