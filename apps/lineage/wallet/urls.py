from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('dashboard/', views.dashboard_wallet, name='dashboard'),
    path('transfer/server/', views.transfer_to_server, name='transfer_to_server'),
    path('transfer/from-server/', views.transfer_from_server, name='transfer_from_server'),
    path('transfer/player/', views.transfer_to_player, name='transfer_to_player'),
    path("config/coins/", views.coin_config_panel, name="coin_config_panel"),
    path('buy-tokens/', views.comprar_fichas_wallet, name='comprar_fichas_wallet'),
]
