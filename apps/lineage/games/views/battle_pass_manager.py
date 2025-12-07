from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse

from ..models import (
    BattlePassSeason, BattlePassLevel, BattlePassReward, 
    BattlePassItemExchange, UserBattlePassProgress
)


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def dashboard(request):
    """Dashboard de gerenciamento do Battle Pass (Base de Batalha)"""
    
    # Obter temporada ativa ou a mais recente
    active_season = BattlePassSeason.objects.filter(is_active=True).first()
    season = active_season or BattlePassSeason.objects.order_by('-created_at').first()
    
    # Estatísticas gerais
    total_seasons = BattlePassSeason.objects.count()
    total_levels = BattlePassLevel.objects.filter(season=season).count() if season else 0
    total_rewards = BattlePassReward.objects.filter(level__season=season).count() if season else 0
    total_progress = UserBattlePassProgress.objects.filter(season=season).count() if season else 0
    total_exchanges = BattlePassItemExchange.objects.filter(is_active=True).count()
    
    context = {
        'season': season,
        'active_season': active_season,
        'total_seasons': total_seasons,
        'total_levels': total_levels,
        'total_rewards': total_rewards,
        'total_progress': total_progress,
        'total_exchanges': total_exchanges,
    }
    
    return render(request, 'battle_pass/manager/dashboard.html', context)


@staff_required
def season_list(request):
    """Lista todas as temporadas"""
    seasons = BattlePassSeason.objects.annotate(
        levels_count=Count('battlepasslevel'),
        rewards_count=Count('battlepasslevel__battlepassreward'),
        users_count=Count('userbattlepassprogress')
    ).order_by('-created_at')
    
    context = {
        'seasons': seasons,
    }
    return render(request, 'battle_pass/manager/season_list.html', context)


@staff_required
@transaction.atomic
def season_create(request):
    """Criar nova temporada"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_active = request.POST.get('is_active') == 'on'
            premium_price = request.POST.get('premium_price', 50)
            
            if not name or not start_date or not end_date:
                messages.error(request, _('Preencha todos os campos obrigatórios.'))
                return redirect('games:battle_pass_manager_season_create')
            
            season = BattlePassSeason.objects.create(
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                premium_price=int(premium_price) if premium_price else 50
            )
            
            messages.success(request, _('Temporada criada com sucesso!'))
            return redirect('games:battle_pass_manager_season_detail', season_id=season.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao criar temporada: {}').format(str(e)))
    
    return render(request, 'battle_pass/manager/season_create.html')


@staff_required
@transaction.atomic
def season_edit(request, season_id):
    """Editar temporada existente"""
    season = get_object_or_404(BattlePassSeason, id=season_id)
    
    if request.method == 'POST':
        try:
            season.name = request.POST.get('name', season.name)
            season.start_date = request.POST.get('start_date', season.start_date)
            season.end_date = request.POST.get('end_date', season.end_date)
            season.is_active = request.POST.get('is_active') == 'on'
            premium_price = request.POST.get('premium_price')
            if premium_price:
                season.premium_price = int(premium_price)
            season.save()
            
            messages.success(request, _('Temporada atualizada com sucesso!'))
            return redirect('games:battle_pass_manager_season_detail', season_id=season.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar temporada: {}').format(str(e)))
    
    context = {
        'season': season,
    }
    return render(request, 'battle_pass/manager/season_edit.html', context)


@staff_required
def season_detail(request, season_id):
    """Detalhes da temporada com níveis e recompensas"""
    season = get_object_or_404(
        BattlePassSeason.objects.prefetch_related(
            Prefetch(
                'battlepasslevel_set',
                queryset=BattlePassLevel.objects.prefetch_related(
                    Prefetch(
                        'battlepassreward_set',
                        queryset=BattlePassReward.objects.all()
                    )
                ).order_by('level')
            )
        ),
        id=season_id
    )
    
    levels = season.battlepasslevel_set.all()
    total_users = UserBattlePassProgress.objects.filter(season=season).count()
    
    context = {
        'season': season,
        'levels': levels,
        'total_users': total_users,
    }
    return render(request, 'battle_pass/manager/season_detail.html', context)


@staff_required
@transaction.atomic
def season_delete(request, season_id):
    """Deletar temporada"""
    season = get_object_or_404(BattlePassSeason, id=season_id)
    
    if request.method == 'POST':
        season_name = season.name
        season.delete()
        messages.success(request, _('Temporada "{}" deletada com sucesso!').format(season_name))
        return redirect('games:battle_pass_manager_season_list')
    
    context = {
        'season': season,
    }
    return render(request, 'battle_pass/manager/season_delete.html', context)


@staff_required
@transaction.atomic
def level_create(request, season_id):
    """Criar novo nível para uma temporada"""
    season = get_object_or_404(BattlePassSeason, id=season_id)
    
    if request.method == 'POST':
        try:
            level = int(request.POST.get('level'))
            required_xp = int(request.POST.get('required_xp'))
            
            if BattlePassLevel.objects.filter(season=season, level=level).exists():
                messages.error(request, _('Já existe um nível {} para esta temporada.').format(level))
                return redirect('games:battle_pass_manager_level_create', season_id=season_id)
            
            bp_level = BattlePassLevel.objects.create(
                season=season,
                level=level,
                required_xp=required_xp
            )
            
            messages.success(request, _('Nível {} criado com sucesso!').format(level))
            return redirect('games:battle_pass_manager_season_detail', season_id=season_id)
            
        except Exception as e:
            messages.error(request, _('Erro ao criar nível: {}').format(str(e)))
    
    context = {
        'season': season,
    }
    return render(request, 'battle_pass/manager/level_create.html', context)


@staff_required
@transaction.atomic
def level_edit(request, level_id):
    """Editar nível existente"""
    bp_level = get_object_or_404(BattlePassLevel, id=level_id)
    
    if request.method == 'POST':
        try:
            bp_level.level = int(request.POST.get('level', bp_level.level))
            bp_level.required_xp = int(request.POST.get('required_xp', bp_level.required_xp))
            bp_level.save()
            
            messages.success(request, _('Nível atualizado com sucesso!'))
            return redirect('games:battle_pass_manager_season_detail', season_id=bp_level.season.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar nível: {}').format(str(e)))
    
    context = {
        'level': bp_level,
        'season': bp_level.season,
    }
    return render(request, 'battle_pass/manager/level_edit.html', context)


@staff_required
@transaction.atomic
def level_delete(request, level_id):
    """Deletar nível"""
    bp_level = get_object_or_404(BattlePassLevel, id=level_id)
    season_id = bp_level.season.id
    
    if request.method == 'POST':
        level_number = bp_level.level
        bp_level.delete()
        messages.success(request, _('Nível {} deletado com sucesso!').format(level_number))
        return redirect('games:battle_pass_manager_season_detail', season_id=season_id)
    
    context = {
        'level': bp_level,
        'season': bp_level.season,
    }
    return render(request, 'battle_pass/manager/level_delete.html', context)


@staff_required
@transaction.atomic
def reward_create(request, level_id):
    """Criar nova recompensa para um nível"""
    bp_level = get_object_or_404(BattlePassLevel, id=level_id)
    
    if request.method == 'POST':
        try:
            description = request.POST.get('description')
            is_premium = request.POST.get('is_premium') == 'on'
            item_id = request.POST.get('item_id')
            item_name = request.POST.get('item_name')
            item_enchant = request.POST.get('item_enchant', 0)
            item_amount = request.POST.get('item_amount', 1)
            
            if not description:
                messages.error(request, _('Descrição é obrigatória.'))
                return redirect('games:battle_pass_manager_reward_create', level_id=level_id)
            
            BattlePassReward.objects.create(
                level=bp_level,
                description=description,
                is_premium=is_premium,
                item_id=int(item_id) if item_id else None,
                item_name=item_name if item_name else None,
                item_enchant=int(item_enchant) if item_enchant else 0,
                item_amount=int(item_amount) if item_amount else 1
            )
            
            messages.success(request, _('Recompensa criada com sucesso!'))
            return redirect('games:battle_pass_manager_season_detail', season_id=bp_level.season.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao criar recompensa: {}').format(str(e)))
    
    context = {
        'level': bp_level,
        'season': bp_level.season,
    }
    return render(request, 'battle_pass/manager/reward_create.html', context)


@staff_required
@transaction.atomic
def reward_edit(request, reward_id):
    """Editar recompensa existente"""
    reward = get_object_or_404(BattlePassReward, id=reward_id)
    
    if request.method == 'POST':
        try:
            reward.description = request.POST.get('description', reward.description)
            reward.is_premium = request.POST.get('is_premium') == 'on'
            item_id = request.POST.get('item_id')
            reward.item_id = int(item_id) if item_id else None
            reward.item_name = request.POST.get('item_name', reward.item_name)
            reward.item_enchant = int(request.POST.get('item_enchant', 0))
            reward.item_amount = int(request.POST.get('item_amount', 1))
            reward.save()
            
            messages.success(request, _('Recompensa atualizada com sucesso!'))
            return redirect('games:battle_pass_manager_season_detail', season_id=reward.level.season.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar recompensa: {}').format(str(e)))
    
    context = {
        'reward': reward,
        'level': reward.level,
        'season': reward.level.season,
    }
    return render(request, 'battle_pass/manager/reward_edit.html', context)


@staff_required
@transaction.atomic
def reward_delete(request, reward_id):
    """Deletar recompensa"""
    reward = get_object_or_404(BattlePassReward, id=reward_id)
    season_id = reward.level.season.id
    
    if request.method == 'POST':
        reward_desc = reward.description
        reward.delete()
        messages.success(request, _('Recompensa "{}" deletada com sucesso!').format(reward_desc))
        return redirect('games:battle_pass_manager_season_detail', season_id=season_id)
    
    context = {
        'reward': reward,
        'level': reward.level,
        'season': reward.level.season,
    }
    return render(request, 'battle_pass/manager/reward_delete.html', context)


@staff_required
def exchange_list(request):
    """Lista de trocas de itens por XP"""
    exchanges = BattlePassItemExchange.objects.all().order_by('-created_at')
    
    context = {
        'exchanges': exchanges,
    }
    return render(request, 'battle_pass/manager/exchange_list.html', context)


@staff_required
@transaction.atomic
def exchange_create(request):
    """Criar nova troca de item por XP"""
    if request.method == 'POST':
        try:
            item_id = request.POST.get('item_id')
            item_name = request.POST.get('item_name')
            item_enchant = request.POST.get('item_enchant', 0)
            xp_amount = request.POST.get('xp_amount')
            is_active = request.POST.get('is_active') == 'on'
            max_exchanges = request.POST.get('max_exchanges', 0)
            
            if not item_id or not item_name or not xp_amount:
                messages.error(request, _('Preencha todos os campos obrigatórios.'))
                return redirect('games:battle_pass_manager_exchange_create')
            
            BattlePassItemExchange.objects.create(
                item_id=int(item_id),
                item_name=item_name,
                item_enchant=int(item_enchant) if item_enchant else 0,
                xp_amount=int(xp_amount),
                is_active=is_active,
                max_exchanges=int(max_exchanges) if max_exchanges else 0
            )
            
            messages.success(request, _('Troca criada com sucesso!'))
            return redirect('games:battle_pass_manager_exchange_list')
            
        except Exception as e:
            messages.error(request, _('Erro ao criar troca: {}').format(str(e)))
    
    return render(request, 'battle_pass/manager/exchange_create.html')


@staff_required
@transaction.atomic
def exchange_edit(request, exchange_id):
    """Editar troca existente"""
    exchange = get_object_or_404(BattlePassItemExchange, id=exchange_id)
    
    if request.method == 'POST':
        try:
            exchange.item_id = int(request.POST.get('item_id', exchange.item_id))
            exchange.item_name = request.POST.get('item_name', exchange.item_name)
            exchange.item_enchant = int(request.POST.get('item_enchant', 0))
            exchange.xp_amount = int(request.POST.get('xp_amount', exchange.xp_amount))
            exchange.is_active = request.POST.get('is_active') == 'on'
            max_exchanges = request.POST.get('max_exchanges')
            if max_exchanges:
                exchange.max_exchanges = int(max_exchanges)
            exchange.save()
            
            messages.success(request, _('Troca atualizada com sucesso!'))
            return redirect('games:battle_pass_manager_exchange_list')
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar troca: {}').format(str(e)))
    
    context = {
        'exchange': exchange,
    }
    return render(request, 'battle_pass/manager/exchange_edit.html', context)


@staff_required
@transaction.atomic
def exchange_delete(request, exchange_id):
    """Deletar troca"""
    exchange = get_object_or_404(BattlePassItemExchange, id=exchange_id)
    
    if request.method == 'POST':
        exchange_name = exchange.item_name
        exchange.delete()
        messages.success(request, _('Troca "{}" deletada com sucesso!').format(exchange_name))
        return redirect('games:battle_pass_manager_exchange_list')
    
    context = {
        'exchange': exchange,
    }
    return render(request, 'battle_pass/manager/exchange_delete.html', context)

