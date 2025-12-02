from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _
from django.db.models import Count, Sum, Avg, Max, Q
from django.contrib import messages

from ..models import (
    FishingRod, Fish, FishingHistory, FishingBait, UserFishingBait, Item
)
from ..forms import FishForm, FishingBaitForm


@staff_member_required
def dashboard(request):
    """Dashboard de gerenciamento do Fishing Game"""
    
    # Processar formulários
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'quick_setup':
            # Setup completo: peixes + iscas
            # 1. Popular peixes
            fishes_data = [
                {'name': 'Peixinho', 'rarity': 'common', 'icon': '🐟', 'min_level': 1, 'weight': 50, 'xp': 10, 'fichas': 5},
                {'name': 'Sardinha', 'rarity': 'common', 'icon': '🐠', 'min_level': 1, 'weight': 45, 'xp': 12, 'fichas': 6},
                {'name': 'Carpa', 'rarity': 'common', 'icon': '🐡', 'min_level': 1, 'weight': 40, 'xp': 15, 'fichas': 8},
                {'name': 'Atum', 'rarity': 'rare', 'icon': '🐟', 'min_level': 3, 'weight': 25, 'xp': 30, 'fichas': 20},
                {'name': 'Salmão', 'rarity': 'rare', 'icon': '🐠', 'min_level': 3, 'weight': 20, 'xp': 35, 'fichas': 25},
                {'name': 'Dourado', 'rarity': 'rare', 'icon': '🐡', 'min_level': 3, 'weight': 18, 'xp': 40, 'fichas': 30},
                {'name': 'Tubarão', 'rarity': 'epic', 'icon': '🦈', 'min_level': 5, 'weight': 10, 'xp': 80, 'fichas': 50},
                {'name': 'Golfinho', 'rarity': 'epic', 'icon': '🐬', 'min_level': 5, 'weight': 8, 'xp': 90, 'fichas': 60},
                {'name': 'Baleia', 'rarity': 'epic', 'icon': '🐋', 'min_level': 5, 'weight': 6, 'xp': 100, 'fichas': 70},
                {'name': 'Dragão Marinho', 'rarity': 'legendary', 'icon': '🐉', 'min_level': 7, 'weight': 3, 'xp': 200, 'fichas': 150},
                {'name': 'Kraken Bebê', 'rarity': 'legendary', 'icon': '🦑', 'min_level': 7, 'weight': 2, 'xp': 250, 'fichas': 200},
                {'name': 'Sereia Dourada', 'rarity': 'legendary', 'icon': '🧜', 'min_level': 10, 'weight': 1, 'xp': 500, 'fichas': 500},
            ]
            
            fish_count = 0
            for fish_data in fishes_data:
                fish, created = Fish.objects.get_or_create(
                    name=fish_data['name'],
                    defaults={
                        'rarity': fish_data['rarity'],
                        'icon': fish_data['icon'],
                        'min_rod_level': fish_data['min_level'],
                        'weight': fish_data['weight'],
                        'experience_reward': fish_data['xp'],
                        'fichas_reward': fish_data['fichas']
                    }
                )
                if created:
                    fish_count += 1
            
            # 2. Popular iscas
            baits_data = [
                {'name': 'Isca Comum', 'description': 'Aumenta a chance de pegar peixes comuns', 'price': 20, 'rarity_boost': 'common', 'boost_percentage': 50.0, 'duration_minutes': 30},
                {'name': 'Isca Rara', 'description': 'Aumenta a chance de pegar peixes raros', 'price': 50, 'rarity_boost': 'rare', 'boost_percentage': 50.0, 'duration_minutes': 30},
                {'name': 'Isca Épica', 'description': 'Aumenta a chance de pegar peixes épicos', 'price': 100, 'rarity_boost': 'epic', 'boost_percentage': 50.0, 'duration_minutes': 30},
                {'name': 'Isca Lendária', 'description': 'Aumenta a chance de pegar peixes lendários', 'price': 200, 'rarity_boost': 'legendary', 'boost_percentage': 50.0, 'duration_minutes': 60},
            ]
            
            baits_count = 0
            for bait_data in baits_data:
                bait, created = FishingBait.objects.get_or_create(
                    name=bait_data['name'],
                    defaults=bait_data
                )
                if created:
                    baits_count += 1
            
            messages.success(request, _('✅ Setup completo! Criados: {} peixes, {} iscas!').format(fish_count, baits_count))
            return redirect('games:fishing_game_manager')
        
        elif action == 'auto_populate_fish':
            # Popular peixes automaticamente
            fishes_data = [
                # Peixes Comuns (Level 1+)
                {'name': 'Peixinho', 'rarity': 'common', 'icon': '🐟', 'min_level': 1, 'weight': 50, 'xp': 10, 'fichas': 5},
                {'name': 'Sardinha', 'rarity': 'common', 'icon': '🐠', 'min_level': 1, 'weight': 45, 'xp': 12, 'fichas': 6},
                {'name': 'Carpa', 'rarity': 'common', 'icon': '🐡', 'min_level': 1, 'weight': 40, 'xp': 15, 'fichas': 8},
                # Peixes Raros (Level 3+)
                {'name': 'Atum', 'rarity': 'rare', 'icon': '🐟', 'min_level': 3, 'weight': 25, 'xp': 30, 'fichas': 20},
                {'name': 'Salmão', 'rarity': 'rare', 'icon': '🐠', 'min_level': 3, 'weight': 20, 'xp': 35, 'fichas': 25},
                {'name': 'Dourado', 'rarity': 'rare', 'icon': '🐡', 'min_level': 3, 'weight': 18, 'xp': 40, 'fichas': 30},
                # Peixes Épicos (Level 5+)
                {'name': 'Tubarão', 'rarity': 'epic', 'icon': '🦈', 'min_level': 5, 'weight': 10, 'xp': 80, 'fichas': 50},
                {'name': 'Golfinho', 'rarity': 'epic', 'icon': '🐬', 'min_level': 5, 'weight': 8, 'xp': 90, 'fichas': 60},
                {'name': 'Baleia', 'rarity': 'epic', 'icon': '🐋', 'min_level': 5, 'weight': 6, 'xp': 100, 'fichas': 70},
                # Peixes Lendários (Level 7+)
                {'name': 'Dragão Marinho', 'rarity': 'legendary', 'icon': '🐉', 'min_level': 7, 'weight': 3, 'xp': 200, 'fichas': 150},
                {'name': 'Kraken Bebê', 'rarity': 'legendary', 'icon': '🦑', 'min_level': 7, 'weight': 2, 'xp': 250, 'fichas': 200},
                {'name': 'Sereia Dourada', 'rarity': 'legendary', 'icon': '🧜', 'min_level': 10, 'weight': 1, 'xp': 500, 'fichas': 500},
            ]
            
            count = 0
            for fish_data in fishes_data:
                fish, created = Fish.objects.get_or_create(
                    name=fish_data['name'],
                    defaults={
                        'rarity': fish_data['rarity'],
                        'icon': fish_data['icon'],
                        'min_rod_level': fish_data['min_level'],
                        'weight': fish_data['weight'],
                        'experience_reward': fish_data['xp'],
                        'fichas_reward': fish_data['fichas']
                    }
                )
                if created:
                    count += 1
            
            messages.success(request, _('✅ {} peixes criados automaticamente!').format(count))
            return redirect('games:fishing_game_manager')
        
        elif action == 'auto_populate_baits':
            # Popular iscas automaticamente
            baits_data = [
                {'name': 'Isca Comum', 'description': 'Aumenta a chance de pegar peixes comuns', 'price': 20, 'rarity_boost': 'common', 'boost_percentage': 50.0, 'duration_minutes': 30},
                {'name': 'Isca Rara', 'description': 'Aumenta a chance de pegar peixes raros', 'price': 50, 'rarity_boost': 'rare', 'boost_percentage': 50.0, 'duration_minutes': 30},
                {'name': 'Isca Épica', 'description': 'Aumenta a chance de pegar peixes épicos', 'price': 100, 'rarity_boost': 'epic', 'boost_percentage': 50.0, 'duration_minutes': 30},
                {'name': 'Isca Lendária', 'description': 'Aumenta a chance de pegar peixes lendários', 'price': 200, 'rarity_boost': 'legendary', 'boost_percentage': 50.0, 'duration_minutes': 60},
            ]
            
            count = 0
            for bait_data in baits_data:
                bait, created = FishingBait.objects.get_or_create(
                    name=bait_data['name'],
                    defaults=bait_data
                )
                if created:
                    count += 1
            
            messages.success(request, _('✅ {} iscas criadas automaticamente!').format(count))
            return redirect('games:fishing_game_manager')
        
        elif action == 'add_fish':
            form = FishForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, _('Peixe adicionado com sucesso!'))
            else:
                messages.error(request, _('Erro ao adicionar peixe.'))
            return redirect('games:fishing_game_manager')
        
        elif action == 'delete_fish':
            fish_id = request.POST.get('fish_id')
            fish = get_object_or_404(Fish, id=fish_id)
            fish.delete()
            messages.success(request, _('Peixe removido com sucesso!'))
            return redirect('games:fishing_game_manager')
        
        elif action == 'add_bait':
            form = FishingBaitForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('Isca adicionada com sucesso!'))
            else:
                messages.error(request, _('Erro ao adicionar isca.'))
            return redirect('games:fishing_game_manager')
        
        elif action == 'delete_bait':
            bait_id = request.POST.get('bait_id')
            bait = get_object_or_404(FishingBait, id=bait_id)
            bait.delete()
            messages.success(request, _('Isca removida com sucesso!'))
            return redirect('games:fishing_game_manager')
    
    # Formulários
    fish_form = FishForm()
    bait_form = FishingBaitForm()
    
    # Items disponíveis
    items = Item.objects.filter(can_be_populated=True).order_by('name')
    
    # Estatísticas de Peixes
    total_fish = Fish.objects.count()
    fish_by_rarity = Fish.objects.values('rarity').annotate(
        count=Count('id')
    ).order_by('rarity')
    
    # Estatísticas de Varas
    total_rods = FishingRod.objects.count()
    avg_rod_level = FishingRod.objects.aggregate(avg=Avg('level'))['avg'] or 0
    max_rod_level = FishingRod.objects.aggregate(max=Max('level'))['max'] or 0
    
    # Top pescadores por nível
    top_anglers = FishingRod.objects.select_related('user').order_by(
        '-level', '-experience'
    )[:10]
    
    # Estatísticas de Pescarias
    total_catches = FishingHistory.objects.count()
    successful_catches = FishingHistory.objects.filter(success=True).count()
    success_rate = round((successful_catches / total_catches * 100) if total_catches > 0 else 0, 2)
    
    # Capturas por raridade
    catches_by_rarity = FishingHistory.objects.filter(
        success=True
    ).values('fish__rarity').annotate(
        count=Count('id')
    ).order_by('fish__rarity')
    
    # Peixes mais capturados
    most_caught_fish = FishingHistory.objects.filter(
        success=True
    ).values('fish__name', 'fish__icon', 'fish__rarity').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Peixes menos capturados (mais raros)
    least_caught_fish = FishingHistory.objects.filter(
        success=True
    ).values('fish__name', 'fish__icon', 'fish__rarity').annotate(
        count=Count('id')
    ).order_by('count')[:10]
    
    # Top pescadores de peixes lendários
    top_legendary_hunters = FishingHistory.objects.filter(
        fish__rarity='legendary',
        success=True
    ).values('user__username').annotate(
        legendary_count=Count('id')
    ).order_by('-legendary_count')[:10]
    
    # Últimas pescarias
    recent_catches = FishingHistory.objects.select_related(
        'user', 'fish'
    ).order_by('-created_at')[:20]
    
    # Estatísticas de Iscas
    total_baits = FishingBait.objects.count()
    active_baits = UserFishingBait.objects.filter(is_active=True).count()
    
    # Iscas mais usadas
    most_used_baits = UserFishingBait.objects.values(
        'bait__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Distribuição de níveis de vara
    rod_level_distribution = []
    for level in range(1, max_rod_level + 1 if max_rod_level > 0 else 11):
        count = FishingRod.objects.filter(level=level).count()
        rod_level_distribution.append({
            'level': level,
            'count': count,
            'percentage': round((count / total_rods * 100) if total_rods > 0 else 0, 2)
        })
    
    # Todos os peixes e iscas
    all_fish = Fish.objects.all().order_by('rarity', 'name')
    all_baits = FishingBait.objects.all().order_by('name')
    
    context = {
        'fish_form': fish_form,
        'bait_form': bait_form,
        'items': items,
        'all_fish': all_fish,
        'all_baits': all_baits,
        'total_fish': total_fish,
        'fish_by_rarity': fish_by_rarity,
        'total_rods': total_rods,
        'avg_rod_level': round(avg_rod_level, 2),
        'max_rod_level': max_rod_level,
        'top_anglers': top_anglers,
        'total_catches': total_catches,
        'successful_catches': successful_catches,
        'success_rate': success_rate,
        'catches_by_rarity': catches_by_rarity,
        'most_caught_fish': most_caught_fish,
        'least_caught_fish': least_caught_fish,
        'top_legendary_hunters': top_legendary_hunters,
        'recent_catches': recent_catches,
        'total_baits': total_baits,
        'active_baits': active_baits,
        'most_used_baits': most_used_baits,
        'rod_level_distribution': rod_level_distribution,
    }
    
    return render(request, 'fishing_game/manager/dashboard.html', context)

