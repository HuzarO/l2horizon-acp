from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import CharacterTransfer
from .services import MarketplaceService


def marketplace_list(request):
    """
    Lista todos os personagens disponíveis para venda.
    """
    transfers = CharacterTransfer.objects.filter(status='for_sale').select_related('seller')
    return render(request, 'marketplace/list.html', {'transfers': transfers})


def character_detail(request, transfer_id):
    """
    Mostra detalhes de um personagem à venda.
    """
    transfer = get_object_or_404(CharacterTransfer, id=transfer_id)
    return render(request, 'marketplace/detail.html', {'transfer': transfer})


@login_required
def sell_character(request):
    """
    Formulário para listar um personagem para venda.
    """
    if request.method == 'POST':
        # TODO: Implementar formulário e validação
        pass
    
    return render(request, 'marketplace/sell.html')


@login_required
def buy_character(request, transfer_id):
    """
    Processa a compra de um personagem.
    """
    if request.method == 'POST':
        try:
            transfer = MarketplaceService.purchase_character(
                buyer=request.user,
                transfer_id=transfer_id
            )
            messages.success(request, _('Compra realizada com sucesso!'))
            return redirect('marketplace:character_detail', transfer_id=transfer.id)
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('marketplace:character_detail', transfer_id=transfer_id)


@login_required
def cancel_sale(request, transfer_id):
    """
    Cancela uma venda.
    """
    if request.method == 'POST':
        try:
            MarketplaceService.cancel_sale(transfer_id, request.user)
            messages.success(request, _('Venda cancelada com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('marketplace:my_sales')


@login_required
def my_sales(request):
    """
    Lista as vendas do usuário.
    """
    sales = CharacterTransfer.objects.filter(seller=request.user).order_by('-listed_at')
    return render(request, 'marketplace/my_sales.html', {'sales': sales})


@login_required
def my_purchases(request):
    """
    Lista as compras do usuário.
    """
    purchases = CharacterTransfer.objects.filter(buyer=request.user).order_by('-sold_at')
    return render(request, 'marketplace/my_purchases.html', {'purchases': purchases})

