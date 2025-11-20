from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from apps.main.home.models import User
import json

from .forms import PedidosPagamentosFilterForm
from .reports.saldo import saldo_usuario
from .reports.fluxo_caixa import fluxo_caixa_por_dia
from .reports.pedidos_pagamentos import pedidos_pagamentos_resumo
from .reports.reconciliacao_wallet import reconciliacao_wallet_transacoes


@staff_member_required
def relatorio_saldo_usuarios(request):
    usuarios = User.objects.all()
    relatorio = []
    
    total_saldo_wallet = 0
    total_saldo_bonus = 0
    total_saldo_calculado = 0
    total_diferenca = 0
    total_transacoes = 0
    contador_status = {'consistente': 0, 'pequena_discrepancia': 0, 'discrepancia': 0, 'sem_carteira': 0}

    for usuario in usuarios:
        info = saldo_usuario(usuario)
        relatorio.append({
            'usuario': usuario.username,
            **info
        })
        
        # Acumula totais
        total_saldo_wallet += float(info.get('saldo_wallet', 0))
        total_saldo_bonus += float(info.get('saldo_bonus', 0))
        total_saldo_calculado += float(info.get('saldo_calculado', 0))
        total_diferenca += float(info.get('diferenca', 0))
        total_transacoes += info.get('num_transacoes', 0)
        status = info.get('status', 'sem_carteira')
        if status in contador_status:
            contador_status[status] += 1

    resumo = {
        'total_usuarios': len(relatorio),
        'total_saldo_wallet': total_saldo_wallet,
        'total_saldo_bonus': total_saldo_bonus,
        'total_saldo_total': total_saldo_wallet + total_saldo_bonus,
        'total_saldo_calculado': total_saldo_calculado,
        'total_diferenca': total_diferenca,
        'total_transacoes': total_transacoes,
        'status_contador': contador_status,
    }

    return render(request, 'accountancy/relatorio_saldo.html', {
        'relatorio': relatorio,
        'resumo': resumo
    })


@staff_member_required
def relatorio_fluxo_caixa(request):
    dados = fluxo_caixa_por_dia()
    relatorio = dados['relatorio']
    resumo = dados['resumo']

    labels = [str(item['data'].strftime('%d/%m')) for item in relatorio]
    entradas = [float(item['entradas']) for item in relatorio]
    saidas = [float(item['saidas']) for item in relatorio]
    saldos = [float(item['saldo']) for item in relatorio]

    labels.reverse()
    entradas.reverse()
    saidas.reverse()
    saldos.reverse()

    context = {
        'labels': json.dumps(labels),
        'entradas': json.dumps(entradas),
        'saidas': json.dumps(saidas),
        'saldos': json.dumps(saldos),
        'relatorio': relatorio,
        'resumo': resumo,
    }

    return render(request, 'accountancy/relatorio_fluxo_caixa.html', context)


@staff_member_required
def relatorio_pedidos_pagamentos(request):
    # Inicializa o formulário de filtros
    filter_form = PedidosPagamentosFilterForm(request.GET)
    
    # Obtém o queryset base
    from apps.lineage.payment.models import PedidoPagamento
    pedidos = PedidoPagamento.objects.all().select_related('usuario').order_by('-data_criacao')
    
    # Aplica os filtros se o formulário for válido
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        metodo = filter_form.cleaned_data.get('metodo')
        data_inicio = filter_form.cleaned_data.get('data_inicio')
        data_fim = filter_form.cleaned_data.get('data_fim')
        usuario = filter_form.cleaned_data.get('usuario')
        valor_minimo = filter_form.cleaned_data.get('valor_minimo')
        valor_maximo = filter_form.cleaned_data.get('valor_maximo')
        
        # Aplica filtro de status
        if status:
            pedidos = pedidos.filter(status=status)
        
        # Aplica filtro de método de pagamento
        if metodo:
            pedidos = pedidos.filter(metodo=metodo)
        
        # Aplica filtro de período de datas
        if data_inicio:
            pedidos = pedidos.filter(data_criacao__date__gte=data_inicio)
        if data_fim:
            pedidos = pedidos.filter(data_criacao__date__lte=data_fim)
        
        # Aplica filtro de usuário (busca por username)
        if usuario:
            pedidos = pedidos.filter(usuario__username__icontains=usuario)
        
        # Aplica filtro de valor
        if valor_minimo is not None:
            pedidos = pedidos.filter(valor_pago__gte=valor_minimo)
        if valor_maximo is not None:
            pedidos = pedidos.filter(valor_pago__lte=valor_maximo)
    
    # Obtém o resumo com totais (calculados sobre os pedidos FILTRADOS)
    dados = pedidos_pagamentos_resumo(pedidos=pedidos)
    resumo = dados['resumo']
    
    # Obtém o queryset paginado (apenas para exibição na tabela)
    pedidos_paginados = dados['queryset']
    
    # Configura a paginação - 50 itens por página
    paginator = Paginator(pedidos_paginados, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Processa apenas os pedidos da página atual para o relatório
    relatorio = []
    from decimal import Decimal
    for pedido in page_obj:
        # Calcula percentual de bônus apenas para os pedidos da página atual
        percentual_bonus = Decimal('0.00')
        if pedido.valor_pago > 0:
            percentual_bonus = (pedido.bonus_aplicado / pedido.valor_pago) * 100
        
        relatorio.append({
            'id_pedido': pedido.id,
            'usuario': pedido.usuario.username,
            'valor': pedido.valor_pago,
            'bonus_aplicado': pedido.bonus_aplicado,
            'total_creditado': pedido.total_creditado,
            'moedas_geradas': pedido.moedas_geradas,
            'percentual_bonus': percentual_bonus,
            'status': dados['status_mapping'].get(pedido.status, pedido.status.lower()),
            'metodo_pagamento': dados['metodo_mapping'].get(pedido.metodo, pedido.metodo.lower()),
            'data': pedido.data_criacao,
        })
    
    return render(request, 'accountancy/relatorio_pedidos_pagamentos.html', {
        'relatorio': relatorio,
        'resumo': resumo,
        'page_obj': page_obj,
        'filter_form': filter_form,
    })


@staff_member_required
def relatorio_reconciliacao_wallet(request):
    dados = reconciliacao_wallet_transacoes()
    return render(request, 'accountancy/relatorio_reconciliacao_wallet.html', {
        'relatorio': dados['relatorio'],
        'resumo': dados['resumo']
    })


@staff_member_required
def dashboard_accountancy(request):
    return render(request, 'accountancy/dashboard.html')
