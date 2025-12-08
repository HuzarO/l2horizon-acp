from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.lineage.games.models import Recompensa, RecompensaRecebida
from apps.main.home.models import Conquista, ConquistaUsuario
from utils.achievement_progress import calcular_progresso_conquista


@login_required
def achievement_rewards_view(request):
    """Lista todas as premiações de conquistas disponíveis com progresso"""
    
    user = request.user
    
    # Obter todas as conquistas para mostrar progresso
    todas_conquistas = Conquista.objects.all().order_by('nome')
    
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
    total_conquistas_disponiveis = todas_conquistas.count()
    
    # Processar todas as conquistas com progresso
    conquistas_com_progresso = []
    for conquista in todas_conquistas:
        progresso = calcular_progresso_conquista(user, conquista)
        conquistas_com_progresso.append({
            'conquista': conquista,
            'progresso': progresso,
            'tem_recompensa': recompensas_conquista.filter(referencia=conquista.codigo).exists(),
        })
    
    # Ordenar: completadas primeiro, depois por progresso
    conquistas_com_progresso.sort(key=lambda x: (
        not x['progresso']['completada'],  # Completadas primeiro
        -x['progresso']['progresso_percent']  # Maior progresso primeiro
    ))
    
    # Processar recompensas por conquista
    recompensas_conquista_list = []
    for recompensa in recompensas_conquista:
        # Buscar a conquista pelo código
        conquista = Conquista.objects.filter(codigo=recompensa.referencia).first()
        conquista_desbloqueada = conquista and conquista.id in conquistas_usuario_ids if conquista else False
        recebida = recompensa.id in recompensas_recebidas_ids
        
        # Calcular progresso se tiver conquista
        progresso = None
        if conquista:
            progresso = calcular_progresso_conquista(user, conquista)
        
        recompensas_conquista_list.append({
            'recompensa': recompensa,
            'conquista': conquista,
            'conquista_desbloqueada': conquista_desbloqueada,
            'recebida': recebida,
            'pode_receber': conquista_desbloqueada and not recebida,
            'progresso': progresso,
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
        progresso_percent = min(100, int((total_conquistas_usuario / quantidade_necessaria) * 100)) if quantidade_necessaria > 0 else 0
        
        recompensas_multiplas_list.append({
            'recompensa': recompensa,
            'quantidade_necessaria': quantidade_necessaria,
            'total_conquistas': total_conquistas_usuario,
            'recebida': recebida,
            'pode_receber': pode_receber,
            'progresso_percent': progresso_percent,
            'falta': max(0, quantidade_necessaria - total_conquistas_usuario),
        })
    
    # Ordenar por quantidade necessária
    recompensas_multiplas_list.sort(key=lambda x: x['quantidade_necessaria'])
    
    # Calcular totais
    total_recebidos = sum(1 for r in recompensas_conquista_list if r['recebida']) + sum(1 for r in recompensas_multiplas_list if r['recebida'])
    total_disponiveis = sum(1 for r in recompensas_conquista_list if r['pode_receber']) + sum(1 for r in recompensas_multiplas_list if r['pode_receber'])
    
    # Calcular porcentagem de conquistas completadas (platinadas)
    conquistas_completadas = sum(1 for c in conquistas_com_progresso if c['progresso']['completada'])
    porcentagem_platinado = int((conquistas_completadas / total_conquistas_disponiveis * 100)) if total_conquistas_disponiveis > 0 else 0
    
    context = {
        'conquistas_com_progresso': conquistas_com_progresso,
        'recompensas_conquista': recompensas_conquista_list,
        'recompensas_multiplas': recompensas_multiplas_list,
        'total_conquistas_usuario': total_conquistas_usuario,
        'total_conquistas_disponiveis': total_conquistas_disponiveis,
        'conquistas_completadas': conquistas_completadas,
        'porcentagem_platinado': porcentagem_platinado,
        'total_recebidos': total_recebidos,
        'total_disponiveis': total_disponiveis,
    }
    
    return render(request, 'dashboard_custom/achievement_rewards.html', context)

