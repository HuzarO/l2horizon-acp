from django.urls import path
from . import views
from .views import send_push_view
from . import manager_views

app_name = 'notification'

urlpatterns = [
    path('list/', views.get_notifications, name='notification_list'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('clear-all-notifications/', views.clear_all_notifications, name='clear_all_notifications'),
    path('detail/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('all/', views.all_notifications, name='all_notifications'),
    path('confirm-view/<int:pk>/', views.confirm_notification_view, name='confirm_notification_view'),
    path('claim-rewards/<int:pk>/', views.claim_rewards, name='claim_rewards'),
    path('send-push/', send_push_view, name='send_push'),
    
    # Manager URLs
    path('manager/', manager_views.manager_dashboard, name='manager_dashboard'),
    path('manager/list/', manager_views.notification_list, name='manager_list'),
    path('manager/create/', manager_views.notification_create, name='manager_create'),
    path('manager/detail/<int:pk>/', manager_views.notification_detail, name='manager_detail'),
    path('manager/delete/<int:pk>/', manager_views.notification_delete, name='manager_delete'),
    path('manager/api/item-info/', manager_views.get_item_info, name='manager_item_info'),
]
