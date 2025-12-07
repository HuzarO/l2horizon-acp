from django.urls import path
from . import views, views_manager


app_name = "roadmap"


urlpatterns = [
    path('', views.index, name='index'),
    
    # Manager URLs - DEVEM vir antes do padrão genérico <slug:slug>
    path('manager/', views_manager.manager_dashboard, name='manager_dashboard'),
    path('manager/roadmaps/', views_manager.roadmap_list, name='manager_roadmap_list'),
    path('manager/roadmap/create/', views_manager.roadmap_create, name='manager_roadmap_create'),
    path('manager/roadmap/<int:roadmap_id>/', views_manager.roadmap_detail, name='manager_roadmap_detail'),
    path('manager/roadmap/<int:roadmap_id>/edit/', views_manager.roadmap_edit, name='manager_roadmap_edit'),
    path('manager/roadmap/<int:roadmap_id>/delete/', views_manager.roadmap_delete, name='manager_roadmap_delete'),
    
    # Padrão genérico deve vir por último
    path('<slug:slug>/', views.detail, name='detail'),
]
