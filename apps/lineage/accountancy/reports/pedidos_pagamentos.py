from apps.lineage.payment.models import PedidoPagamento, Pagamento, WebhookLog
from apps.lineage.wallet.models import TransacaoWallet
from django.db.models import Sum, Count, Q
from decimal import Decimal


def validar_origem_pagamento(pedido):
    """
    Valida se o pagamento foi confirmado manualmente por staff ou processado via serviço de pagamento.
    
    Retorna:
    - 'manual': Confirmado manualmente por staff no admin
    - 'servico': Processado via webhook/serviço de pagamento (MercadoPago/Stripe)
    - 'indeterminado': Não foi possível determinar a origem
    """
    # Verifica se existe um Pagamento associado com transaction_code
    try:
        pagamento = Pagamento.objects.filter(pedido_pagamento=pedido).first()
        
        if pagamento:
            # Se tem transaction_code, provavelmente passou pelo serviço
            if pagamento.transaction_code:
                # Verifica se existe webhook log relacionado
                webhook_exists = WebhookLog.objects.filter(
                    Q(data_id=str(pagamento.id)) | 
                    Q(payload__metadata__pagamento_id=str(pagamento.id)) |
                    Q(payload__data__object__metadata__pagamento_id=str(pagamento.id))
                ).exists()
                
                if webhook_exists:
                    return 'servico'
                # Se tem transaction_code mas não tem webhook, ainda pode ser serviço (webhook pode ter falhado)
                # Mas vamos verificar se foi processado por webhook verificando a data de processamento
                if pagamento.processado_em:
                    # Se tem processado_em, provavelmente foi via serviço
                    return 'servico'
                # Se tem transaction_code mas não tem processado_em, pode ser manual também
                return 'indeterminado'
            else:
                # Sem transaction_code, provavelmente foi manual
                return 'manual'
        else:
            # Não tem Pagamento associado, provavelmente foi confirmado manualmente direto no pedido
            # Verifica nas transações da wallet se tem a descrição "confirmação manual"
            try:
                wallet = pedido.usuario.wallet_set.first()
                if wallet:
                    transacoes = TransacaoWallet.objects.filter(
                        wallet=wallet,
                        tipo='ENTRADA',
                        descricao__icontains='confirmação manual por admin'
                    ).order_by('-data')[:1]
                    
                    # Verifica se alguma transação recente corresponde ao valor do pedido
                    for transacao in transacoes:
                        if abs(float(transacao.valor) - float(pedido.total_creditado)) < 0.01:
                            return 'manual'
            except Exception:
                pass
            
            # Se não encontrou evidência de manual, mas não tem pagamento, pode ser manual
            return 'manual'
    except Exception:
        pass
    
    return 'indeterminado'


def pedidos_pagamentos_resumo(pedidos=None):
    # Se não foi passado um queryset, busca todos os pedidos
    if pedidos is None:
        pedidos = PedidoPagamento.objects.all().select_related('usuario').order_by('-data_criacao')

    # FILTRO IMPORTANTE: Para cálculos financeiros, consideramos apenas pedidos CONFIRMADOS/CONCLUÍDOS
    # Isso garante que os totais representem apenas faturamento real
    # CONCLUÍDO é usado no fluxo do Mercado Pago e é equivalente a CONFIRMADO
    # Aplica o filtro sobre o queryset passado (que pode já estar filtrado)
    pedidos_confirmados = pedidos.filter(status__in=['CONFIRMADO', 'CONCLUÍDO', 'CONCLUIDO'])

    # Mapeamento de status do modelo para o template
    # CONCLUÍDO é usado no fluxo do Mercado Pago e é equivalente a CONFIRMADO
    status_mapping = {
        'CONFIRMADO': 'aprovado',
        'CONCLUÍDO': 'aprovado',  # Status usado no fluxo do Mercado Pago
        'CONCLUIDO': 'aprovado',   # Variação sem acento (por segurança)
        'PENDENTE': 'pendente',
        'FALHOU': 'cancelado',
        'PROCESSANDO': 'processando',
    }

    # Mapeamento de métodos de pagamento para exibição
    # Não assumimos qual método específico foi usado (PIX, cartão, boleto)
    # Apenas formatamos o nome para exibição amigável
    metodo_mapping = {
        'MercadoPago': 'Mercado Pago',
        'Stripe': 'Stripe',
        'PIX': 'PIX',
        'CARTAO': 'Cartão',
        'BOLETO': 'Boleto',
    }

    # Calcula contadores de status para TODOS os pedidos (sem filtros)
    # IMPORTANTE: Sempre conta todos os pedidos, independente dos filtros aplicados
    # Isso permite ver o resumo geral mesmo quando há filtros aplicados
    todos_pedidos = PedidoPagamento.objects.all()
    contador_status_raw = todos_pedidos.values('status').annotate(count=Count('id'))
    contador_status = {'aprovado': 0, 'pendente': 0, 'cancelado': 0, 'processando': 0, 'outros': 0}
    
    # Mapeia os status conhecidos e agrupa os desconhecidos em "outros"
    for item in contador_status_raw:
        status_original = item['status']
        status_mapeado = status_mapping.get(status_original)
        
        if status_mapeado:
            # Status conhecido, adiciona ao contador
            if status_mapeado in contador_status:
                contador_status[status_mapeado] += item['count']
        else:
            # Status desconhecido, adiciona a "outros"
            contador_status['outros'] += item['count']
    
    # Conta pedidos confirmados por origem (manual vs serviço)
    contador_origem = {'manual': 0, 'servico': 0, 'indeterminado': 0}
    pedidos_confirmados_para_validacao = pedidos_confirmados.select_related('usuario')
    for pedido in pedidos_confirmados_para_validacao:
        origem = validar_origem_pagamento(pedido)
        contador_origem[origem] += 1

    # Calcula totais financeiros APENAS de pedidos CONFIRMADOS
    # Usando aggregate para eficiência e precisão
    totais_confirmados = pedidos_confirmados.aggregate(
        total_valor_pago=Sum('valor_pago'),
        total_bonus=Sum('bonus_aplicado'),
        total_moedas=Sum('moedas_geradas'),
        count=Count('id')
    )

    # Valores financeiros (apenas confirmados)
    total_valor_pago = totais_confirmados['total_valor_pago'] or Decimal('0.00')
    total_bonus = totais_confirmados['total_bonus'] or Decimal('0.00')
    # IMPORTANTE: Total creditado deve ser sempre = valor_pago + bonus_aplicado
    # Não somamos o campo total_creditado do banco porque pode estar inconsistente
    # Calculamos dinamicamente para garantir precisão financeira
    total_creditado = total_valor_pago + total_bonus
    total_moedas = totais_confirmados['total_moedas'] or Decimal('0.00')
    total_pedidos_confirmados = totais_confirmados['count'] or 0

    # Não precisamos calcular percentuais aqui - será feito na view apenas para a página atual

    # Calcula resumo geral
    # IMPORTANTE: Os totais financeiros são calculados apenas com pedidos CONFIRMADOS
    # Mas o total de pedidos deve mostrar TODOS os pedidos do sistema (independente de status)
    todos_pedidos_count = todos_pedidos.count()  # Total de pedidos no sistema (todos os status)
    media_valor = total_valor_pago / total_pedidos_confirmados if total_pedidos_confirmados > 0 else Decimal('0.00')
    percentual_bonus_geral = (total_bonus / total_valor_pago * 100) if total_valor_pago > 0 else Decimal('0.00')
    
    resumo = {
        'total_pedidos': todos_pedidos_count,  # Total de TODOS os pedidos (independente de status)
        'total_valor_pago': total_valor_pago,  # Soma apenas de pedidos confirmados
        'total_bonus': total_bonus,  # Soma apenas de pedidos confirmados
        'total_creditado': total_creditado,  # Soma apenas de pedidos confirmados
        'total_moedas': total_moedas,  # Soma apenas de pedidos confirmados
        'media_valor': media_valor,  # Média calculada apenas com pedidos confirmados
        'percentual_bonus_geral': percentual_bonus_geral,  # Percentual calculado apenas com pedidos confirmados
        'status_contador': contador_status,  # Contador de todos os status (mostra aprovados, pendentes, etc)
        'origem_contador': contador_origem,  # Contador de origem (manual vs serviço) apenas para pedidos confirmados
    }

    return {
        'queryset': pedidos,  # Retorna o queryset para paginação
        'resumo': resumo,
        'status_mapping': status_mapping,
        'metodo_mapping': metodo_mapping,
    }
