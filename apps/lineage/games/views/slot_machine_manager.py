from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _
from django.db.models import Count, Sum
from django.contrib import messages
from django.db import transaction

from ..models import (
    SlotMachineConfig, SlotMachineSymbol, SlotMachinePrize,
    SlotMachineHistory, Item
)
from ..forms import SlotMachineConfigForm, SlotMachineSymbolForm, SlotMachinePrizeForm


@staff_member_required
def dashboard(request):
    """Dashboard de gerenciamento do Slot Machine"""
    
    # Processar formulários
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_default_config':
            # Criar configuração padrão
            config, created = SlotMachineConfig.objects.get_or_create(
                name='Slot Machine Principal',
                defaults={
                    'cost_per_spin': 1,
                    'is_active': True,
                    'jackpot_amount': 1000,
                    'jackpot_chance': 0.1
                }
            )
            
            if created:
                messages.success(request, _('✅ Configuração criada com sucesso!'))
            else:
                messages.info(request, _('Configuração já existe!'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'auto_populate_symbols':
            # Popular símbolos automaticamente
            symbols_data = [
                {'symbol': 'sword', 'weight': 15, 'icon': '⚔️'},
                {'symbol': 'shield', 'weight': 15, 'icon': '🛡️'},
                {'symbol': 'potion', 'weight': 20, 'icon': '🧪'},
                {'symbol': 'gem', 'weight': 10, 'icon': '💎'},
                {'symbol': 'gold', 'weight': 25, 'icon': '🪙'},
                {'symbol': 'armor', 'weight': 12, 'icon': '🥋'},
                {'symbol': 'bow', 'weight': 13, 'icon': '🏹'},
                {'symbol': 'staff', 'weight': 8, 'icon': '🪄'},
                {'symbol': 'jackpot', 'weight': 1, 'icon': '💰'},
            ]
            
            count = 0
            for symbol_data in symbols_data:
                symbol, created = SlotMachineSymbol.objects.get_or_create(
                    symbol=symbol_data['symbol'],
                    defaults={
                        'weight': symbol_data['weight'],
                        'icon': symbol_data['icon']
                    }
                )
                if created:
                    count += 1
            
            messages.success(request, _('✅ {} símbolos criados automaticamente!').format(count))
            return redirect('games:slot_machine_manager')
        
        elif action == 'quick_setup':
            # Setup completo: configuração + símbolos + prêmios
            # 1. Criar configuração
            config, config_created = SlotMachineConfig.objects.get_or_create(
                name='Slot Machine Principal',
                defaults={
                    'cost_per_spin': 1,
                    'is_active': True,
                    'jackpot_amount': 1000,
                    'jackpot_chance': 0.1
                }
            )
            
            # 2. Criar símbolos
            symbols_data = [
                {'symbol': 'sword', 'weight': 15, 'icon': '⚔️'},
                {'symbol': 'shield', 'weight': 15, 'icon': '🛡️'},
                {'symbol': 'potion', 'weight': 20, 'icon': '🧪'},
                {'symbol': 'gem', 'weight': 10, 'icon': '💎'},
                {'symbol': 'gold', 'weight': 25, 'icon': '🪙'},
                {'symbol': 'armor', 'weight': 12, 'icon': '🥋'},
                {'symbol': 'bow', 'weight': 13, 'icon': '🏹'},
                {'symbol': 'staff', 'weight': 8, 'icon': '🪄'},
                {'symbol': 'jackpot', 'weight': 1, 'icon': '💰'},
            ]
            
            symbols_count = 0
            for symbol_data in symbols_data:
                symbol, created = SlotMachineSymbol.objects.get_or_create(
                    symbol=symbol_data['symbol'],
                    defaults={
                        'weight': symbol_data['weight'],
                        'icon': symbol_data['icon']
                    }
                )
                if created:
                    symbols_count += 1
            
            # 3. Criar prêmios
            prizes_data = [
                {'symbol': 'jackpot', 'matches': 3, 'fichas': 10000},
                {'symbol': 'gem', 'matches': 3, 'fichas': 500},
                {'symbol': 'staff', 'matches': 3, 'fichas': 300},
                {'symbol': 'armor', 'matches': 3, 'fichas': 200},
                {'symbol': 'bow', 'matches': 3, 'fichas': 150},
                {'symbol': 'sword', 'matches': 3, 'fichas': 100},
                {'symbol': 'shield', 'matches': 3, 'fichas': 100},
                {'symbol': 'gold', 'matches': 3, 'fichas': 50},
                {'symbol': 'potion', 'matches': 3, 'fichas': 30},
                {'symbol': 'gem', 'matches': 2, 'fichas': 50},
                {'symbol': 'sword', 'matches': 2, 'fichas': 20},
                {'symbol': 'shield', 'matches': 2, 'fichas': 20},
            ]
            
            prizes_count = 0
            for prize_data in prizes_data:
                symbol = SlotMachineSymbol.objects.filter(symbol=prize_data['symbol']).first()
                if symbol:
                    prize, created = SlotMachinePrize.objects.get_or_create(
                        config=config,
                        symbol=symbol,
                        matches_required=prize_data['matches'],
                        defaults={'fichas_prize': prize_data['fichas']}
                    )
                    if created:
                        prizes_count += 1
            
            messages.success(request, _('✅ Setup completo! Criados: {} símbolos, {} prêmios!').format(symbols_count, prizes_count))
            return redirect('games:slot_machine_manager')
        
        elif action == 'auto_populate_prizes':
            # Popular prêmios automaticamente
            config = SlotMachineConfig.objects.filter(is_active=True).first()
            if not config:
                messages.error(request, _('Crie uma configuração primeiro!'))
                return redirect('games:slot_machine_manager')
            
            prizes_data = [
                {'symbol': 'jackpot', 'matches': 3, 'fichas': 10000},
                {'symbol': 'gem', 'matches': 3, 'fichas': 500},
                {'symbol': 'staff', 'matches': 3, 'fichas': 300},
                {'symbol': 'armor', 'matches': 3, 'fichas': 200},
                {'symbol': 'bow', 'matches': 3, 'fichas': 150},
                {'symbol': 'sword', 'matches': 3, 'fichas': 100},
                {'symbol': 'shield', 'matches': 3, 'fichas': 100},
                {'symbol': 'gold', 'matches': 3, 'fichas': 50},
                {'symbol': 'potion', 'matches': 3, 'fichas': 30},
                {'symbol': 'gem', 'matches': 2, 'fichas': 50},
                {'symbol': 'sword', 'matches': 2, 'fichas': 20},
                {'symbol': 'shield', 'matches': 2, 'fichas': 20},
            ]
            
            count = 0
            for prize_data in prizes_data:
                symbol = SlotMachineSymbol.objects.filter(symbol=prize_data['symbol']).first()
                if symbol:
                    prize, created = SlotMachinePrize.objects.get_or_create(
                        config=config,
                        symbol=symbol,
                        matches_required=prize_data['matches'],
                        defaults={'fichas_prize': prize_data['fichas']}
                    )
                    if created:
                        count += 1
            
            messages.success(request, _('✅ {} prêmios criados automaticamente!').format(count))
            return redirect('games:slot_machine_manager')
        
        elif action == 'update_config':
            config_id = request.POST.get('config_id')
            config = get_object_or_404(SlotMachineConfig, id=config_id)
            
            # Atualizar campos manualmente para garantir que checkbox funcione
            config.name = request.POST.get('name', config.name)
            config.cost_per_spin = int(request.POST.get('cost_per_spin', config.cost_per_spin))
            config.jackpot_amount = int(request.POST.get('jackpot_amount', config.jackpot_amount))
            config.jackpot_chance = float(request.POST.get('jackpot_chance', config.jackpot_chance))
            config.is_active = request.POST.get('is_active') == 'on'  # Checkbox
            config.save()
            
            messages.success(request, _('Configuração atualizada com sucesso!'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'add_symbol':
            form = SlotMachineSymbolForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('Símbolo adicionado com sucesso!'))
            else:
                messages.error(request, _('Erro ao adicionar símbolo.'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'edit_symbol':
            symbol_id = request.POST.get('symbol_id')
            symbol = get_object_or_404(SlotMachineSymbol, id=symbol_id)
            form = SlotMachineSymbolForm(request.POST, instance=symbol)
            if form.is_valid():
                form.save()
                messages.success(request, _('Símbolo atualizado com sucesso!'))
            else:
                messages.error(request, _('Erro ao atualizar símbolo.'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'delete_symbol':
            symbol_id = request.POST.get('symbol_id')
            symbol = get_object_or_404(SlotMachineSymbol, id=symbol_id)
            symbol.delete()
            messages.success(request, _('Símbolo removido com sucesso!'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'add_prize':
            config_id = request.POST.get('config_id')
            config = get_object_or_404(SlotMachineConfig, id=config_id)
            form = SlotMachinePrizeForm(request.POST)
            if form.is_valid():
                prize = form.save(commit=False)
                prize.config = config
                prize.save()
                messages.success(request, _('Prêmio adicionado com sucesso!'))
            else:
                messages.error(request, _('Erro ao adicionar prêmio.'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'edit_prize':
            prize_id = request.POST.get('prize_id')
            prize = get_object_or_404(SlotMachinePrize, id=prize_id)
            form = SlotMachinePrizeForm(request.POST, instance=prize)
            if form.is_valid():
                form.save()
                messages.success(request, _('Prêmio atualizado com sucesso!'))
            else:
                messages.error(request, _('Erro ao atualizar prêmio.'))
            return redirect('games:slot_machine_manager')
        
        elif action == 'delete_prize':
            prize_id = request.POST.get('prize_id')
            prize = get_object_or_404(SlotMachinePrize, id=prize_id)
            prize.delete()
            messages.success(request, _('Prêmio removido com sucesso!'))
            return redirect('games:slot_machine_manager')
    
    # Configurações
    configs = SlotMachineConfig.objects.all()
    active_config = configs.filter(is_active=True).first()
    
    # Formulários
    config_form = SlotMachineConfigForm(instance=active_config) if active_config else None
    symbol_form = SlotMachineSymbolForm()
    prize_form = SlotMachinePrizeForm()
    
    # Símbolos
    symbols = SlotMachineSymbol.objects.all().order_by('symbol')
    total_symbols = symbols.count()
    
    # Prêmios
    prizes = SlotMachinePrize.objects.all().select_related('symbol', 'config', 'item')
    total_prizes = prizes.count()
    
    # Items disponíveis
    items = Item.objects.filter(can_be_populated=True).order_by('name')
    
    # Estatísticas
    from django.db.models import Q
    total_spins = SlotMachineHistory.objects.count()
    total_jackpots = SlotMachineHistory.objects.filter(is_jackpot=True).count()
    total_wins = SlotMachineHistory.objects.filter(prize_won__isnull=False).count()
    total_fichas_distributed = SlotMachineHistory.objects.aggregate(
        total=Sum('fichas_won')
    )['total'] or 0
    
    # Últimas jogadas
    recent_plays = SlotMachineHistory.objects.select_related(
        'user', 'config', 'prize_won'
    ).order_by('-created_at')[:20]
    
    # Top ganhadores
    top_winners = SlotMachineHistory.objects.values(
        'user__username'
    ).annotate(
        total_won=Sum('fichas_won'),
        total_plays=Count('id')
    ).order_by('-total_won')[:10]
    
    context = {
        'configs': configs,
        'active_config': active_config,
        'config_form': config_form,
        'symbol_form': symbol_form,
        'prize_form': prize_form,
        'symbols': symbols,
        'total_symbols': total_symbols,
        'prizes': prizes,
        'total_prizes': total_prizes,
        'items': items,
        'total_spins': total_spins,
        'total_jackpots': total_jackpots,
        'total_wins': total_wins,
        'total_fichas_distributed': total_fichas_distributed,
        'recent_plays': recent_plays,
        'top_winners': top_winners,
        'win_rate': round((total_wins / total_spins * 100) if total_spins > 0 else 0, 2),
    }
    
    return render(request, 'slot_machine/manager/dashboard.html', context)

