from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.lineage.games.models import Recompensa, RecompensaRecebida
from apps.main.home.models import PerfilGamer


@login_required
def level_rewards_view(request):
    """Visualizar recompensas disponíveis por nível"""
    perfil, created = PerfilGamer.objects.get_or_create(user=request.user)
    current_level = perfil.level
    
    # Buscar todas as recompensas por nível
    todas_recompensas = Recompensa.objects.filter(tipo='NIVEL').order_by('referencia')
    
    # IDs das recompensas já recebidas
    recompensas_recebidas_ids = set(
        RecompensaRecebida.objects.filter(
            user=request.user,
            recompensa__tipo='NIVEL'
        ).values_list('recompensa_id', flat=True)
    )
    
    # Categorizar recompensas
    recompensas_disponiveis = []  # Nível <= current_level e não recebida
    recompensas_recebidas = []     # Já recebida
    recompensas_futuras = []       # Nível > current_level
    
    for recompensa in todas_recompensas:
        try:
            nivel_recompensa = int(recompensa.referencia)
        except (ValueError, TypeError):
            continue
        
        if recompensa.id in recompensas_recebidas_ids:
            recompensas_recebidas.append({
                'recompensa': recompensa,
                'nivel': nivel_recompensa
            })
        elif nivel_recompensa <= current_level:
            recompensas_disponiveis.append({
                'recompensa': recompensa,
                'nivel': nivel_recompensa
            })
        else:
            recompensas_futuras.append({
                'recompensa': recompensa,
                'nivel': nivel_recompensa,
                'niveis_faltantes': nivel_recompensa - current_level
            })
    
    context = {
        'current_level': current_level,
        'recompensas_disponiveis': recompensas_disponiveis,
        'recompensas_recebidas': recompensas_recebidas,
        'recompensas_futuras': recompensas_futuras,
        'total_disponiveis': len(recompensas_disponiveis),
        'total_recebidas': len(recompensas_recebidas),
        'total_futuras': len(recompensas_futuras),
    }
    
    return render(request, 'level_rewards/view.html', context)

