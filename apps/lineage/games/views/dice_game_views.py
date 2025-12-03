from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils.translation import gettext as _
from apps.main.home.decorator import conditional_otp_required
import random

from ..models import DiceGameConfig, DiceGameHistory, DiceGamePrize, Bag, BagItem


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
    
    # Informações para as regras
    total_plays = stats['total_games'] or 0
    last_play = user_history.first()
    last_bet_type = last_play.bet_type if last_play else None
    must_play_number = (total_plays + 1) % 5 == 0  # Próxima jogada é múltiplo de 5
    
    context = {
        'config': config,
        'user_history': user_history,
        'user_fichas': request.user.fichas,
        'stats': stats,
        'win_rate': round(win_rate, 2),
        'profit': profit,
        'last_bet_type': last_bet_type,
        'must_play_number': must_play_number,
        'total_plays': total_plays,
        'min_bet_for_number': 10,
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
    
    user = request.user
    
    # Verificar histórico do jogador
    user_history = DiceGameHistory.objects.filter(user=user).order_by('-created_at')
    total_plays = user_history.count()
    
    # REGRA 1: Não pode escolher a mesma modalidade duas vezes seguidas
    last_play = user_history.first()
    if last_play and last_play.bet_type == bet_type:
        return JsonResponse({
            'error': _('Você não pode escolher a mesma modalidade duas vezes seguidas! Escolha outra opção.')
        }, status=400)
    
    # REGRA 2: A cada 5 jogadas, deve escolher "Número Específico"
    if (total_plays + 1) % 5 == 0:  # Próxima jogada será múltiplo de 5
        if bet_type != 'number':
            return JsonResponse({
                'error': _('A cada 5 jogadas você deve escolher "Número Específico"! Esta é sua {}ª jogada.').format(total_plays + 1)
            }, status=400)
    
    # REGRA 3: Aposta mínima de 10 fichas para número específico
    min_bet_for_number = 10
    if bet_type == 'number':
        if bet_amount < min_bet_for_number:
            return JsonResponse({
                'error': _('A aposta mínima para "Número Específico" é {} fichas.').format(min_bet_for_number)
            }, status=400)
    
    # Validar valor da aposta (limites gerais)
    if bet_amount < config.min_bet or bet_amount > config.max_bet:
        return JsonResponse({
            'error': _('Aposta deve estar entre {} e {} fichas').format(
                config.min_bet, config.max_bet
            )
        }, status=400)
    
    # Verificar fichas do usuário
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
    bonus_prize = None
    bonus_item = None
    bonus_fichas = 0
    
    if won:
        prize_amount = int(bet_amount * multiplier)
        user.fichas += prize_amount
        user.save(update_fields=['fichas'])
        
        # Verificar prêmios bonus
        active_prizes = DiceGamePrize.objects.filter(is_active=True)
        for prize in active_prizes:
            # Verificar se ganha o prêmio pela chance
            if random.random() * 100 <= prize.drop_chance:
                bonus_prize = prize
                
                # Adicionar fichas bonus
                if prize.fichas_bonus > 0:
                    bonus_fichas = prize.fichas_bonus
                    user.fichas += bonus_fichas
                    user.save(update_fields=['fichas'])
                
                # Adicionar item à bag
                if prize.item:
                    bonus_item = prize.item
                    bag, bag_created = Bag.objects.get_or_create(user=user)
                    bag_item, created = BagItem.objects.get_or_create(
                        bag=bag,
                        item_id=prize.item.item_id,
                        enchant=prize.item.enchant,
                        defaults={
                            'item_name': prize.item.name,
                            'quantity': 1,
                        }
                    )
                    if not created:
                        bag_item.quantity += 1
                        bag_item.save()
                
                break  # Apenas um prêmio bonus por vitória
    
    # Salvar histórico
    history = DiceGameHistory.objects.create(
        user=user,
        bet_type=bet_type,
        bet_value=bet_value_int,
        bet_amount=bet_amount,
        dice_result=dice_result,
        won=won,
        prize_amount=prize_amount,
        bonus_prize=bonus_prize
    )
    
    # Construir mensagem
    message = ''
    if won:
        message = _('Parabéns! Você ganhou {} fichas!').format(prize_amount)
        if bonus_prize:
            if bonus_fichas > 0 and bonus_item:
                message += _(' 🎁 Prêmio Bonus: {} fichas + {}!').format(bonus_fichas, bonus_item.name)
            elif bonus_fichas > 0:
                message += _(' 🎁 Prêmio Bonus: {} fichas!').format(bonus_fichas)
            elif bonus_item:
                message += _(' 🎁 Prêmio Bonus: {}!').format(bonus_item.name)
    else:
        message = _('Não foi dessa vez!')
    
    response_data = {
        'success': True,
        'dice_result': dice_result,
        'won': won,
        'prize_amount': prize_amount,
        'user_fichas': user.fichas,
        'multiplier': multiplier if won else 0,
        'message': message,
        'bonus_prize': {
            'name': bonus_prize.name if bonus_prize else None,
            'fichas': bonus_fichas,
            'item': {
                'name': bonus_item.name,
                'enchant': bonus_item.enchant,
                'rarity': bonus_item.rarity
            } if bonus_item else None
        } if bonus_prize else None
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

