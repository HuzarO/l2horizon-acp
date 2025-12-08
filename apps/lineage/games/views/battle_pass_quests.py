"""
Views para sistema de missões/quests do Battle Pass
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, gettext
from django.db import transaction
from apps.main.home.decorator import conditional_otp_required
from django.db import models
from apps.lineage.games.models import (
    BattlePassQuest, BattlePassQuestProgress, UserBattlePassProgress,
    BattlePassSeason
)
from apps.lineage.games.services.battle_pass_service import BattlePassService
from apps.lineage.games.services.quest_progress_tracker import (
    update_quest_progress, check_and_update_all_quests
)
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
        # Atualizar progresso automaticamente
        update_quest_progress(request.user, quest)
        
        # Buscar o progresso atualizado (refresh do banco para garantir dados atualizados)
        quest_progress, created = BattlePassQuestProgress.objects.get_or_create(
            user=request.user,
            quest=quest
        )
        # Recarregar do banco para garantir que temos os dados mais recentes
        quest_progress.refresh_from_db()
        
        # Verificar se pode completar (progresso >= target e não está completa)
        can_complete = (
            not quest_progress.completed and 
            quest_progress.progress >= quest.objective_target
        )
        
        # Se a quest requer um item, verificar se o usuário tem o item na bag
        has_required_item = True
        if quest.required_item_id:
            try:
                from ..models import Bag, BagItem
                bag, bag_created = Bag.objects.get_or_create(user=request.user)
                # Converter para int para garantir compatibilidade
                required_item_id = int(quest.required_item_id)
                required_enchant = int(quest.required_item_enchant) if quest.required_item_enchant else 0
                
                # Primeiro tenta buscar com o enchant específico
                bag_item = BagItem.objects.filter(
                    bag=bag,
                    item_id=required_item_id,
                    enchant=required_enchant
                ).first()
                
                # Se não encontrou e o enchant é 0, tenta buscar qualquer enchant (mais flexível)
                if not bag_item and required_enchant == 0:
                    bag_item = BagItem.objects.filter(
                        bag=bag,
                        item_id=required_item_id
                    ).first()
                
                if not bag_item:
                    has_required_item = False
                    can_complete = False
                elif bag_item.quantity < quest.required_item_amount:
                    has_required_item = False
                    can_complete = False
            except (Bag.DoesNotExist, ValueError, TypeError) as e:
                has_required_item = False
                can_complete = False
        
        # Adicionar informações sobre o item na bag para debug
        bag_item_info = None
        if quest.required_item_id:
            try:
                from ..models import Bag, BagItem
                bag, _ = Bag.objects.get_or_create(user=request.user)
                required_item_id = int(quest.required_item_id)
                required_enchant = int(quest.required_item_enchant) if quest.required_item_enchant else 0
                
                bag_item = BagItem.objects.filter(
                    bag=bag,
                    item_id=required_item_id,
                    enchant=required_enchant
                ).first()
                
                if not bag_item and required_enchant == 0:
                    bag_item = BagItem.objects.filter(
                        bag=bag,
                        item_id=required_item_id
                    ).first()
                
                if bag_item:
                    bag_item_info = {
                        'quantity': bag_item.quantity,
                        'enchant': bag_item.enchant,
                    }
            except:
                pass
        
        quest_data = {
            'quest': quest,
            'progress': quest_progress,
            'can_complete': can_complete,
            'has_required_item': has_required_item,
            'bag_item_info': bag_item_info,
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
    
    # Atualizar progresso antes de verificar
    update_quest_progress(request.user, quest)
    
    quest_progress, created = BattlePassQuestProgress.objects.get_or_create(
        user=request.user,
        quest=quest
    )
    
    if quest_progress.completed:
        messages.info(request, _("Você já completou esta quest."))
        return redirect('games:quests')
    
    # Verificar se o objetivo foi atingido
    if quest_progress.progress < quest.objective_target:
        messages.error(request, _("Você ainda não completou o objetivo desta quest. Progresso: {}/{}").format(
            quest_progress.progress, quest.objective_target
        ))
        return redirect('games:quests')
    
    # Se a quest requer um item, verificar se o usuário tem o item na bag
    if quest.required_item_id:
        from ..models import Bag, BagItem
        try:
            bag, bag_created = Bag.objects.get_or_create(user=request.user)
            # Converter para int para garantir compatibilidade
            required_item_id = int(quest.required_item_id)
            required_enchant = int(quest.required_item_enchant) if quest.required_item_enchant else 0
            
            # Primeiro tenta buscar com o enchant específico
            bag_item = BagItem.objects.filter(
                bag=bag,
                item_id=required_item_id,
                enchant=required_enchant
            ).first()
            
            # Se não encontrou e o enchant é 0, tenta buscar qualquer enchant (mais flexível)
            if not bag_item and required_enchant == 0:
                bag_item = BagItem.objects.filter(
                    bag=bag,
                    item_id=required_item_id
                ).first()
            
            if not bag_item:
                # Debug: listar itens na bag para ajudar no diagnóstico
                all_items = BagItem.objects.filter(bag=bag).values_list('item_id', 'item_name', 'quantity', 'enchant')
                items_str = ', '.join([f"{name}(ID:{id},Qty:{qty},Ench:{ench})" for id, name, qty, ench in all_items[:5]])
                messages.error(request, _("Você não possui o item requerido: {} x{} (ID: {}, Enchant: {}). Itens na bag: {}").format(
                    quest.required_item_name or f"Item ID {quest.required_item_id}",
                    quest.required_item_amount,
                    required_item_id,
                    required_enchant,
                    items_str
                ))
                return redirect('games:quests')
            
            if bag_item.quantity < quest.required_item_amount:
                messages.error(request, _("Você não possui quantidade suficiente do item requerido. Necessário: {} x{}, você tem: {}").format(
                    quest.required_item_name or f"Item ID {quest.required_item_id}",
                    quest.required_item_amount,
                    bag_item.quantity
                ))
                return redirect('games:quests')
        except (Bag.DoesNotExist, ValueError, TypeError) as e:
            messages.error(request, _("Erro ao verificar item na bag: {}").format(str(e)))
            return redirect('games:quests')
    
    # Marca como completa
    quest_progress.completed = True
    quest_progress.completed_at = timezone.now()
    quest_progress.save()
    
    # Adiciona XP
    progress.add_xp(quest.xp_reward, source='quest', auto_claim=True)
    
    # Remover item requerido da bag se houver
    item_removed = False
    if quest.required_item_id:
        item_removed = quest.remove_required_item_from_user(request.user)
        if not item_removed:
            messages.warning(request, _("Aviso: O item requerido não foi encontrado na sua bag, mas a quest foi completada."))
    
    # Atualiza estatísticas
    from ..models import BattlePassStatistics
    stats, stats_created = BattlePassStatistics.objects.get_or_create(
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
    
    success_msg = gettext("Quest completada! Você ganhou {} XP!").format(quest.xp_reward)
    if item_removed and quest.required_item_name:
        success_msg += gettext(" Item removido: {} x{}").format(quest.required_item_name, quest.required_item_amount)
    messages.success(request, success_msg)
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

