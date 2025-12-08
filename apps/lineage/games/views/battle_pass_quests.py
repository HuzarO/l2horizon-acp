"""
Views para sistema de missões/quests do Battle Pass
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, gettext
from django.db import transaction
from apps.main.home.decorator import conditional_otp_required
from django.db import models
from ..models import (
    BattlePassQuest, BattlePassQuestProgress, UserBattlePassProgress,
    BattlePassSeason
)
from ..services.battle_pass_service import BattlePassService
from django.utils import timezone
from datetime import timedelta


@conditional_otp_required
def quests_view(request):
    """Visualização de todas as quests disponíveis"""
    season = BattlePassService.get_active_season()
    
    if not season:
        messages.error(request, _("Não há temporada ativa no momento."))
        return redirect('games:battle_pass')
    
    progress, created = UserBattlePassProgress.objects.get_or_create(
        user=request.user,
        season=season
    )
    
    # Busca todas as quests ativas
    all_quests = BattlePassQuest.objects.filter(
        is_active=True
    ).filter(
        models.Q(season=season) | models.Q(season__isnull=True)
    ).order_by('quest_type', 'order')
    
    # Agrupa por tipo
    daily_quests = []
    weekly_quests = []
    seasonal_quests = []
    special_quests = []
    
    for quest in all_quests:
        quest_progress, _ = BattlePassQuestProgress.objects.get_or_create(
            user=request.user,
            quest=quest
        )
        
        quest_data = {
            'quest': quest,
            'progress': quest_progress,
            'can_complete': False,  # Será implementado com lógica específica
        }
        
        if quest.quest_type == 'daily':
            daily_quests.append(quest_data)
        elif quest.quest_type == 'weekly':
            weekly_quests.append(quest_data)
        elif quest.quest_type == 'seasonal':
            seasonal_quests.append(quest_data)
        else:
            special_quests.append(quest_data)
    
    # Verifica se precisa resetar quests diárias/semanais
    _reset_quests_if_needed(request.user, daily_quests, weekly_quests)
    
    context = {
        'season': season,
        'progress': progress,
        'daily_quests': daily_quests,
        'weekly_quests': weekly_quests,
        'seasonal_quests': seasonal_quests,
        'special_quests': special_quests,
    }
    
    return render(request, 'battlepass/quests.html', context)


@conditional_otp_required
@transaction.atomic
def complete_quest(request, quest_id):
    """Completa uma quest e adiciona XP"""
    quest = get_object_or_404(BattlePassQuest, id=quest_id, is_active=True)
    season = BattlePassService.get_active_season()
    
    if not season:
        messages.error(request, _("Não há temporada ativa no momento."))
        return redirect('games:quests')
    
    progress, created = UserBattlePassProgress.objects.get_or_create(
        user=request.user,
        season=season
    )
    
    # Verifica se a quest é premium e se o usuário tem premium
    if quest.is_premium and not progress.has_premium:
        messages.error(request, _("Você precisa do Passe Premium para completar esta quest."))
        return redirect('games:quests')
    
    quest_progress, created = BattlePassQuestProgress.objects.get_or_create(
        user=request.user,
        quest=quest
    )
    
    if quest_progress.completed:
        messages.info(request, _("Você já completou esta quest."))
        return redirect('games:quests')
    
    # Marca como completa
    quest_progress.completed = True
    quest_progress.completed_at = timezone.now()
    quest_progress.save()
    
    # Adiciona XP
    progress.add_xp(quest.xp_reward, source='quest', auto_claim=True)
    
    # Atualiza estatísticas
    from ..models import BattlePassStatistics
    stats, _ = BattlePassStatistics.objects.get_or_create(
        user=request.user,
        season=season
    )
    stats.total_quests_completed += 1
    stats.save()
    
    # Registra no histórico
    from ..models import BattlePassHistory
    BattlePassHistory.objects.create(
        user=request.user,
        season=season,
        action_type='quest_completed',
        description=f'Completou quest: {quest.title}',
        xp_amount=quest.xp_reward,
        metadata={'quest_id': quest.id, 'quest_type': quest.quest_type}
    )
    
    messages.success(request, gettext("Quest completada! Você ganhou {} XP!").format(quest.xp_reward))
    return redirect('games:quests')


def _reset_quests_if_needed(user, daily_quests, weekly_quests):
    """Reseta quests diárias/semanais se necessário"""
    now = timezone.now()
    
    for quest_data in daily_quests:
        quest = quest_data['quest']
        quest_progress = quest_data['progress']
        
        if quest.reset_daily:
            # Verifica se passou um dia desde o último reset
            if now.date() > quest_progress.last_reset.date():
                # Reseta o progresso
                quest_progress.progress = 0
                quest_progress.completed = False
                quest_progress.completed_at = None
                quest_progress.last_reset = now
                quest_progress.save()
    
    for quest_data in weekly_quests:
        quest = quest_data['quest']
        quest_progress = quest_data['progress']
        
        if quest.reset_weekly:
            # Verifica se passou uma semana desde o último reset
            week_ago = now - timedelta(days=7)
            if quest_progress.last_reset < week_ago:
                # Reseta o progresso
                quest_progress.progress = 0
                quest_progress.completed = False
                quest_progress.completed_at = None
                quest_progress.last_reset = now
                quest_progress.save()

