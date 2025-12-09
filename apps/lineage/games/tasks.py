from celery import shared_task
import logging
from django.utils import timezone
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


@shared_task
def desativar_temporadas_expiradas():
    """
    Task para desativar automaticamente temporadas do battle pass que expiraram.
    Verifica temporadas ativas com end_date menor que a data atual e as desativa.
    """
    from .models import BattlePassSeason
    from .services.battle_pass_service import BattlePassService
    
    agora = timezone.now()
    
    # Busca temporadas ativas que já expiraram
    temporadas_expiradas = BattlePassSeason.objects.filter(
        is_active=True,
        end_date__lt=agora
    )
    
    count = temporadas_expiradas.count()
    
    if count == 0:
        logger.debug(_('Nenhuma temporada expirada encontrada para desativar.'))
        return
    
    # Desativa cada temporada expirada
    for temporada in temporadas_expiradas:
        try:
            temporada.is_active = False
            temporada.save()
            logger.info(_('Temporada "%(nome)s" (ID: %(id)s) desativada automaticamente.') % {
                'nome': temporada.name,
                'id': temporada.id
            })
        except Exception as e:
            logger.error(_('Erro ao desativar temporada %(id)s: %(erro)s') % {
                'id': temporada.id,
                'erro': str(e)
            })
    
    # Limpa o cache da temporada ativa após desativar temporadas expiradas
    try:
        BattlePassService.clear_active_season_cache()
    except Exception as e:
        logger.warning(_('Erro ao limpar cache da temporada ativa: %(erro)s') % {
            'erro': str(e)
        })
    
    logger.info(_('%(qtd)d temporada(s) desativada(s) automaticamente.') % {'qtd': count})

