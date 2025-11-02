"""
Services para o marketplace de personagens.
Contém toda a lógica de negócio relacionada à compra/venda de personagens.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import CharacterTransfer, MarketplaceTransaction, ClaimRequest
from utils.dynamic_import import get_query_class

# Importa a classe de queries do Lineage dinamicamente
LineageMarketplace = get_query_class("LineageMarketplace")


class MarketplaceService:
    """
    Serviço principal para gerenciar operações do marketplace.
    """
    
    @staticmethod
    def list_character_for_sale(user, char_id, account_name, price, currency='BRL', notes=''):
        """
        Lista um personagem para venda no marketplace.
        
        Args:
            user: Usuário vendedor (Django User)
            char_id: ID do personagem no banco L2
            account_name: Nome da conta no banco L2
            price: Preço do personagem
            currency: Moeda (BRL, USD, etc.)
            notes: Observações sobre a venda
            
        Returns:
            CharacterTransfer: Objeto criado
        """
        # 1. Verificar se o personagem pertence ao usuário
        if not LineageMarketplace.verify_character_ownership(char_id, account_name):
            raise ValidationError(_("Este personagem não pertence à sua conta."))
        
        # 2. Buscar detalhes do personagem no banco L2
        char_details = LineageMarketplace.get_character_details(char_id)
        if not char_details:
            raise ValidationError(_("Personagem não encontrado."))
        
        # 3. Verificar se o personagem já está à venda
        existing_transfer = CharacterTransfer.objects.filter(
            char_id=char_id,
            status__in=['pending', 'for_sale']
        ).first()
        
        if existing_transfer:
            raise ValidationError(_("Este personagem já está listado para venda."))
        
        # 4. Criar a transferência
        transfer = CharacterTransfer.objects.create(
            char_id=char_id,
            char_name=char_details['char_name'],
            char_level=char_details['level'],
            char_class=char_details['classid'],
            old_account=account_name,
            seller=user,
            price=price,
            currency=currency,
            status='for_sale',
            notes=notes
        )
        
        return transfer
    
    @staticmethod
    @transaction.atomic
    def purchase_character(buyer, transfer_id, payment_method='wallet'):
        """
        Processa a compra de um personagem.
        
        Args:
            buyer: Usuário comprador (Django User)
            transfer_id: ID da transferência
            payment_method: Método de pagamento
            
        Returns:
            CharacterTransfer: Objeto atualizado
        """
        # 1. Buscar a transferência
        transfer = CharacterTransfer.objects.select_for_update().get(
            id=transfer_id,
            status='for_sale'
        )
        
        # 2. Verificar se o comprador não é o vendedor
        if transfer.seller == buyer:
            raise ValidationError(_("Você não pode comprar seu próprio personagem."))
        
        # 3. Processar pagamento (implementar lógica específica)
        # TODO: Integrar com sistema de wallet/pagamento
        
        # 4. Criar transação de compra
        MarketplaceTransaction.objects.create(
            transfer=transfer,
            transaction_type='purchase',
            amount=transfer.price,
            currency=transfer.currency,
            user=buyer,
            status='pending'
        )
        
        # 5. Criar transação de venda
        MarketplaceTransaction.objects.create(
            transfer=transfer,
            transaction_type='sale',
            amount=transfer.price,
            currency=transfer.currency,
            user=transfer.seller,
            status='pending'
        )
        
        # 6. Atualizar transferência
        transfer.buyer = buyer
        transfer.status = 'sold'
        transfer.sold_at = timezone.now()
        transfer.save()
        
        return transfer
    
    @staticmethod
    @transaction.atomic
    def transfer_character_ownership(transfer_id, new_account_name):
        """
        Transfere a propriedade do personagem no banco L2.
        Deve ser chamado após confirmação de pagamento.
        
        Args:
            transfer_id: ID da transferência
            new_account_name: Nome da nova conta no banco L2
            
        Returns:
            bool: True se transferência foi bem-sucedida
        """
        transfer = CharacterTransfer.objects.get(id=transfer_id)
        
        if transfer.status != 'sold':
            raise ValidationError(_("Esta transferência não está em status de venda."))
        
        # Transferir no banco L2
        success = LineageMarketplace.transfer_character_to_account(
            transfer.char_id,
            new_account_name
        )
        
        if success:
            transfer.new_account = new_account_name
            transfer.save()
            
            # Atualizar transações para completadas
            transfer.transactions.filter(status='pending').update(
                status='completed',
                completed_at=timezone.now()
            )
        
        return success
    
    @staticmethod
    def create_claim(transfer_id, requester, reason):
        """
        Cria uma reivindicação/disputa sobre uma transferência.
        
        Args:
            transfer_id: ID da transferência
            requester: Usuário que está reivindicando
            reason: Motivo da reivindicação
            
        Returns:
            ClaimRequest: Objeto criado
        """
        transfer = CharacterTransfer.objects.get(id=transfer_id)
        
        claim = ClaimRequest.objects.create(
            transfer=transfer,
            char_id=transfer.char_id,
            requester=requester,
            reason=reason,
            status='pending'
        )
        
        # Marcar transferência como em disputa
        transfer.status = 'disputed'
        transfer.save()
        
        return claim
    
    @staticmethod
    def cancel_sale(transfer_id, user):
        """
        Cancela uma venda (apenas se ainda não foi vendida).
        
        Args:
            transfer_id: ID da transferência
            user: Usuário que está cancelando
            
        Returns:
            CharacterTransfer: Objeto atualizado
        """
        transfer = CharacterTransfer.objects.get(id=transfer_id)
        
        # Apenas o vendedor pode cancelar
        if transfer.seller != user:
            raise ValidationError(_("Apenas o vendedor pode cancelar esta venda."))
        
        # Apenas pode cancelar se ainda não foi vendido
        if transfer.status not in ['pending', 'for_sale']:
            raise ValidationError(_("Não é possível cancelar esta venda."))
        
        transfer.status = 'cancelled'
        transfer.save()
        
        return transfer

