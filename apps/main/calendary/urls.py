from django.urls import path
from . import views, views_manager

app_name = 'calendary'

urlpatterns = [
    path('dashboard/', views.calendar, name="calendar"),
    path('api/events/', views.get_events, name="get_events"),
    
    # Manager URLs
    path('manager/', views_manager.manager_dashboard, name='manager_dashboard'),
    path('manager/events/', views_manager.event_list, name='manager_event_list'),
    path('manager/event/create/', views_manager.event_create, name='manager_event_create'),
    path('manager/event/<int:event_id>/', views_manager.event_detail, name='manager_event_detail'),
    path('manager/event/<int:event_id>/edit/', views_manager.event_edit, name='manager_event_edit'),
    path('manager/event/<int:event_id>/delete/', views_manager.event_delete, name='manager_event_delete'),
]
