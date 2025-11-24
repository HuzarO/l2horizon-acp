"""
Utilitários para monitoramento de segurança de pagamentos
"""
import logging
from django.utils import timezone
from django.utils.timezone import timedelta
from ipware import get_client_ip
from .models import TentativaFalsificacao
from utils.notifications import send_notification

logger = logging.getLogger(__name__)


def registrar_tentativa_falsificacao(request, provedor, tipo_tentativa, detalhes=None):
    """
    Registra uma tentativa de falsificação de pagamento
    
    Args:
        request: Objeto request do Django
        provedor: 'Stripe' ou 'MercadoPago'
        tipo_tentativa: Tipo da tentativa (sem_assinatura, assinatura_falsa, etc)
        detalhes: Detalhes adicionais sobre a tentativa
    """
    try:
        ip_address, _ = get_client_ip(request)
        if not ip_address:
            ip_address = '0.0.0.0'
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        tentativa = TentativaFalsificacao.objects.create(
            ip_address=ip_address,
            provedor=provedor,
            tipo_tentativa=tipo_tentativa,
            detalhes=detalhes or '',
            user_agent=user_agent[:500]  # Limita tamanho
        )
        
        # Verifica se deve enviar alerta
        if TentativaFalsificacao.deve_enviar_alerta(ip_address, limite=5, minutos=60):
            enviar_alerta_seguranca(ip_address, provedor, tentativa)
            tentativa.alerta_enviado = True
            tentativa.save(update_fields=['alerta_enviado'])
        
        logger.warning(
            f"Tentativa de falsificação registrada: {provedor} - {tipo_tentativa} - IP: {ip_address}"
        )
        
        return tentativa
    except Exception as e:
        logger.error(f"Erro ao registrar tentativa de falsificação: {e}")
        return None


def enviar_alerta_seguranca(ip_address, provedor, tentativa):
    """
    Envia alerta para staff sobre múltiplas tentativas de falsificação do mesmo IP
    """
    try:
        # Conta tentativas recentes
        tentativas_recentes = TentativaFalsificacao.contar_tentativas_recentes(ip_address, minutos=60)
        
        # Conta tentativas totais nas últimas 24h
        cutoff_24h = timezone.now() - timedelta(hours=24)
        tentativas_24h = TentativaFalsificacao.objects.filter(
            ip_address=ip_address,
            data_tentativa__gte=cutoff_24h
        ).count()
        
        # Busca tipos de tentativas mais comuns
        from django.db.models import Count
        
        tipos_comuns = TentativaFalsificacao.objects.filter(
            ip_address=ip_address,
            data_tentativa__gte=cutoff_24h
        ).values('tipo_tentativa').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        tipos_str = ', '.join([f"{t['tipo_tentativa']} ({t['count']}x)" for t in tipos_comuns])
        
        mensagem = (
            f"🚨 ALERTA DE SEGURANÇA - Múltiplas tentativas de falsificação de pagamento detectadas!\n\n"
            f"IP: {ip_address}\n"
            f"Provedor: {provedor}\n"
            f"Tentativas (última hora): {tentativas_recentes}\n"
            f"Tentativas (últimas 24h): {tentativas_24h}\n"
            f"Tipos mais comuns: {tipos_str}\n"
            f"Última tentativa: {tentativa.tipo_tentativa}\n\n"
            f"Recomendação: Considere bloquear este IP se o padrão continuar."
        )
        
        send_notification(
            user=None,
            notification_type='staff',
            message=mensagem,
            created_by=None
        )
        
        logger.critical(
            f"ALERTA DE SEGURANÇA: {tentativas_recentes} tentativas de falsificação "
            f"do IP {ip_address} nas últimas 60 minutos"
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar alerta de segurança: {e}")


def obter_estatisticas_seguranca(ip_address=None, dias=7):
    """
    Obtém estatísticas de segurança de pagamentos
    
    Args:
        ip_address: IP específico (opcional)
        dias: Número de dias para analisar
    
    Returns:
        dict com estatísticas
    """
    from django.db.models import Count, Q
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(days=dias)
    queryset = TentativaFalsificacao.objects.filter(data_tentativa__gte=cutoff)
    
    if ip_address:
        queryset = queryset.filter(ip_address=ip_address)
    
    total = queryset.count()
    
    por_provedor = queryset.values('provedor').annotate(
        count=Count('id')
    ).order_by('-count')
    
    por_tipo = queryset.values('tipo_tentativa').annotate(
        count=Count('id')
    ).order_by('-count')
    
    ips_mais_ativos = queryset.values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return {
        'total_tentativas': total,
        'por_provedor': list(por_provedor),
        'por_tipo': list(por_tipo),
        'ips_mais_ativos': list(ips_mais_ativos),
        'periodo_dias': dias
    }
