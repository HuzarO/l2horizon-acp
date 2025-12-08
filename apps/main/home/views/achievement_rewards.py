from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.lineage.games.models import Recompensa, RecompensaRecebida
from apps.main.home.models import Conquista, ConquistaUsuario


@login_required
def achievement_rewards_view(request):
    """Lista todas as premiações de conquistas disponíveis"""
    
    user = request.user
    
    # Obter todas as recompensas de conquistas
    recompensas_conquista = Recompensa.objects.filter(tipo='CONQUISTA').order_by('referencia')
    recompensas_multiplas = Recompensa.objects.filter(tipo='CONQUISTAS_MULTIPLAS').order_by('referencia')
    
    # IDs de recompensas já recebidas pelo usuário
    recompensas_recebidas_ids = set(
        RecompensaRecebida.objects.filter(user=user).values_list('recompensa_id', flat=True)
    )
    
    # IDs de conquistas do usuário
    conquistas_usuario_ids = set(
        ConquistaUsuario.objects.filter(usuario=user).values_list('conquista_id', flat=True)
    )
    
    # Total de conquistas do usuário
    total_conquistas_usuario = len(conquistas_usuario_ids)
    
    # Processar recompensas por conquista
    recompensas_conquista_list = []
    for recompensa in recompensas_conquista:
        # Buscar a conquista pelo código
        conquista = Conquista.objects.filter(codigo=recompensa.referencia).first()
        conquista_desbloqueada = conquista and conquista.id in conquistas_usuario_ids if conquista else False
        recebida = recompensa.id in recompensas_recebidas_ids
        
        recompensas_conquista_list.append({
            'recompensa': recompensa,
            'conquista': conquista,
            'conquista_desbloqueada': conquista_desbloqueada,
            'recebida': recebida,
            'pode_receber': conquista_desbloqueada and not recebida,
        })
    
    # Processar recompensas por quantidade
    recompensas_multiplas_list = []
    for recompensa in recompensas_multiplas:
        try:
            quantidade_necessaria = int(recompensa.referencia)
        except (ValueError, TypeError):
            continue
        
        recebida = recompensa.id in recompensas_recebidas_ids
        pode_receber = total_conquistas_usuario >= quantidade_necessaria and not recebida
        
        recompensas_multiplas_list.append({
            'recompensa': recompensa,
            'quantidade_necessaria': quantidade_necessaria,
            'total_conquistas': total_conquistas_usuario,
            'recebida': recebida,
            'pode_receber': pode_receber,
            'progresso_percent': min(100, int((total_conquistas_usuario / quantidade_necessaria) * 100)) if quantidade_necessaria > 0 else 0,
        })
    
    # Ordenar por quantidade necessária
    recompensas_multiplas_list.sort(key=lambda x: x['quantidade_necessaria'])
    
    # Calcular totais
    total_recebidos = sum(1 for r in recompensas_conquista_list if r['recebida']) + sum(1 for r in recompensas_multiplas_list if r['recebida'])
    total_disponiveis = sum(1 for r in recompensas_conquista_list if r['pode_receber']) + sum(1 for r in recompensas_multiplas_list if r['pode_receber'])
    
    context = {
        'recompensas_conquista': recompensas_conquista_list,
        'recompensas_multiplas': recompensas_multiplas_list,
        'total_conquistas_usuario': total_conquistas_usuario,
        'total_recebidos': total_recebidos,
        'total_disponiveis': total_disponiveis,
    }
    
    return render(request, 'dashboard_custom/achievement_rewards.html', context)

