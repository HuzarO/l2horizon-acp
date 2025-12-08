from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils.translation import gettext as _
from django.utils import timezone
from apps.main.home.decorator import conditional_otp_required
import random
from datetime import timedelta

from ..models import (
    FishingGameConfig, FishingRod, Fish, FishingHistory, FishingBait,
    UserFishingBait, Bag, BagItem
)


@conditional_otp_required
def fishing_game_page(request):
    """Página principal do Fishing Game"""
    config = FishingGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        messages.error(request, _("Fishing Game não está disponível no momento."))
        return redirect('dashboard')
    
    # Criar vara de pesca se não existir
    rod, created = FishingRod.objects.get_or_create(user=request.user)
    
    # Todos os peixes (marcando quais estão disponíveis)
    all_fish = Fish.objects.all().order_by('min_rod_level', 'rarity')
    available_fish = []
    locked_fish = []
    
    for fish in all_fish:
        if fish.min_rod_level <= rod.level:
            available_fish.append(fish)
        else:
            locked_fish.append(fish)
    
    # Iscas disponíveis para compra
    available_baits = FishingBait.objects.all()
    
    # Iscas ativas do usuário
    active_baits = UserFishingBait.objects.filter(
        user=request.user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).select_related('bait')
    
    # Histórico de pescarias
    fishing_history = FishingHistory.objects.filter(
        user=request.user
    ).select_related('fish').order_by('-created_at')[:10]
    
    # Estatísticas
    from django.db.models import Count, Q
    stats = FishingHistory.objects.filter(user=request.user).aggregate(
        total_catches=Count('id'),
        successful_catches=Count('id', filter=Q(success=True)),
        common_fish=Count('id', filter=Q(fish__rarity='common')),
        rare_fish=Count('id', filter=Q(fish__rarity='rare')),
        epic_fish=Count('id', filter=Q(fish__rarity='epic')),
        legendary_fish=Count('id', filter=Q(fish__rarity='legendary'))
    )
    
    # XP necessária para próximo nível
    xp_for_next_level = rod.level * 100
    xp_percentage = (rod.experience / xp_for_next_level * 100) if xp_for_next_level > 0 else 0
    
    context = {
        'config': config,
        'rod': rod,
        'available_fish': available_fish,
        'locked_fish': locked_fish,
        'available_baits': available_baits,
        'active_baits': active_baits,
        'fishing_history': fishing_history,
        'stats': stats,
        'user_fichas': request.user.fichas,
        'xp_for_next_level': xp_for_next_level,
        'xp_percentage': round(xp_percentage, 2),
    }
    
    return render(request, 'fishing_game/fishing_game.html', context)


@conditional_otp_required
@transaction.atomic
def fishing_game_cast(request):
    """Lançar linha e tentar pescar"""
    if request.method != 'POST':
        return JsonResponse({'error': _('Método inválido')}, status=400)
    
    config = FishingGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        return JsonResponse({'error': _('Fishing Game não disponível')}, status=400)
    
    user = request.user
    if user.fichas < config.cost_per_cast:
        return JsonResponse({
            'error': _('Você não tem fichas suficientes. Necessário: {} ficha(s)').format(config.cost_per_cast)
        }, status=400)
    
    # Deduzir ficha
    user.fichas -= config.cost_per_cast
    user.save(update_fields=['fichas'])
    
    # Pegar vara do usuário
    rod = FishingRod.objects.get(user=user)
    
    # Peixes disponíveis para o nível da vara
    available_fish = list(Fish.objects.filter(min_rod_level__lte=rod.level))
    
    if not available_fish:
        return JsonResponse({
            'error': _('Nenhum peixe disponível para seu nível de vara')
        }, status=400)
    
    # Verificar iscas ativas
    active_baits = UserFishingBait.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).select_related('bait')
    
    # Ajustar pesos baseado nas iscas
    fish_weights = []
    for fish in available_fish:
        base_weight = fish.weight
        
        # Aplicar bônus de iscas
        for user_bait in active_baits:
            if fish.rarity == user_bait.bait.rarity_boost:
                base_weight *= (1 + user_bait.bait.boost_percentage / 100)
        
        fish_weights.append(base_weight)
    
    # Selecionar peixe baseado nos pesos
    caught_fish = random.choices(available_fish, weights=fish_weights, k=1)[0]
    
    # Chance de sucesso baseada na raridade e nível da vara
    success_chances = {
        'common': 90,
        'rare': 70,
        'epic': 50,
        'legendary': 30
    }
    
    base_success = success_chances.get(caught_fish.rarity, 70)
    # Aumentar chance com nível da vara (1% por nível)
    success_rate = min(95, base_success + rod.level)
    
    # Determinar sucesso
    success = random.random() < (success_rate / 100)
    
    # Adicionar experiência (menos se falhar)
    xp_gained = caught_fish.experience_reward if success else int(caught_fish.experience_reward * 0.3)
    rod.add_experience(xp_gained)
    
    # Se sucesso, adicionar recompensas
    fichas_won = 0
    item_won = None
    
    if success:
        fichas_won = caught_fish.fichas_reward
        
        if fichas_won > 0:
            user.fichas += fichas_won
            user.save(update_fields=['fichas'])
        
        # Adicionar item à bag se tiver
        if caught_fish.item_reward:
            item_won = caught_fish.item_reward
            bag, bag_created = Bag.objects.get_or_create(user=user)
            bag_item, created = BagItem.objects.get_or_create(
                bag=bag,
                item_id=caught_fish.item_reward.item_id,
                enchant=caught_fish.item_reward.enchant,
                defaults={
                    'item_name': caught_fish.item_reward.name,
                    'quantity': 1,
                }
            )
            if not created:
                bag_item.quantity += 1
                bag_item.save()
    
    # Salvar histórico
    history = FishingHistory.objects.create(
        user=user,
        fish=caught_fish,
        rod_level=rod.level,
        success=success
    )
    
    # Atualizar progresso de quests relacionadas à pescaria (verificar nível da vara)
    try:
        from apps.lineage.games.services.quest_progress_tracker import check_and_update_all_quests
        check_and_update_all_quests(user)
    except Exception as e:
        # Não falhar se houver erro no tracking
        pass
    
    response_data = {
        'success': success,
        'fish': {
            'name': caught_fish.name,
            'icon': caught_fish.icon,
            'image_url': caught_fish.get_display_image(),
            'rarity': caught_fish.rarity,
            'rarity_display': caught_fish.get_rarity_display()
        },
        'xp_gained': xp_gained,
        'fichas_won': fichas_won,
        'item_won': {
            'name': item_won.name,
            'enchant': item_won.enchant,
            'rarity': item_won.rarity
        } if item_won else None,
        'rod_level': rod.level,
        'rod_experience': rod.experience,
        'user_fichas': user.fichas,
        'message': _('Você pescou {}!').format(caught_fish.name) if success else _('O peixe escapou!')
    }
    
    return JsonResponse(response_data)


@conditional_otp_required
@transaction.atomic
def fishing_buy_bait(request):
    """Comprar isca especial"""
    if request.method != 'POST':
        return JsonResponse({'error': _('Método inválido')}, status=400)
    
    config = FishingGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        return JsonResponse({'error': _('Fishing Game não disponível')}, status=400)
    
    try:
        bait_id = int(request.POST.get('bait_id'))
    except (ValueError, TypeError):
        return JsonResponse({'error': _('ID de isca inválido')}, status=400)
    
    bait = FishingBait.objects.filter(id=bait_id).first()
    
    if not bait:
        return JsonResponse({'error': _('Isca não encontrada')}, status=400)
    
    user = request.user
    
    # Verificar fichas
    if user.fichas < bait.price:
        return JsonResponse({
            'error': _('Você não tem fichas suficientes. Necessário: {}').format(bait.price)
        }, status=400)
    
    # Deduzir fichas
    user.fichas -= bait.price
    user.save(update_fields=['fichas'])
    
    # Ativar isca
    now = timezone.now()
    expires_at = now + timedelta(minutes=bait.duration_minutes)
    
    user_bait = UserFishingBait.objects.create(
        user=user,
        bait=bait,
        activated_at=now,
        expires_at=expires_at,
        is_active=True
    )
    
    return JsonResponse({
        'success': True,
        'message': _('Isca {} ativada por {} minutos!').format(bait.name, bait.duration_minutes),
        'user_fichas': user.fichas,
        'bait': {
            'name': bait.name,
            'expires_at': expires_at.isoformat()
        }
    })


@conditional_otp_required
def fishing_leaderboard(request):
    """Leaderboard do Fishing Game"""
    config = FishingGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        messages.error(request, _("Fishing Game não está disponível no momento."))
        return redirect('dashboard')
    
    from django.db.models import Count, Max, Q
    
    # Top pescadores (por nível de vara)
    top_anglers = FishingRod.objects.select_related('user').order_by('-level', '-experience')[:10]
    
    # Top pescadores de peixes lendários
    top_legendary_hunters = FishingHistory.objects.filter(
        fish__rarity='legendary',
        success=True
    ).values('user__username').annotate(
        legendary_count=Count('id')
    ).order_by('-legendary_count')[:10]
    
    # Mais pescarias totais
    top_fishers = FishingHistory.objects.filter(
        success=True
    ).values('user__username').annotate(
        total_catches=Count('id'),
        rare_catches=Count('id', filter=Q(fish__rarity__in=['rare', 'epic', 'legendary']))
    ).order_by('-total_catches')[:10]
    
    context = {
        'top_anglers': top_anglers,
        'top_legendary_hunters': top_legendary_hunters,
        'top_fishers': top_fishers,
    }
    
    return render(request, 'fishing_game/leaderboard.html', context)


@conditional_otp_required
def fishing_collection(request):
    """Coleção de peixes pescados pelo usuário"""
    config = FishingGameConfig.objects.filter(is_active=True).first()
    
    if not config:
        messages.error(request, _("Fishing Game não está disponível no momento."))
        return redirect('dashboard')
    
    # Todos os peixes possíveis
    all_fish = Fish.objects.all().order_by('rarity', 'name')
    
    # Peixes que o usuário já pescou
    caught_fish_ids = FishingHistory.objects.filter(
        user=request.user,
        success=True
    ).values_list('fish_id', flat=True).distinct()
    
    # Marcar peixes capturados
    fish_collection = []
    for fish in all_fish:
        fish_collection.append({
            'fish': fish,
            'caught': fish.id in caught_fish_ids,
            'catch_count': FishingHistory.objects.filter(
                user=request.user,
                fish=fish,
                success=True
            ).count()
        })
    
    # Progresso da coleção
    total_fish = all_fish.count()
    caught_count = len(set(caught_fish_ids))
    collection_percentage = round((caught_count / total_fish * 100) if total_fish > 0 else 0, 2)
    
    context = {
        'fish_collection': fish_collection,
        'total_fish': total_fish,
        'caught_count': caught_count,
        'collection_percentage': collection_percentage,
    }
    
    return render(request, 'fishing_game/collection.html', context)

