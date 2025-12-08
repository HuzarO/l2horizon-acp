"""
Service layer para lógica de negócio do Battle Pass
"""
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from typing import Optional, Dict, Tuple
from ..models import (
    BattlePassSeason, BattlePassLevel, UserBattlePassProgress,
    BattlePassReward, BattlePassHistory, BattlePassStatistics,
    BattlePassMilestone
)
from django.urls import reverse


class BattlePassService:
    """Service para operações do Battle Pass"""
    
    CACHE_KEY_ACTIVE_SEASON = 'battle_pass_active_season'
    CACHE_TIMEOUT = 300  # 5 minutos
    
    @staticmethod
    def get_active_season() -> Optional[BattlePassSeason]:
        """
        Obtém a temporada ativa com cache
        Mantém compatibilidade com sistema antigo - busca apenas por is_active=True
        """
        cached_season = cache.get(BattlePassService.CACHE_KEY_ACTIVE_SEASON)
        if cached_season:
            return cached_season
        
        # Busca temporada ativa (comportamento original para compatibilidade)
        season = BattlePassSeason.objects.filter(is_active=True).first()
        
        if season:
            cache.set(
                BattlePassService.CACHE_KEY_ACTIVE_SEASON,
                season,
                BattlePassService.CACHE_TIMEOUT
            )
        
        return season
    
    @staticmethod
    def clear_active_season_cache():
        """Limpa o cache da temporada ativa"""
        cache.delete(BattlePassService.CACHE_KEY_ACTIVE_SEASON)
    
    @staticmethod
    def calculate_progress(
        progress: UserBattlePassProgress
    ) -> Dict[str, any]:
        """
        Calcula o progresso do usuário no battle pass
        
        Returns:
            Dict com informações de progresso:
            - current_level: nível atual
            - current_level_number: número do nível atual
            - next_level: próximo nível
            - current_xp: XP atual no nível
            - xp_for_next_level: XP necessário para próximo nível
            - progress_percentage: porcentagem de progresso
            - is_max_level: se atingiu o nível máximo
        """
        current_level = progress.get_current_level()
        current_level_number = current_level.level if current_level else 0
        
        next_level = BattlePassLevel.objects.filter(
            season=progress.season,
            level__gt=current_level_number
        ).order_by('level').first()
        
        if next_level:
            if current_level_number == 0:
                current_level_xp = 0
            else:
                current_level_xp = current_level.required_xp
            
            xp_for_next_level = next_level.required_xp - current_level_xp
            current_xp = progress.xp - current_level_xp
            progress_percentage = min(100, int((current_xp / xp_for_next_level) * 100))
            is_max_level = False
        else:
            xp_for_next_level = 0
            current_xp = 0
            progress_percentage = 100
            is_max_level = True
        
        return {
            'current_level': current_level,
            'current_level_number': current_level_number,
            'next_level': next_level,
            'current_xp': current_xp,
            'xp_for_next_level': xp_for_next_level,
            'progress_percentage': progress_percentage,
            'is_max_level': is_max_level,
        }
    
    @staticmethod
    def add_xp(user, amount: int, season: Optional[BattlePassSeason] = None) -> Tuple[bool, Optional[int]]:
        """
        Adiciona XP ao progresso do usuário
        
        Args:
            user: Usuário
            amount: Quantidade de XP a adicionar
            season: Temporada (opcional, usa temporada ativa se não fornecido)
        
        Returns:
            Tuple (success, new_level_reached)
            - success: se a operação foi bem-sucedida
            - new_level_reached: nível alcançado (None se não alcançou novo nível)
        """
        if not season:
            season = BattlePassService.get_active_season()
        
        if not season:
            return False, None
        
        progress, created = UserBattlePassProgress.objects.get_or_create(
            user=user,
            season=season
        )
        
        old_level = progress.get_current_level()
        old_level_number = old_level.level if old_level else 0
        
        progress.add_xp(amount, source='service', auto_claim=True)
        
        new_level = progress.get_current_level()
        new_level_number = new_level.level if new_level else 0
        
        # Verifica se alcançou um novo nível
        new_level_reached = None
        if new_level_number > old_level_number:
            new_level_reached = new_level_number
        
        return True, new_level_reached
    
    @staticmethod
    def get_available_rewards(progress: UserBattlePassProgress) -> Dict[str, list]:
        """
        Obtém recompensas disponíveis para resgate
        
        Returns:
            Dict com:
            - available: recompensas disponíveis para resgate
            - locked: recompensas ainda bloqueadas
            - claimed: recompensas já resgatadas
        """
        current_level = progress.get_current_level()
        current_level_number = current_level.level if current_level else 0
        
        all_rewards = BattlePassReward.objects.filter(
            level__season=progress.season
        ).select_related('level').prefetch_related('level__season')
        
        available = []
        locked = []
        claimed = []
        
        claimed_reward_ids = set(progress.claimed_rewards.values_list('id', flat=True))
        
        for reward in all_rewards:
            if reward.id in claimed_reward_ids:
                claimed.append(reward)
            elif reward.level.level <= current_level_number:
                # Verifica se é premium e se o usuário tem premium
                if reward.is_premium and not progress.has_premium:
                    locked.append(reward)
                else:
                    available.append(reward)
            else:
                locked.append(reward)
        
        return {
            'available': available,
            'locked': locked,
            'claimed': claimed,
        }
    
    @staticmethod
    def get_season_time_remaining(season: BattlePassSeason) -> Dict[str, any]:
        """
        Calcula o tempo restante da temporada
        
        Returns:
            Dict com:
            - days: dias restantes
            - hours: horas restantes
            - minutes: minutos restantes
            - total_seconds: segundos totais restantes
            - is_ending_soon: se está acabando em breve (< 7 dias)
            - is_ended: se já terminou
        """
        now = timezone.now()
        
        if now > season.end_date:
            return {
                'days': 0,
                'hours': 0,
                'minutes': 0,
                'total_seconds': 0,
                'is_ending_soon': False,
                'is_ended': True,
            }
        
        delta = season.end_date - now
        total_seconds = int(delta.total_seconds())
        days = delta.days
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'total_seconds': total_seconds,
            'is_ending_soon': days < 7,
            'is_ended': False,
        }
    
    @staticmethod
    def can_claim_reward(progress: UserBattlePassProgress, reward: BattlePassReward) -> Tuple[bool, str]:
        """
        Verifica se o usuário pode resgatar uma recompensa
        
        Returns:
            Tuple (can_claim, reason)
        """
        current_level = progress.get_current_level()
        current_level_number = current_level.level if current_level else 0
        
        # Verifica se atingiu o nível necessário
        if reward.level.level > current_level_number:
            return False, "Você ainda não atingiu o nível necessário para esta recompensa."
        
        # Verifica se já foi resgatada
        if reward in progress.claimed_rewards.all():
            return False, "Você já resgatou esta recompensa."
        
        # Verifica se é premium e se o usuário tem premium
        if reward.is_premium and not progress.has_premium:
            return False, "Você precisa do Passe Premium para resgatar esta recompensa."
        
        return True, ""
    
    @staticmethod
    def handle_level_up(progress: UserBattlePassProgress, old_level: int, new_level: int, auto_claim: bool = True):
        """
        Trata quando o usuário alcança um novo nível
        
        Args:
            progress: Progresso do usuário
            old_level: Nível anterior
            new_level: Novo nível alcançado
            auto_claim: Se deve fazer auto-claim de recompensas free
        """
        from utils.notifications import send_notification
        
        # Verifica se já notificou este nível
        if new_level > progress.last_level_notified:
            # Envia notificação
            battle_pass_url = reverse('games:battle_pass')
            send_notification(
                user=progress.user,
                notification_type='user',
                message=f'🎉 Parabéns! Você alcançou o nível {new_level} no Battle Pass!',
                link=battle_pass_url
            )
            
            progress.last_level_notified = new_level
            progress.save()
        
        # Registra no histórico
        BattlePassHistory.objects.create(
            user=progress.user,
            season=progress.season,
            action_type='level_up',
            description=f'Alcançou o nível {new_level}',
            level_reached=new_level,
            metadata={'old_level': old_level, 'new_level': new_level}
        )
        
        # Verifica se há milestone neste nível
        milestone = BattlePassMilestone.objects.filter(
            season=progress.season,
            level=new_level
        ).first()
        
        if milestone:
            # Adiciona bônus de XP do milestone
            if milestone.bonus_xp > 0:
                progress.add_xp(milestone.bonus_xp, source='milestone', auto_claim=False)
            
            # Registra milestone no histórico
            BattlePassHistory.objects.create(
                user=progress.user,
                season=progress.season,
                action_type='milestone_reached',
                description=f'Milestone alcançado: {milestone.title}',
                level_reached=new_level,
                metadata={'milestone_id': milestone.id, 'bonus_xp': milestone.bonus_xp}
            )
            
            # Atualiza estatísticas
            stats, _ = BattlePassStatistics.objects.get_or_create(
                user=progress.user,
                season=progress.season
            )
            stats.total_milestones_reached += 1
            stats.save()
            
            # Notifica sobre milestone
            send_notification(
                user=progress.user,
                notification_type='user',
                message=f'🏆 Milestone alcançado: {milestone.title}! +{milestone.bonus_xp} XP bônus!',
                link=battle_pass_url
            )
        
        # Auto-claim de recompensas free se habilitado
        if auto_claim:
            # Chama o método diretamente
            method = getattr(progress, 'auto_claim_free_rewards', None)
            if callable(method):
                method()

