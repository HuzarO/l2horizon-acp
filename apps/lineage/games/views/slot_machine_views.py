from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils.translation import gettext as _
from apps.main.home.decorator import conditional_otp_required
import random
import json

from ..models import (
    SlotMachineConfig, SlotMachineSymbol, SlotMachinePrize,
    SlotMachineHistory, Bag, BagItem, Item, TokenHistory
)


@conditional_otp_required
def slot_machine_page(request):
    """Página principal da Slot Machine"""
    config = SlotMachineConfig.objects.filter(is_active=True).first()
    
    if not config:
        messages.error(request, _("Slot Machine não está disponível no momento."))
        return redirect('dashboard')
    
    symbols = SlotMachineSymbol.objects.all()
    recent_wins = SlotMachineHistory.objects.filter(
        prize_won__isnull=False
    ).select_related('user', 'prize_won').order_by('-created_at')[:10]
    
    user_history = SlotMachineHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    context = {
        'config': config,
        'symbols': symbols,
        'recent_wins': recent_wins,
        'user_history': user_history,
        'user_fichas': request.user.fichas,
    }
    
    return render(request, 'slot_machine/slot_machine.html', context)


@conditional_otp_required
@transaction.atomic
def slot_machine_spin(request):
    """Processar giro da slot machine"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': _('Método inválido')}, status=400)
        
        config = SlotMachineConfig.objects.filter(is_active=True).first()
        
        if not config:
            return JsonResponse({'error': _('Slot Machine não disponível')}, status=400)
        
        # Verificar fichas do usuário
        user = request.user
        if user.fichas < config.cost_per_spin:
            return JsonResponse({
                'error': _('Você não tem fichas suficientes. Necessário: {}').format(config.cost_per_spin)
            }, status=400)
        
        # Deduzir fichas
        user.fichas -= config.cost_per_spin
        user.save(update_fields=['fichas'])
        
        # Registra gasto no histórico de fichas
        TokenHistory.objects.create(
            user=user,
            transaction_type='spend',
            game_type='slot_machine',
            amount=config.cost_per_spin,
            description=f'Giro na slot machine (custo: {config.cost_per_spin} fichas)',
            metadata={'cost_per_spin': config.cost_per_spin}
        )
        
        # Pegar todos os símbolos com seus pesos
        symbols = list(SlotMachineSymbol.objects.all())
        
        if not symbols:
            return JsonResponse({'error': _('Nenhum símbolo configurado')}, status=400)
        
        # Gerar 3 símbolos aleatórios baseados nos pesos
        weights = [s.weight for s in symbols]
        result_symbols = random.choices(symbols, weights=weights, k=3)
        
        # Verificar se é jackpot (chance muito baixa)
        is_jackpot = random.random() < (config.jackpot_chance / 100)
        
        # Contar símbolos iguais
        symbol_counts = {}
        for sym in result_symbols:
            symbol_counts[sym.id] = symbol_counts.get(sym.id, 0) + 1
        
        # Verificar prêmio
        prize_won = None
        fichas_won = 0
        item_won = None
        
        if is_jackpot:
            fichas_won = config.jackpot_amount
            config.jackpot_amount = 100  # Reset jackpot
            config.save()
        else:
            # Verificar combinações
            for symbol_id, count in symbol_counts.items():
                prize = SlotMachinePrize.objects.filter(
                    config=config,
                    symbol_id=symbol_id,
                    matches_required__lte=count
                ).order_by('-matches_required').first()
                
                if prize:
                    prize_won = prize
                    fichas_won = prize.fichas_prize
                    
                    # Se tiver item como prêmio, adicionar à bag
                    if prize.item:
                        item_won = prize.item
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
                    
                    break
        
        # Adicionar fichas ganhas
        if fichas_won > 0:
            user.fichas += fichas_won
            user.save(update_fields=['fichas'])
            
            # Registra ganho no histórico de fichas
            TokenHistory.objects.create(
                user=user,
                transaction_type='earn',
                game_type='slot_machine',
                amount=fichas_won,
                description=f'Ganhou {fichas_won} fichas na slot machine',
                metadata={'is_jackpot': is_jackpot, 'prize_id': prize_won.id if prize_won else None}
            )
        
        # Incrementar jackpot progressivo
        if not is_jackpot:
            config.jackpot_amount += int(config.cost_per_spin * 0.1)
            config.save()
        
        # Salvar histórico
        symbols_result = json.dumps([s.symbol for s in result_symbols])
        history = SlotMachineHistory.objects.create(
            user=user,
            config=config,
            symbols_result=symbols_result,
            prize_won=prize_won,
            is_jackpot=is_jackpot,
            fichas_won=fichas_won
        )
        
        # Atualizar progresso de quests relacionadas ao slot machine
        if item_won:
            try:
                from apps.lineage.games.services.quest_progress_tracker import check_and_update_all_quests
                check_and_update_all_quests(user)
            except Exception as e:
                # Não falhar se houver erro no tracking
                pass
        
        response_data = {
            'success': True,
            'symbols': [
                {
                    'symbol': s.symbol,
                    'icon': s.icon,
                    'display_name': s.get_symbol_display()
                } for s in result_symbols
            ],
            'is_jackpot': is_jackpot,
            'fichas_won': fichas_won,
            'item_won': {
                'name': item_won.name,
                'enchant': item_won.enchant,
                'rarity': item_won.rarity
            } if item_won else None,
            'user_fichas': user.fichas,
            'current_jackpot': config.jackpot_amount,
            'prize_name': prize_won.symbol.get_symbol_display() if prize_won else None
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': _('Erro ao processar giro: {}').format(str(e))
        }, status=500)


@conditional_otp_required
def slot_machine_leaderboard(request):
    """Leaderboard da Slot Machine"""
    from django.db.models import Sum, Count
    
    # Top ganhadores (por fichas ganhas)
    top_winners = SlotMachineHistory.objects.values(
        'user__username'
    ).annotate(
        total_won=Sum('fichas_won'),
        total_plays=Count('id')
    ).order_by('-total_won')[:10]
    
    # Top jogadores (por número de jogadas)
    top_players = SlotMachineHistory.objects.values(
        'user__username'
    ).annotate(
        total_plays=Count('id')
    ).order_by('-total_plays')[:10]
    
    # Maiores prêmios individuais
    biggest_wins = SlotMachineHistory.objects.filter(
        fichas_won__gt=0
    ).select_related('user').order_by('-fichas_won')[:10]
    
    context = {
        'top_winners': top_winners,
        'top_players': top_players,
        'biggest_wins': biggest_wins,
    }
    
    return render(request, 'slot_machine/leaderboard.html', context)

