from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils.translation import gettext as _
from apps.main.home.decorator import conditional_otp_required
import random

from ..models import DiceGameConfig, DiceGameHistory


@conditional_otp_required
def dice_game_page(request):
    """Página principal do Dice Game"""
    config = DiceGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        messages.error(request, _("Dice Game não está disponível no momento."))
        return redirect('dashboard')
    
    # Histórico recente do usuário
    user_history = DiceGameHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    # Estatísticas do usuário
    from django.db.models import Sum, Count, Q
    stats = DiceGameHistory.objects.filter(user=request.user).aggregate(
        total_games=Count('id'),
        total_won=Count('id', filter=Q(won=True)),
        total_bet=Sum('bet_amount'),
        total_prize=Sum('prize_amount')
    )
    
    # Calcular win rate
    win_rate = 0
    if stats['total_games'] and stats['total_games'] > 0:
        win_rate = (stats['total_won'] / stats['total_games']) * 100
    
    # Lucro/Prejuízo
    profit = (stats['total_prize'] or 0) - (stats['total_bet'] or 0)
    
    context = {
        'config': config,
        'user_history': user_history,
        'user_fichas': request.user.fichas,
        'stats': stats,
        'win_rate': round(win_rate, 2),
        'profit': profit,
    }
    
    return render(request, 'dice_game/dice_game.html', context)


@conditional_otp_required
@transaction.atomic
def dice_game_play(request):
    """Processar jogada no Dice Game"""
    if request.method != 'POST':
        return JsonResponse({'error': _('Método inválido')}, status=400)
    
    config = DiceGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        return JsonResponse({'error': _('Dice Game não disponível')}, status=400)
    
    # Pegar dados do POST
    try:
        bet_type = request.POST.get('bet_type')
        bet_amount = int(request.POST.get('bet_amount', 0))
        bet_value = request.POST.get('bet_value')  # Número específico (1-6)
    except (ValueError, TypeError):
        return JsonResponse({'error': _('Dados inválidos')}, status=400)
    
    # Validar tipo de aposta
    valid_bet_types = ['number', 'even', 'odd', 'high', 'low']
    if bet_type not in valid_bet_types:
        return JsonResponse({'error': _('Tipo de aposta inválido')}, status=400)
    
    # Validar valor da aposta
    if bet_amount < config.min_bet or bet_amount > config.max_bet:
        return JsonResponse({
            'error': _('Aposta deve estar entre {} e {} fichas').format(
                config.min_bet, config.max_bet
            )
        }, status=400)
    
    # Verificar fichas do usuário
    user = request.user
    if user.fichas < bet_amount:
        return JsonResponse({
            'error': _('Você não tem fichas suficientes')
        }, status=400)
    
    # Validar número específico
    bet_value_int = None
    if bet_type == 'number':
        try:
            bet_value_int = int(bet_value)
            if bet_value_int < 1 or bet_value_int > 6:
                return JsonResponse({'error': _('Número deve estar entre 1 e 6')}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': _('Número inválido')}, status=400)
    
    # Deduzir fichas
    user.fichas -= bet_amount
    user.save(update_fields=['fichas'])
    
    # Rolar o dado
    dice_result = random.randint(1, 6)
    
    # Verificar se ganhou
    won = False
    multiplier = 0
    
    if bet_type == 'number':
        if dice_result == bet_value_int:
            won = True
            multiplier = config.specific_number_multiplier
    elif bet_type == 'even':
        if dice_result % 2 == 0:
            won = True
            multiplier = config.even_odd_multiplier
    elif bet_type == 'odd':
        if dice_result % 2 != 0:
            won = True
            multiplier = config.even_odd_multiplier
    elif bet_type == 'high':
        if dice_result >= 4:
            won = True
            multiplier = config.high_low_multiplier
    elif bet_type == 'low':
        if dice_result <= 3:
            won = True
            multiplier = config.high_low_multiplier
    
    # Calcular prêmio
    prize_amount = 0
    if won:
        prize_amount = int(bet_amount * multiplier)
        user.fichas += prize_amount
        user.save(update_fields=['fichas'])
    
    # Salvar histórico
    history = DiceGameHistory.objects.create(
        user=user,
        bet_type=bet_type,
        bet_value=bet_value_int,
        bet_amount=bet_amount,
        dice_result=dice_result,
        won=won,
        prize_amount=prize_amount
    )
    
    response_data = {
        'success': True,
        'dice_result': dice_result,
        'won': won,
        'prize_amount': prize_amount,
        'user_fichas': user.fichas,
        'multiplier': multiplier if won else 0,
        'message': _('Parabéns! Você ganhou {} fichas!').format(prize_amount) if won else _('Não foi dessa vez!')
    }
    
    return JsonResponse(response_data)


@conditional_otp_required
def dice_game_leaderboard(request):
    """Leaderboard do Dice Game"""
    from django.db.models import Sum, Count, Q, F
    
    # Top ganhadores (maior lucro)
    top_winners = DiceGameHistory.objects.values(
        'user__username'
    ).annotate(
        total_bet=Sum('bet_amount'),
        total_prize=Sum('prize_amount'),
        profit=F('total_prize') - F('total_bet'),
        total_games=Count('id'),
        wins=Count('id', filter=Q(won=True))
    ).order_by('-profit')[:10]
    
    # Adicionar win rate
    for winner in top_winners:
        if winner['total_games'] > 0:
            winner['win_rate'] = round((winner['wins'] / winner['total_games']) * 100, 2)
        else:
            winner['win_rate'] = 0
    
    # Top apostadores (mais jogos)
    top_players = DiceGameHistory.objects.values(
        'user__username'
    ).annotate(
        total_games=Count('id'),
        wins=Count('id', filter=Q(won=True))
    ).order_by('-total_games')[:10]
    
    for player in top_players:
        if player['total_games'] > 0:
            player['win_rate'] = round((player['wins'] / player['total_games']) * 100, 2)
        else:
            player['win_rate'] = 0
    
    # Maiores apostas ganhas
    biggest_wins = DiceGameHistory.objects.filter(
        won=True
    ).select_related('user').order_by('-prize_amount')[:10]
    
    context = {
        'top_winners': top_winners,
        'top_players': top_players,
        'biggest_wins': biggest_wins,
    }
    
    return render(request, 'dice_game/leaderboard.html', context)


@conditional_otp_required
def dice_game_statistics(request):
    """Estatísticas detalhadas do Dice Game"""
    from django.db.models import Count, Avg, Sum
    
    # Estatísticas gerais
    total_games = DiceGameHistory.objects.count()
    total_wins = DiceGameHistory.objects.filter(won=True).count()
    
    # Distribuição de resultados do dado
    dice_distribution = []
    for i in range(1, 7):
        count = DiceGameHistory.objects.filter(dice_result=i).count()
        dice_distribution.append({
            'number': i,
            'count': count,
            'percentage': round((count / total_games * 100) if total_games > 0 else 0, 2)
        })
    
    # Tipos de apostas mais populares
    bet_type_stats = DiceGameHistory.objects.values('bet_type').annotate(
        count=Count('id'),
        wins=Count('id', filter=Q(won=True)),
        total_bet=Sum('bet_amount'),
        total_prize=Sum('prize_amount')
    ).order_by('-count')
    
    context = {
        'total_games': total_games,
        'total_wins': total_wins,
        'win_rate': round((total_wins / total_games * 100) if total_games > 0 else 0, 2),
        'dice_distribution': dice_distribution,
        'bet_type_stats': bet_type_stats,
    }
    
    return render(request, 'dice_game/statistics.html', context)

