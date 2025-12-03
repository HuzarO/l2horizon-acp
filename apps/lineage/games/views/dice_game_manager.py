from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _
from django.db.models import Count, Sum, Avg, Q, F
from django.contrib import messages

from ..models import DiceGameConfig, DiceGameHistory, DiceGamePrize, Item
from ..forms import DiceGameConfigForm, DiceGamePrizeForm


@staff_member_required
def dashboard(request):
    """Dashboard de gerenciamento do Dice Game"""
    
    # Processar formulários
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_default_config':
            # Criar configuração padrão apenas se não existir nenhuma
            existing_config = DiceGameConfig.objects.first()
            if existing_config:
                messages.info(request, _('Configuração já existe!'))
            else:
                config = DiceGameConfig.objects.create(
                    min_bet=1,
                    max_bet=100,
                    is_active=True,
                    specific_number_multiplier=5.0,
                    even_odd_multiplier=2.0,
                    high_low_multiplier=2.0
                )
                messages.success(request, _('✅ Configuração criada com sucesso!'))
            return redirect('games:dice_game_manager')
        
        elif action == 'update_config':
            config_id = request.POST.get('config_id')
            if config_id:
                config = get_object_or_404(DiceGameConfig, id=config_id)
                
                # Atualizar campos manualmente para garantir que checkbox funcione
                config.min_bet = int(request.POST.get('min_bet', config.min_bet))
                config.max_bet = int(request.POST.get('max_bet', config.max_bet))
                config.specific_number_multiplier = float(request.POST.get('specific_number_multiplier', config.specific_number_multiplier))
                config.even_odd_multiplier = float(request.POST.get('even_odd_multiplier', config.even_odd_multiplier))
                config.high_low_multiplier = float(request.POST.get('high_low_multiplier', config.high_low_multiplier))
                config.is_active = request.POST.get('is_active') == 'on'  # Checkbox
                config.save()
                
                messages.success(request, _('Configuração atualizada com sucesso!'))
            else:
                form = DiceGameConfigForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, _('Configuração criada com sucesso!'))
                else:
                    messages.error(request, _('Erro ao criar configuração.'))
            return redirect('games:dice_game_manager')
        
        elif action == 'add_prize':
            form = DiceGamePrizeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('Prêmio adicionado com sucesso!'))
            else:
                messages.error(request, _('Erro ao adicionar prêmio.'))
            return redirect('games:dice_game_manager')
        
        elif action == 'edit_prize':
            prize_id = request.POST.get('prize_id')
            prize = get_object_or_404(DiceGamePrize, id=prize_id)
            form = DiceGamePrizeForm(request.POST, instance=prize)
            if form.is_valid():
                form.save()
                messages.success(request, _('Prêmio atualizado com sucesso!'))
            else:
                messages.error(request, _('Erro ao atualizar prêmio.'))
            return redirect('games:dice_game_manager')
        
        elif action == 'delete_prize':
            prize_id = request.POST.get('prize_id')
            prize = get_object_or_404(DiceGamePrize, id=prize_id)
            prize.delete()
            messages.success(request, _('Prêmio removido com sucesso!'))
            return redirect('games:dice_game_manager')
    
    # Configurações
    config = DiceGameConfig.objects.filter(is_active=True).first()
    all_configs = DiceGameConfig.objects.all()
    config_form = DiceGameConfigForm(instance=config) if config else DiceGameConfigForm()
    
    # Prêmios
    all_prizes = DiceGamePrize.objects.all().order_by('-drop_chance')
    prize_form = DiceGamePrizeForm()
    
    # Items disponíveis
    items = Item.objects.filter(can_be_populated=True).order_by('name')
    
    # Estatísticas gerais
    total_games = DiceGameHistory.objects.count()
    total_wins = DiceGameHistory.objects.filter(won=True).count()
    total_bet = DiceGameHistory.objects.aggregate(total=Sum('bet_amount'))['total'] or 0
    total_prize = DiceGameHistory.objects.aggregate(total=Sum('prize_amount'))['total'] or 0
    house_profit = total_bet - total_prize
    
    # Estatísticas por tipo de aposta
    bet_type_stats = DiceGameHistory.objects.values('bet_type').annotate(
        total_games=Count('id'),
        wins=Count('id', filter=Q(won=True)),
        total_bet=Sum('bet_amount'),
        total_prize=Sum('prize_amount')
    ).order_by('-total_games')
    
    # Adicionar win rate e lucro da casa
    for stat in bet_type_stats:
        stat['win_rate'] = round((stat['wins'] / stat['total_games'] * 100) if stat['total_games'] > 0 else 0, 2)
        stat['house_profit'] = stat['total_bet'] - stat['total_prize']
    
    # Distribuição de resultados do dado
    dice_distribution = []
    for i in range(1, 7):
        count = DiceGameHistory.objects.filter(dice_result=i).count()
        dice_distribution.append({
            'number': i,
            'count': count,
            'percentage': round((count / total_games * 100) if total_games > 0 else 0, 2)
        })
    
    # Últimas jogadas
    recent_plays = DiceGameHistory.objects.select_related('user').order_by('-created_at')[:20]
    
    # Top ganhadores (maior lucro)
    top_winners = DiceGameHistory.objects.values('user__username').annotate(
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
    top_players = DiceGameHistory.objects.values('user__username').annotate(
        total_games=Count('id'),
        total_bet=Sum('bet_amount')
    ).order_by('-total_games')[:10]
    
    context = {
        'config': config,
        'all_configs': all_configs,
        'config_form': config_form,
        'all_prizes': all_prizes,
        'prize_form': prize_form,
        'items': items,
        'total_games': total_games,
        'total_wins': total_wins,
        'win_rate': round((total_wins / total_games * 100) if total_games > 0 else 0, 2),
        'total_bet': total_bet,
        'total_prize': total_prize,
        'house_profit': house_profit,
        'bet_type_stats': bet_type_stats,
        'dice_distribution': dice_distribution,
        'recent_plays': recent_plays,
        'top_winners': top_winners,
        'top_players': top_players,
    }
    
    return render(request, 'dice_game/manager/dashboard.html', context)

