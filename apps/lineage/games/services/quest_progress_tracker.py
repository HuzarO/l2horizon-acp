"""
Serviço para rastrear e atualizar o progresso das quests do Battle Pass
"""
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from apps.lineage.games.models import (
    BattlePassQuest, BattlePassQuestProgress, UserBattlePassProgress,
    SpinHistory, BoxItemHistory, SlotMachineHistory, DiceGameHistory,
    FishingRod, BagItem, BattlePassHistory
)


def update_quest_progress(user, quest):
    """
    Atualiza o progresso de uma quest específica para um usuário
    Retorna True se a quest foi completada, False caso contrário
    """
    quest_progress, created = BattlePassQuestProgress.objects.get_or_create(
        user=user,
        quest=quest
    )
    
    # Verificar se já está completa
    if quest_progress.completed:
        return False
    
    # Calcular progresso baseado no tipo de objetivo
    current_progress = _calculate_progress(user, quest)
    
    # Atualizar progresso
    quest_progress.progress = current_progress
    quest_progress.save()
    
    # Verificar se completou
    if current_progress >= quest.objective_target:
        return True
    
    return False


def _calculate_progress(user, quest):
    """
    Calcula o progresso atual do usuário para uma quest específica
    """
    objective_type = quest.objective_type
    objective_target = quest.objective_target
    metadata = quest.objective_metadata or {}
    
    # Determinar data de início baseado no tipo de quest
    now = timezone.now()
    if quest.reset_daily:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif quest.reset_weekly:
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Para quests sazonais ou especiais, usar desde o início da temporada
        if quest.season:
            start_date = quest.season.start_date
        else:
            start_date = user.date_joined
    
    if objective_type == 'xp':
        # Para XP, o progresso é calculado pela quantidade de XP ganho
        # Buscar temporada ativa
        from apps.lineage.games.services.battle_pass_service import BattlePassService
        season = BattlePassService.get_active_season()
        if not season:
            return 0
        
        # Se a quest tem reset (daily/weekly), contar apenas XP desde a data de início
        # Se não tem reset (seasonal/special), usar o XP total do usuário no battle pass
        if quest.reset_daily or quest.reset_weekly:
            # Somar todo o XP ganho desde a data de início
            total_xp = BattlePassHistory.objects.filter(
                user=user,
                season=season,
                action_type='xp_gained',
                created_at__gte=start_date
            ).aggregate(
                total=Sum('xp_amount')
            )['total'] or 0
            return int(total_xp)
        else:
            # Para quests sazonais, usar o XP total do usuário no battle pass
            try:
                progress = UserBattlePassProgress.objects.get(user=user, season=season)
                return progress.xp
            except UserBattlePassProgress.DoesNotExist:
                return 0
    
    elif objective_type == 'roulette_items':
        # Contar itens adquiridos pela roleta desde a data de início
        count = SpinHistory.objects.filter(
            user=user,
            created_at__gte=start_date
        ).exclude(
            prize__isnull=True
        ).count()
        return count
    
    elif objective_type == 'box_items':
        # Contar itens adquiridos em boxes desde a data de início
        count = BoxItemHistory.objects.filter(
            user=user,
            created_at__gte=start_date
        ).count()
        return count
    
    elif objective_type == 'slot_items':
        # Contar itens adquiridos no slot machine desde a data de início
        # Verificar se o prêmio tem item associado
        count = SlotMachineHistory.objects.filter(
            user=user,
            created_at__gte=start_date,
            prize_won__isnull=False
        ).exclude(
            prize_won__item=None
        ).count()
        return count
    
    elif objective_type == 'fishing_rod_level':
        # Verificar nível da vara de pesca
        try:
            rod = FishingRod.objects.get(user=user)
            target_level = metadata.get('rod_level', objective_target)
            if rod.level >= target_level:
                return objective_target
            return 0
        except FishingRod.DoesNotExist:
            return 0
    
    elif objective_type == 'dice_number':
        # Contar vezes que o usuário ganhou com o número específico
        dice_number = metadata.get('dice_number')
        if dice_number:
            count = DiceGameHistory.objects.filter(
                user=user,
                created_at__gte=start_date,
                won=True,
                dice_result=dice_number
            ).count()
            return count
        return 0
    
    elif objective_type == 'game_item':
        # Verificar se o usuário tem o item específico na bag
        item_id = metadata.get('item_id')
        if item_id:
            try:
                from apps.lineage.games.models import Bag
                bag = Bag.objects.get(user=user)
                bag_item = BagItem.objects.filter(
                    bag=bag,
                    item_id=item_id
                ).first()
                if bag_item and bag_item.quantity >= objective_target:
                    return objective_target
                return bag_item.quantity if bag_item else 0
            except:
                return 0
        return 0
    
    return 0


def check_and_update_all_quests(user):
    """
    Verifica e atualiza o progresso de todas as quests ativas para um usuário
    Retorna lista de quests que foram completadas
    """
    completed_quests = []
    
    # Buscar todas as quests ativas
    active_quests = BattlePassQuest.objects.filter(is_active=True)
    
    for quest in active_quests:
        if update_quest_progress(user, quest):
            completed_quests.append(quest)
    
    return completed_quests


def auto_complete_quest(user, quest):
    """
    Completa automaticamente uma quest e dá as recompensas
    """
    from apps.lineage.games.services.battle_pass_service import BattlePassService
    from apps.lineage.games.models import BattlePassHistory, BattlePassStatistics
    
    season = BattlePassService.get_active_season()
    if not season:
        return False
    
    quest_progress, _ = BattlePassQuestProgress.objects.get_or_create(
        user=user,
        quest=quest
    )
    
    if quest_progress.completed:
        return False
    
    # Marcar como completa
    quest_progress.completed = True
    quest_progress.completed_at = timezone.now()
    quest_progress.save()
    
    # Adicionar XP
    progress, _ = UserBattlePassProgress.objects.get_or_create(
        user=user,
        season=season
    )
    progress.add_xp(quest.xp_reward, source='quest', auto_claim=True)
    
    # Remover item requerido da bag se houver
    if quest.required_item_id:
        quest.remove_required_item_from_user(user)
    
    # Atualizar estatísticas
    stats, _ = BattlePassStatistics.objects.get_or_create(
        user=user,
        season=season
    )
    stats.total_quests_completed += 1
    stats.save()
    
    # Registrar no histórico
    BattlePassHistory.objects.create(
        user=user,
        season=season,
        action_type='quest_completed',
        description=f'Completou quest: {quest.title}',
        xp_amount=quest.xp_reward,
        metadata={'quest_id': quest.id, 'quest_type': quest.quest_type}
    )
    
    return True

