from .validators import registrar_validador
from django.utils.translation import get_language_from_request

from apps.main.home.models import AddressUser
from apps.main.solicitation.models import Solicitation
from apps.main.message.models import Friendship

from apps.lineage.shop.models import ShopPurchase, Cart
from apps.lineage.auction.models import Bid, Auction
from apps.lineage.payment.models import PedidoPagamento, Pagamento
from apps.lineage.wallet.models import TransacaoWallet
from apps.lineage.inventory.models import InventoryItem, InventoryLog

import time


@registrar_validador('primeiro_login')
def primeiro_login(user, request=None):
    return True  # Apenas logar

@registrar_validador('10_leiloes')
def dez_leiloes(user, request=None):
    return user.auctions.count() >= 10

@registrar_validador('primeira_solicitacao')
def primeira_solicitacao(user, request=None):
    return Solicitation.objects.filter(user=user).exists()

@registrar_validador('avatar_editado')
def avatar_editado(user, request=None):
    return bool(getattr(user, 'avatar', None))

@registrar_validador('endereco_cadastrado')
def endereco(user, request=None):
    return AddressUser.objects.filter(user=user).exists()

@registrar_validador('email_verificado')
def email_verificado(user, request=None):
    return getattr(user, 'is_email_verified', False)

@registrar_validador('2fa_ativado')
def dois_fatores(user, request=None):
    return getattr(user, 'is_2fa_enabled', False)

@registrar_validador('idioma_trocado')
def idioma(user, request=None):
    if not request:
        return False
    idioma = get_language_from_request(request)
    return idioma != 'pt-br'  # ou qualquer padrão

@registrar_validador('primeiro_amigo')
def primeiro_amigo(user, request=None):
    return Friendship.objects.filter(user=user).exists()

@registrar_validador('primeiro_amigo_aceito')
def primeiro_amigo_aceito(user, request=None):
    return Friendship.objects.filter(user=user, accepted=True).exists()

@registrar_validador('primeira_compra')
def primeira_compra(user, request=None):
    return ShopPurchase.objects.filter(user=user).exists()

@registrar_validador('primeiro_lance')
def primeiro_lance(user, request=None):
    return Bid.objects.filter(bidder=user).exists()

@registrar_validador('primeiro_cupom')
def primeiro_cupom(user, request=None):
    return Cart.objects.filter(user=user, promocao_aplicada__isnull=False).exists()

@registrar_validador('primeiro_pedido_pagamento')
def primeiro_pedido_pagamento(user, request=None):
    return PedidoPagamento.objects.filter(usuario=user).exists()

@registrar_validador('primeiro_pagamento_concluido')
def primeiro_pagamento_concluido(user, request=None):
    return Pagamento.objects.filter(usuario=user, status='approved').exists()

@registrar_validador('primeira_transferencia_para_o_jogo')
def primeira_transferencia_para_o_jogo(user, request=None):
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para o servidor"
    ).exists()

@registrar_validador('primeira_transferencia_para_jogador')
def primeira_transferencia_para_jogador(user, request=None):
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para jogador"
    ).exists()

@registrar_validador('primeira_retirada_item')
def primeira_retirada_item(user, request=None):
    return InventoryItem.objects.filter(inventory__user=user).exists()

@registrar_validador('primeira_insercao_item')
def primeira_insercao_item(user, request=None):
    return InventoryLog.objects.filter(user=user, acao='INSERIU_NO_JOGO').exists()

@registrar_validador('primeira_troca_itens')
def primeira_troca_itens(user, request=None):
    return InventoryLog.objects.filter(user=user, acao='TROCA_ENTRE_PERSONAGENS').exists()

@registrar_validador('nivel_10')
def nivel_10(user, request=None):
    try:
        perfil = user.perfilgamer
        return perfil.level >= 10
    except:
        return False

@registrar_validador('50_lances')
def cinquenta_lances(user, request=None):
    return Bid.objects.filter(bidder=user).count() >= 50

@registrar_validador('primeiro_vencedor_leilao')
def primeiro_vencedor_leilao(user, request=None):
    return Auction.objects.filter(highest_bidder=user, status='finished').exists()

@registrar_validador('1000_xp')
def mil_xp(user, request=None):
    try:
        perfil = user.perfilgamer
        # Calcula XP total acumulado
        xp_total = perfil.xp
        level_atual = perfil.level
        
        # Adiciona XP de todos os níveis anteriores
        for nivel in range(1, level_atual):
            xp_total += 100 + (nivel - 1) * 25
            
        return xp_total >= 1000
    except:
        return False

@registrar_validador('100_transacoes')
def cem_transacoes(user, request=None):
    from apps.lineage.wallet.models import TransacaoWallet, TransacaoBonus
    # Conta transações normais e de bônus
    transacoes_normais = TransacaoWallet.objects.filter(wallet__usuario=user).count()
    transacoes_bonus = TransacaoBonus.objects.filter(wallet__usuario=user).count()
    return (transacoes_normais + transacoes_bonus) >= 100

@registrar_validador('primeiro_bonus')
def primeiro_bonus(user, request=None):
    from apps.lineage.wallet.models import TransacaoBonus
    return TransacaoBonus.objects.filter(wallet__usuario=user, tipo='ENTRADA').exists()

@registrar_validador('nivel_25')
def nivel_25(user, request=None):
    try:
        perfil = user.perfilgamer
        return perfil.level >= 25
    except:
        return False

@registrar_validador('primeira_solicitacao_resolvida')
def primeira_solicitacao_resolvida(user, request=None):
    from apps.main.solicitation.models import Solicitation
    return Solicitation.objects.filter(user=user, status='closed').exists()

# =========================== NOVAS CONQUISTAS CRIATIVAS ===========================

@registrar_validador('colecionador_itens')
def colecionador_itens(user, request=None):
    """Possui 10 ou mais itens no inventário"""
    return InventoryItem.objects.filter(inventory__user=user).count() >= 10

@registrar_validador('mestre_inventario')
def mestre_inventario(user, request=None):
    """Possui 50 ou mais itens no inventário"""
    return InventoryItem.objects.filter(inventory__user=user).count() >= 50

@registrar_validador('trocador_incansavel')
def trocador_incansavel(user, request=None):
    """Realizou 10 ou mais trocas de itens"""
    return InventoryLog.objects.filter(user=user, acao='TROCA_ENTRE_PERSONAGENS').count() >= 10

@registrar_validador('gerenciador_economico')
def gerenciador_economico(user, request=None):
    """Realizou 20 ou mais transferências para o jogo"""
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para o servidor"
    ).count() >= 20

@registrar_validador('benfeitor_comunitario')
def benfeitor_comunitario(user, request=None):
    """Realizou 10 ou mais transferências para outros jogadores"""
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para jogador"
    ).count() >= 10

@registrar_validador('bonus_diario_7dias')
def bonus_diario_7dias(user, request=None):
    """Recebeu bônus diário por 7 dias consecutivos"""
    from apps.lineage.wallet.models import TransacaoBonus
    from django.utils import timezone
    from datetime import timedelta
    
    # Verifica se recebeu bônus nos últimos 7 dias
    data_limite = timezone.now() - timedelta(days=7)
    bonus_recentes = TransacaoBonus.objects.filter(
        wallet__usuario=user,
        tipo='ENTRADA',
        descricao__icontains="Bônus diário",
        created_at__gte=data_limite
    ).count()
    return bonus_recentes >= 7

@registrar_validador('bonus_diario_30dias')
def bonus_diario_30dias(user, request=None):
    """Recebeu bônus diário por 30 dias consecutivos"""
    from apps.lineage.wallet.models import TransacaoBonus
    from django.utils import timezone
    from datetime import timedelta
    
    data_limite = timezone.now() - timedelta(days=30)
    bonus_recentes = TransacaoBonus.objects.filter(
        wallet__usuario=user,
        tipo='ENTRADA',
        descricao__icontains="Bônus diário",
        created_at__gte=data_limite
    ).count()
    return bonus_recentes >= 30

@registrar_validador('patrocinador_ouro')
def patrocinador_ouro(user, request=None):
    """Realizou 5 ou mais pagamentos aprovados"""
    return Pagamento.objects.filter(usuario=user, status='approved').count() >= 5

@registrar_validador('patrocinador_diamante')
def patrocinador_diamante(user, request=None):
    """Realizou 10 ou mais pagamentos aprovados"""
    return Pagamento.objects.filter(usuario=user, status='approved').count() >= 10

@registrar_validador('comprador_frequente')
def comprador_frequente(user, request=None):
    """Realizou 5 ou mais compras na loja"""
    return ShopPurchase.objects.filter(user=user).count() >= 5

@registrar_validador('comprador_vip')
def comprador_vip(user, request=None):
    """Realizou 15 ou mais compras na loja"""
    return ShopPurchase.objects.filter(user=user).count() >= 15

@registrar_validador('leiloeiro_profissional')
def leiloeiro_profissional(user, request=None):
    """Criou 25 ou mais leilões"""
    return user.auctions.count() >= 25

@registrar_validador('leiloeiro_mestre')
def leiloeiro_mestre(user, request=None):
    """Criou 50 ou mais leilões"""
    return user.auctions.count() >= 50

@registrar_validador('lanceador_profissional')
def lanceador_profissional(user, request=None):
    """Realizou 100 ou mais lances"""
    return Bid.objects.filter(bidder=user).count() >= 100

@registrar_validador('lanceador_mestre')
def lanceador_mestre(user, request=None):
    """Realizou 200 ou mais lances"""
    return Bid.objects.filter(bidder=user).count() >= 200

@registrar_validador('vencedor_serie')
def vencedor_serie(user, request=None):
    """Venceu 3 ou mais leilões"""
    return Auction.objects.filter(highest_bidder=user, status='finished').count() >= 3

@registrar_validador('vencedor_mestre')
def vencedor_mestre(user, request=None):
    """Venceu 10 ou mais leilões"""
    return Auction.objects.filter(highest_bidder=user, status='finished').count() >= 10

@registrar_validador('cupom_mestre')
def cupom_mestre(user, request=None):
    """Aplicou 5 ou mais cupons promocionais"""
    return Cart.objects.filter(user=user, promocao_aplicada__isnull=False).count() >= 5

@registrar_validador('cupom_expert')
def cupom_expert(user, request=None):
    """Aplicou 15 ou mais cupons promocionais"""
    return Cart.objects.filter(user=user, promocao_aplicada__isnull=False).count() >= 15

@registrar_validador('solicitante_frequente')
def solicitante_frequente(user, request=None):
    """Abriu 5 ou mais solicitações de suporte"""
    return Solicitation.objects.filter(user=user).count() >= 5

@registrar_validador('solicitante_expert')
def solicitante_expert(user, request=None):
    """Abriu 15 ou mais solicitações de suporte"""
    return Solicitation.objects.filter(user=user).count() >= 15

@registrar_validador('resolvedor_problemas')
def resolvedor_problemas(user, request=None):
    """Teve 3 ou mais solicitações resolvidas"""
    return Solicitation.objects.filter(user=user, status='closed').count() >= 3

@registrar_validador('resolvedor_mestre')
def resolvedor_mestre(user, request=None):
    """Teve 10 ou mais solicitações resolvidas"""
    return Solicitation.objects.filter(user=user, status='closed').count() >= 10

@registrar_validador('rede_social')
def rede_social(user, request=None):
    """Tem 5 ou mais amigos aceitos"""
    return Friendship.objects.filter(user=user, accepted=True).count() >= 5

@registrar_validador('rede_social_mestre')
def rede_social_mestre(user, request=None):
    """Tem 15 ou mais amigos aceitos"""
    return Friendship.objects.filter(user=user, accepted=True).count() >= 15

@registrar_validador('nivel_50')
def nivel_50(user, request=None):
    """Alcançou o nível 50 no sistema"""
    try:
        perfil = user.perfilgamer
        return perfil.level >= 50
    except:
        return False

@registrar_validador('nivel_75')
def nivel_75(user, request=None):
    """Alcançou o nível 75 no sistema"""
    try:
        perfil = user.perfilgamer
        return perfil.level >= 75
    except:
        return False

@registrar_validador('nivel_100')
def nivel_100(user, request=None):
    """Alcançou o nível 100 no sistema"""
    try:
        perfil = user.perfilgamer
        return perfil.level >= 100
    except:
        return False

@registrar_validador('5000_xp')
def cinco_mil_xp(user, request=None):
    """Acumulou 5000 pontos de experiência"""
    try:
        perfil = user.perfilgamer
        xp_total = perfil.xp
        level_atual = perfil.level
        
        for nivel in range(1, level_atual):
            xp_total += 100 + (nivel - 1) * 25
            
        return xp_total >= 5000
    except:
        return False

@registrar_validador('10000_xp')
def dez_mil_xp(user, request=None):
    """Acumulou 10000 pontos de experiência"""
    try:
        perfil = user.perfilgamer
        xp_total = perfil.xp
        level_atual = perfil.level
        
        for nivel in range(1, level_atual):
            xp_total += 100 + (nivel - 1) * 25
            
        return xp_total >= 10000
    except:
        return False

@registrar_validador('250_transacoes')
def duzentos_cinquenta_transacoes(user, request=None):
    """Realizou 250 transações na carteira"""
    from apps.lineage.wallet.models import TransacaoWallet, TransacaoBonus
    transacoes_normais = TransacaoWallet.objects.filter(wallet__usuario=user).count()
    transacoes_bonus = TransacaoBonus.objects.filter(wallet__usuario=user).count()
    return (transacoes_normais + transacoes_bonus) >= 250

@registrar_validador('500_transacoes')
def quinhentas_transacoes(user, request=None):
    """Realizou 500 transações na carteira"""
    from apps.lineage.wallet.models import TransacaoWallet, TransacaoBonus
    transacoes_normais = TransacaoWallet.objects.filter(wallet__usuario=user).count()
    transacoes_bonus = TransacaoBonus.objects.filter(wallet__usuario=user).count()
    return (transacoes_normais + transacoes_bonus) >= 500

@registrar_validador('bonus_mestre')
def bonus_mestre(user, request=None):
    """Recebeu 10 ou mais bônus"""
    from apps.lineage.wallet.models import TransacaoBonus
    return TransacaoBonus.objects.filter(wallet__usuario=user, tipo='ENTRADA').count() >= 10

@registrar_validador('bonus_expert')
def bonus_expert(user, request=None):
    """Recebeu 25 ou mais bônus"""
    from apps.lineage.wallet.models import TransacaoBonus
    return TransacaoBonus.objects.filter(wallet__usuario=user, tipo='ENTRADA').count() >= 25

# =========================== CONQUISTAS DE JOGOS ===========================

@registrar_validador('primeiro_spin')
def primeiro_spin(user, request=None):
    """Realizou o primeiro giro na roleta"""
    from apps.lineage.games.models import SpinHistory
    return SpinHistory.objects.filter(user=user).exists()

@registrar_validador('10_spins')
def dez_spins(user, request=None):
    """Realizou 10 giros na roleta"""
    from apps.lineage.games.models import SpinHistory
    return SpinHistory.objects.filter(user=user).count() >= 10

@registrar_validador('50_spins')
def cinquenta_spins(user, request=None):
    """Realizou 50 giros na roleta"""
    from apps.lineage.games.models import SpinHistory
    return SpinHistory.objects.filter(user=user).count() >= 50

@registrar_validador('100_spins')
def cem_spins(user, request=None):
    """Realizou 100 giros na roleta"""
    from apps.lineage.games.models import SpinHistory
    return SpinHistory.objects.filter(user=user).count() >= 100

@registrar_validador('primeiro_premio_roleta')
def primeiro_premio_roleta(user, request=None):
    """Ganhou o primeiro prêmio na roleta"""
    from apps.lineage.games.models import SpinHistory
    return SpinHistory.objects.filter(user=user, prize__isnull=False).exists()

@registrar_validador('primeira_caixa_aberta')
def primeira_caixa_aberta(user, request=None):
    """Abriu a primeira caixa"""
    from apps.lineage.games.models import Box
    return Box.objects.filter(user=user, opened=True).exists()

@registrar_validador('10_caixas_abertas')
def dez_caixas_abertas(user, request=None):
    """Abriu 10 caixas"""
    from apps.lineage.games.models import Box
    return Box.objects.filter(user=user, opened=True).count() >= 10

@registrar_validador('50_caixas_abertas')
def cinquenta_caixas_abertas(user, request=None):
    """Abriu 50 caixas"""
    from apps.lineage.games.models import Box
    return Box.objects.filter(user=user, opened=True).count() >= 50

@registrar_validador('100_caixas_abertas')
def cem_caixas_abertas(user, request=None):
    """Abriu 100 caixas"""
    from apps.lineage.games.models import Box
    return Box.objects.filter(user=user, opened=True).count() >= 100

@registrar_validador('item_epico_caixa')
def item_epico_caixa(user, request=None):
    """Obteve um item épico de uma caixa"""
    from apps.lineage.games.models import BoxItemHistory
    return BoxItemHistory.objects.filter(
        user=user,
        item__rarity='EPICO'
    ).exists()

@registrar_validador('item_lendario_caixa')
def item_lendario_caixa(user, request=None):
    """Obteve um item lendário de uma caixa"""
    from apps.lineage.games.models import BoxItemHistory
    return BoxItemHistory.objects.filter(
        user=user,
        item__rarity='LENDARIO'
    ).exists()

@registrar_validador('primeira_jogada_slot')
def primeira_jogada_slot(user, request=None):
    """Realizou a primeira jogada na Slot Machine"""
    from apps.lineage.games.models import SlotMachineHistory
    return SlotMachineHistory.objects.filter(user=user).exists()

@registrar_validador('10_jogadas_slot')
def dez_jogadas_slot(user, request=None):
    """Realizou 10 jogadas na Slot Machine"""
    from apps.lineage.games.models import SlotMachineHistory
    return SlotMachineHistory.objects.filter(user=user).count() >= 10

@registrar_validador('50_jogadas_slot')
def cinquenta_jogadas_slot(user, request=None):
    """Realizou 50 jogadas na Slot Machine"""
    from apps.lineage.games.models import SlotMachineHistory
    return SlotMachineHistory.objects.filter(user=user).count() >= 50

@registrar_validador('100_jogadas_slot')
def cem_jogadas_slot(user, request=None):
    """Realizou 100 jogadas na Slot Machine"""
    from apps.lineage.games.models import SlotMachineHistory
    return SlotMachineHistory.objects.filter(user=user).count() >= 100

@registrar_validador('primeiro_jackpot')
def primeiro_jackpot(user, request=None):
    """Ganhou o primeiro jackpot na Slot Machine"""
    from apps.lineage.games.models import SlotMachineHistory
    return SlotMachineHistory.objects.filter(user=user, is_jackpot=True).exists()

@registrar_validador('jackpot_mestre')
def jackpot_mestre(user, request=None):
    """Ganhou 3 ou mais jackpots"""
    from apps.lineage.games.models import SlotMachineHistory
    return SlotMachineHistory.objects.filter(user=user, is_jackpot=True).count() >= 3

@registrar_validador('primeira_jogada_dice')
def primeira_jogada_dice(user, request=None):
    """Realizou a primeira jogada no Dice Game"""
    from apps.lineage.games.models import DiceGameHistory
    return DiceGameHistory.objects.filter(user=user).exists()

@registrar_validador('10_jogadas_dice')
def dez_jogadas_dice(user, request=None):
    """Realizou 10 jogadas no Dice Game"""
    from apps.lineage.games.models import DiceGameHistory
    return DiceGameHistory.objects.filter(user=user).count() >= 10

@registrar_validador('50_jogadas_dice')
def cinquenta_jogadas_dice(user, request=None):
    """Realizou 50 jogadas no Dice Game"""
    from apps.lineage.games.models import DiceGameHistory
    return DiceGameHistory.objects.filter(user=user).count() >= 50

@registrar_validador('primeira_vitoria_dice')
def primeira_vitoria_dice(user, request=None):
    """Ganhou a primeira aposta no Dice Game"""
    from apps.lineage.games.models import DiceGameHistory
    return DiceGameHistory.objects.filter(user=user, won=True).exists()

@registrar_validador('10_vitorias_dice')
def dez_vitorias_dice(user, request=None):
    """Ganhou 10 apostas no Dice Game"""
    from apps.lineage.games.models import DiceGameHistory
    return DiceGameHistory.objects.filter(user=user, won=True).count() >= 10

@registrar_validador('50_vitorias_dice')
def cinquenta_vitorias_dice(user, request=None):
    """Ganhou 50 apostas no Dice Game"""
    from apps.lineage.games.models import DiceGameHistory
    return DiceGameHistory.objects.filter(user=user, won=True).count() >= 50

@registrar_validador('primeira_pescaria')
def primeira_pescaria(user, request=None):
    """Realizou a primeira pescaria"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(user=user, success=True).exists()

@registrar_validador('10_peixes_capturados')
def dez_peixes_capturados(user, request=None):
    """Capturou 10 peixes"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(user=user, success=True).count() >= 10

@registrar_validador('50_peixes_capturados')
def cinquenta_peixes_capturados(user, request=None):
    """Capturou 50 peixes"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(user=user, success=True).count() >= 50

@registrar_validador('100_peixes_capturados')
def cem_peixes_capturados(user, request=None):
    """Capturou 100 peixes"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(user=user, success=True).count() >= 100

@registrar_validador('peixe_raro')
def peixe_raro(user, request=None):
    """Capturou um peixe raro"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(
        user=user,
        success=True,
        fish__rarity='rare'
    ).exists()

@registrar_validador('peixe_epico')
def peixe_epico(user, request=None):
    """Capturou um peixe épico"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(
        user=user,
        success=True,
        fish__rarity='epic'
    ).exists()

@registrar_validador('peixe_lendario')
def peixe_lendario(user, request=None):
    """Capturou um peixe lendário"""
    from apps.lineage.games.models import FishingHistory
    return FishingHistory.objects.filter(
        user=user,
        success=True,
        fish__rarity='legendary'
    ).exists()

@registrar_validador('vara_nivel_5')
def vara_nivel_5(user, request=None):
    """Alcançou o nível 5 na vara de pesca"""
    from apps.lineage.games.models import FishingRod
    try:
        rod = user.fishingrod
        return rod.level >= 5
    except:
        return False

@registrar_validador('vara_nivel_10')
def vara_nivel_10(user, request=None):
    """Alcançou o nível 10 na vara de pesca"""
    from apps.lineage.games.models import FishingRod
    try:
        rod = user.fishingrod
        return rod.level >= 10
    except:
        return False

@registrar_validador('vara_nivel_20')
def vara_nivel_20(user, request=None):
    """Alcançou o nível 20 na vara de pesca"""
    from apps.lineage.games.models import FishingRod
    try:
        rod = user.fishingrod
        return rod.level >= 20
    except:
        return False

# =========================== CONQUISTAS DE BATTLE PASS ===========================

@registrar_validador('primeiro_battle_pass')
def primeiro_battle_pass(user, request=None):
    """Participou do primeiro Battle Pass"""
    from apps.lineage.games.models import UserBattlePassProgress
    return UserBattlePassProgress.objects.filter(user=user).exists()

@registrar_validador('battle_pass_nivel_10')
def battle_pass_nivel_10(user, request=None):
    """Alcançou o nível 10 no Battle Pass"""
    from apps.lineage.games.models import UserBattlePassProgress
    return UserBattlePassProgress.objects.filter(user=user, level__gte=10).exists()

@registrar_validador('battle_pass_nivel_25')
def battle_pass_nivel_25(user, request=None):
    """Alcançou o nível 25 no Battle Pass"""
    from apps.lineage.games.models import UserBattlePassProgress
    return UserBattlePassProgress.objects.filter(user=user, level__gte=25).exists()

@registrar_validador('battle_pass_nivel_50')
def battle_pass_nivel_50(user, request=None):
    """Alcançou o nível 50 no Battle Pass"""
    from apps.lineage.games.models import UserBattlePassProgress
    return UserBattlePassProgress.objects.filter(user=user, level__gte=50).exists()

@registrar_validador('primeira_quest_battle_pass')
def primeira_quest_battle_pass(user, request=None):
    """Completou a primeira quest do Battle Pass"""
    from apps.lineage.games.models import BattlePassQuestProgress
    return BattlePassQuestProgress.objects.filter(user=user, completed=True).exists()

@registrar_validador('10_quests_battle_pass')
def dez_quests_battle_pass(user, request=None):
    """Completou 10 quests do Battle Pass"""
    from apps.lineage.games.models import BattlePassQuestProgress
    return BattlePassQuestProgress.objects.filter(user=user, completed=True).count() >= 10

@registrar_validador('25_quests_battle_pass')
def vinte_cinco_quests_battle_pass(user, request=None):
    """Completou 25 quests do Battle Pass"""
    from apps.lineage.games.models import BattlePassQuestProgress
    return BattlePassQuestProgress.objects.filter(user=user, completed=True).count() >= 25

@registrar_validador('primeiro_milestone_battle_pass')
def primeiro_milestone_battle_pass(user, request=None):
    """Alcançou o primeiro milestone do Battle Pass"""
    from apps.lineage.games.models import BattlePassHistory
    return BattlePassHistory.objects.filter(
        user=user,
        action_type='milestone_reached'
    ).exists()

@registrar_validador('battle_pass_premium')
def battle_pass_premium(user, request=None):
    """Comprou o Battle Pass Premium"""
    from apps.lineage.games.models import BattlePassHistory
    return BattlePassHistory.objects.filter(
        user=user,
        action_type='premium_purchased'
    ).exists()

# =========================== CONQUISTAS DE DAILY BONUS ===========================

@registrar_validador('primeiro_daily_bonus')
def primeiro_daily_bonus(user, request=None):
    """Recebeu o primeiro Daily Bonus"""
    from apps.lineage.games.models import DailyBonusClaim
    return DailyBonusClaim.objects.filter(user=user).exists()

@registrar_validador('daily_bonus_7dias')
def daily_bonus_7dias(user, request=None):
    """Recebeu Daily Bonus por 7 dias"""
    from apps.lineage.games.models import DailyBonusClaim
    return DailyBonusClaim.objects.filter(user=user).count() >= 7

@registrar_validador('daily_bonus_30dias')
def daily_bonus_30dias(user, request=None):
    """Recebeu Daily Bonus por 30 dias"""
    from apps.lineage.games.models import DailyBonusClaim
    return DailyBonusClaim.objects.filter(user=user).count() >= 30

@registrar_validador('daily_bonus_100dias')
def daily_bonus_100dias(user, request=None):
    """Recebeu Daily Bonus por 100 dias"""
    from apps.lineage.games.models import DailyBonusClaim
    return DailyBonusClaim.objects.filter(user=user).count() >= 100

# =========================== CONQUISTAS DE MARKETPLACE ===========================

@registrar_validador('primeira_transacao_marketplace')
def primeira_transacao_marketplace(user, request=None):
    """Realizou a primeira transação no Marketplace"""
    from apps.lineage.marketplace.models import MarketplaceTransaction
    return MarketplaceTransaction.objects.filter(
        buyer=user
    ).exists() or MarketplaceTransaction.objects.filter(
        seller=user
    ).exists()

@registrar_validador('5_transacoes_marketplace')
def cinco_transacoes_marketplace(user, request=None):
    """Realizou 5 ou mais transações no Marketplace"""
    from apps.lineage.marketplace.models import MarketplaceTransaction
    compras = MarketplaceTransaction.objects.filter(buyer=user).count()
    vendas = MarketplaceTransaction.objects.filter(seller=user).count()
    return (compras + vendas) >= 5

@registrar_validador('10_transacoes_marketplace')
def dez_transacoes_marketplace(user, request=None):
    """Realizou 10 ou mais transações no Marketplace"""
    from apps.lineage.marketplace.models import MarketplaceTransaction
    compras = MarketplaceTransaction.objects.filter(buyer=user).count()
    vendas = MarketplaceTransaction.objects.filter(seller=user).count()
    return (compras + vendas) >= 10

@registrar_validador('primeira_transferencia_personagem')
def primeira_transferencia_personagem(user, request=None):
    """Realizou a primeira transferência de personagem"""
    from apps.lineage.marketplace.models import CharacterTransfer
    return CharacterTransfer.objects.filter(user=user).exists()

# =========================== CONQUISTAS DE BAGS ===========================

@registrar_validador('primeira_bag')
def primeira_bag(user, request=None):
    """Obteve a primeira bag"""
    from apps.lineage.games.models import Bag
    return Bag.objects.filter(user=user).exists()

@registrar_validador('10_itens_bag')
def dez_itens_bag(user, request=None):
    """Coletou 10 ou mais itens em bags"""
    from apps.lineage.games.models import BagItem
    return BagItem.objects.filter(bag__user=user).count() >= 10

@registrar_validador('50_itens_bag')
def cinquenta_itens_bag(user, request=None):
    """Coletou 50 ou mais itens em bags"""
    from apps.lineage.games.models import BagItem
    return BagItem.objects.filter(bag__user=user).count() >= 50

@registrar_validador('100_itens_bag')
def cem_itens_bag(user, request=None):
    """Coletou 100 ou mais itens em bags"""
    from apps.lineage.games.models import BagItem
    return BagItem.objects.filter(bag__user=user).count() >= 100

# =========================== CONQUISTAS ADICIONAIS DE INVENTÁRIO ===========================

@registrar_validador('100_itens_inventario')
def cem_itens_inventario(user, request=None):
    """Possui 100 ou mais itens no inventário"""
    return InventoryItem.objects.filter(inventory__user=user).count() >= 100

@registrar_validador('200_itens_inventario')
def duzentos_itens_inventario(user, request=None):
    """Possui 200 ou mais itens no inventário"""
    return InventoryItem.objects.filter(inventory__user=user).count() >= 200

@registrar_validador('50_insercoes_jogo')
def cinquenta_insercoes_jogo(user, request=None):
    """Inseriu 50 ou mais itens no jogo"""
    return InventoryLog.objects.filter(user=user, acao='INSERIU_NO_JOGO').count() >= 50

@registrar_validador('100_insercoes_jogo')
def cem_insercoes_jogo(user, request=None):
    """Inseriu 100 ou mais itens no jogo"""
    return InventoryLog.objects.filter(user=user, acao='INSERIU_NO_JOGO').count() >= 100

@registrar_validador('50_trocas_itens')
def cinquenta_trocas_itens(user, request=None):
    """Realizou 50 ou mais trocas de itens"""
    return InventoryLog.objects.filter(user=user, acao='TROCA_ENTRE_PERSONAGENS').count() >= 50

# =========================== CONQUISTAS ADICIONAIS DE XP E NÍVEIS ===========================

@registrar_validador('25000_xp')
def vinte_cinco_mil_xp(user, request=None):
    """Acumulou 25000 pontos de experiência"""
    try:
        perfil = user.perfilgamer
        xp_total = perfil.xp
        level_atual = perfil.level
        
        for nivel in range(1, level_atual):
            xp_total += 100 + (nivel - 1) * 25
            
        return xp_total >= 25000
    except:
        return False

@registrar_validador('50000_xp')
def cinquenta_mil_xp(user, request=None):
    """Acumulou 50000 pontos de experiência"""
    try:
        perfil = user.perfilgamer
        xp_total = perfil.xp
        level_atual = perfil.level
        
        for nivel in range(1, level_atual):
            xp_total += 100 + (nivel - 1) * 25
            
        return xp_total >= 50000
    except:
        return False

@registrar_validador('100000_xp')
def cem_mil_xp(user, request=None):
    """Acumulou 100000 pontos de experiência"""
    try:
        perfil = user.perfilgamer
        xp_total = perfil.xp
        level_atual = perfil.level
        
        for nivel in range(1, level_atual):
            xp_total += 100 + (nivel - 1) * 25
            
        return xp_total >= 100000
    except:
        return False

# =========================== CONQUISTAS ADICIONAIS DE TRANSFERÊNCIAS ===========================

@registrar_validador('50_transferencias_jogo')
def cinquenta_transferencias_jogo(user, request=None):
    """Realizou 50 ou mais transferências para o jogo"""
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para o servidor"
    ).count() >= 50

@registrar_validador('100_transferencias_jogo')
def cem_transferencias_jogo(user, request=None):
    """Realizou 100 ou mais transferências para o jogo"""
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para o servidor"
    ).count() >= 100

@registrar_validador('50_transferencias_jogadores')
def cinquenta_transferencias_jogadores(user, request=None):
    """Realizou 50 ou mais transferências para outros jogadores"""
    return TransacaoWallet.objects.filter(
        wallet__usuario=user,
        tipo="SAIDA",
        descricao__icontains="Transferência para jogador"
    ).count() >= 50

# =========================== CONQUISTAS ADICIONAIS DE LEILÕES ===========================

@registrar_validador('100_leiloes')
def cem_leiloes(user, request=None):
    """Criou 100 ou mais leilões"""
    return user.auctions.count() >= 100

@registrar_validador('300_lances')
def trezentos_lances(user, request=None):
    """Realizou 300 ou mais lances"""
    return Bid.objects.filter(bidder=user).count() >= 300

@registrar_validador('500_lances')
def quinhentos_lances(user, request=None):
    """Realizou 500 ou mais lances"""
    return Bid.objects.filter(bidder=user).count() >= 500

@registrar_validador('25_vencedor_leiloes')
def vinte_cinco_vencedor_leiloes(user, request=None):
    """Venceu 25 ou mais leilões"""
    return Auction.objects.filter(highest_bidder=user, status='finished').count() >= 25

@registrar_validador('50_vencedor_leiloes')
def cinquenta_vencedor_leiloes(user, request=None):
    """Venceu 50 ou mais leilões"""
    return Auction.objects.filter(highest_bidder=user, status='finished').count() >= 50

# =========================== CONQUISTAS ADICIONAIS DE COMPRAS ===========================

@registrar_validador('30_compras')
def trinta_compras(user, request=None):
    """Realizou 30 ou mais compras na loja"""
    return ShopPurchase.objects.filter(user=user).count() >= 30

@registrar_validador('50_compras')
def cinquenta_compras(user, request=None):
    """Realizou 50 ou mais compras na loja"""
    return ShopPurchase.objects.filter(user=user).count() >= 50

@registrar_validador('25_cupons')
def vinte_cinco_cupons(user, request=None):
    """Aplicou 25 ou mais cupons promocionais"""
    return Cart.objects.filter(user=user, promocao_aplicada__isnull=False).count() >= 25

@registrar_validador('50_cupons')
def cinquenta_cupons(user, request=None):
    """Aplicou 50 ou mais cupons promocionais"""
    return Cart.objects.filter(user=user, promocao_aplicada__isnull=False).count() >= 50

# =========================== CONQUISTAS ADICIONAIS DE PAGAMENTOS ===========================

@registrar_validador('25_pagamentos')
def vinte_cinco_pagamentos(user, request=None):
    """Realizou 25 ou mais pagamentos aprovados"""
    return Pagamento.objects.filter(usuario=user, status='approved').count() >= 25

@registrar_validador('50_pagamentos')
def cinquenta_pagamentos(user, request=None):
    """Realizou 50 ou mais pagamentos aprovados"""
    return Pagamento.objects.filter(usuario=user, status='approved').count() >= 50

# =========================== CONQUISTAS ADICIONAIS DE AMIZADES ===========================

@registrar_validador('30_amigos')
def trinta_amigos(user, request=None):
    """Tem 30 ou mais amigos aceitos"""
    return Friendship.objects.filter(user=user, accepted=True).count() >= 30

@registrar_validador('50_amigos')
def cinquenta_amigos(user, request=None):
    """Tem 50 ou mais amigos aceitos"""
    return Friendship.objects.filter(user=user, accepted=True).count() >= 50

# =========================== CONQUISTAS ADICIONAIS DE SOLICITAÇÕES ===========================

@registrar_validador('30_solicitacoes')
def trinta_solicitacoes(user, request=None):
    """Abriu 30 ou mais solicitações de suporte"""
    return Solicitation.objects.filter(user=user).count() >= 30

@registrar_validador('25_solicitacoes_resolvidas')
def vinte_cinco_solicitacoes_resolvidas(user, request=None):
    """Teve 25 ou mais solicitações resolvidas"""
    return Solicitation.objects.filter(user=user, status='closed').count() >= 25

# =========================== CONQUISTAS ADICIONAIS DE TRANSACOES ===========================

@registrar_validador('1000_transacoes')
def mil_transacoes(user, request=None):
    """Realizou 1000 transações na carteira"""
    from apps.lineage.wallet.models import TransacaoWallet, TransacaoBonus
    transacoes_normais = TransacaoWallet.objects.filter(wallet__usuario=user).count()
    transacoes_bonus = TransacaoBonus.objects.filter(wallet__usuario=user).count()
    return (transacoes_normais + transacoes_bonus) >= 1000

@registrar_validador('50_bonus')
def cinquenta_bonus(user, request=None):
    """Recebeu 50 ou mais bônus"""
    from apps.lineage.wallet.models import TransacaoBonus
    return TransacaoBonus.objects.filter(wallet__usuario=user, tipo='ENTRADA').count() >= 50

@registrar_validador('100_bonus')
def cem_bonus(user, request=None):
    """Recebeu 100 ou mais bônus"""
    from apps.lineage.wallet.models import TransacaoBonus
    return TransacaoBonus.objects.filter(wallet__usuario=user, tipo='ENTRADA').count() >= 100

# =========================== CONQUISTAS DE FEED SOCIAL ===========================

@registrar_validador('primeira_visita_feed')
def primeira_visita_feed(user, request=None):
    """Visitou o feed social pela primeira vez"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='social_feed'
    ).exists()

@registrar_validador('10_visitas_feed')
def dez_visitas_feed(user, request=None):
    """Visitou o feed social 10 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='social_feed'
    ).count() >= 10

@registrar_validador('50_visitas_feed')
def cinquenta_visitas_feed(user, request=None):
    """Visitou o feed social 50 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='social_feed'
    ).count() >= 50

@registrar_validador('100_visitas_feed')
def cem_visitas_feed(user, request=None):
    """Visitou o feed social 100 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='social_feed'
    ).count() >= 100

# =========================== CONQUISTAS DE EXPLORAÇÃO - TOPS ===========================

@registrar_validador('primeira_visita_tops')
def primeira_visita_tops(user, request=None):
    """Visitou uma página de tops pela primeira vez"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='tops'
    ).exists()

@registrar_validador('5_paginas_tops')
def cinco_paginas_tops(user, request=None):
    """Visitou 5 páginas diferentes de tops"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='tops'
    ).values('url_path').distinct().count() >= 5

@registrar_validador('todas_paginas_tops')
def todas_paginas_tops(user, request=None):
    """Visitou todas as páginas de tops"""
    from apps.main.home.models import PageView
    # Conta quantas páginas únicas de tops foram visitadas
    paginas_visitadas = PageView.objects.filter(
        user=user,
        page_category='tops'
    ).values('url_path').distinct().count()
    # Espera-se que existam pelo menos 8-10 páginas de tops
    return paginas_visitadas >= 8

@registrar_validador('20_visitas_tops')
def vinte_visitas_tops(user, request=None):
    """Visitou páginas de tops 20 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='tops'
    ).count() >= 20

@registrar_validador('50_visitas_tops')
def cinquenta_visitas_tops(user, request=None):
    """Visitou páginas de tops 50 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='tops'
    ).count() >= 50

# =========================== CONQUISTAS DE EXPLORAÇÃO - HEROES ===========================

@registrar_validador('primeira_visita_heroes')
def primeira_visita_heroes(user, request=None):
    """Visitou uma página de heroes pela primeira vez"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='heroes'
    ).exists()

@registrar_validador('todas_paginas_heroes')
def todas_paginas_heroes(user, request=None):
    """Visitou todas as páginas de heroes"""
    from apps.main.home.models import PageView
    # Conta quantas páginas únicas de heroes foram visitadas
    paginas_visitadas = PageView.objects.filter(
        user=user,
        page_category='heroes'
    ).values('url_path').distinct().count()
    # Espera-se que existam 3 páginas de heroes
    return paginas_visitadas >= 3

@registrar_validador('10_visitas_heroes')
def dez_visitas_heroes(user, request=None):
    """Visitou páginas de heroes 10 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='heroes'
    ).count() >= 10

@registrar_validador('25_visitas_heroes')
def vinte_cinco_visitas_heroes(user, request=None):
    """Visitou páginas de heroes 25 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='heroes'
    ).count() >= 25

# =========================== CONQUISTAS DE EXPLORAÇÃO - CASTLE SIEGE ===========================

@registrar_validador('primeira_visita_siege')
def primeira_visita_siege(user, request=None):
    """Visitou a página de Castle Siege pela primeira vez"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='siege'
    ).exists()

@registrar_validador('10_visitas_siege')
def dez_visitas_siege(user, request=None):
    """Visitou a página de Castle Siege 10 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='siege'
    ).count() >= 10

@registrar_validador('25_visitas_siege')
def vinte_cinco_visitas_siege(user, request=None):
    """Visitou a página de Castle Siege 25 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='siege'
    ).count() >= 25

# =========================== CONQUISTAS DE EXPLORAÇÃO - BOSS JEWEL LOCATIONS ===========================

@registrar_validador('primeira_visita_boss_jewel')
def primeira_visita_boss_jewel(user, request=None):
    """Visitou a página de Boss Jewel Locations pela primeira vez"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='boss_jewel'
    ).exists()

@registrar_validador('10_visitas_boss_jewel')
def dez_visitas_boss_jewel(user, request=None):
    """Visitou a página de Boss Jewel Locations 10 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='boss_jewel'
    ).count() >= 10

@registrar_validador('25_visitas_boss_jewel')
def vinte_cinco_visitas_boss_jewel(user, request=None):
    """Visitou a página de Boss Jewel Locations 25 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='boss_jewel'
    ).count() >= 25

# =========================== CONQUISTAS DE EXPLORAÇÃO - GRAND BOSS STATUS ===========================

@registrar_validador('primeira_visita_grandboss')
def primeira_visita_grandboss(user, request=None):
    """Visitou a página de Grand Boss Status pela primeira vez"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='grandboss'
    ).exists()

@registrar_validador('10_visitas_grandboss')
def dez_visitas_grandboss(user, request=None):
    """Visitou a página de Grand Boss Status 10 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='grandboss'
    ).count() >= 10

@registrar_validador('25_visitas_grandboss')
def vinte_cinco_visitas_grandboss(user, request=None):
    """Visitou a página de Grand Boss Status 25 vezes"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category='grandboss'
    ).count() >= 25

# =========================== CONQUISTAS DE EXPLORAÇÃO GERAL ===========================

@registrar_validador('explorador_iniciante')
def explorador_iniciante(user, request=None):
    """Visitou 5 páginas diferentes de exploração"""
    from apps.main.home.models import PageView
    categorias_visitadas = PageView.objects.filter(
        user=user,
        page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
    ).values('page_category').distinct().count()
    return categorias_visitadas >= 3

@registrar_validador('explorador_avancado')
def explorador_avancado(user, request=None):
    """Visitou todas as categorias de exploração"""
    from apps.main.home.models import PageView
    categorias_visitadas = PageView.objects.filter(
        user=user,
        page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
    ).values('page_category').distinct().count()
    return categorias_visitadas >= 5

@registrar_validador('explorador_mestre')
def explorador_mestre(user, request=None):
    """Visitou 50 páginas de exploração no total"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
    ).count() >= 50

@registrar_validador('explorador_legendario')
def explorador_legendario(user, request=None):
    """Visitou 100 páginas de exploração no total"""
    from apps.main.home.models import PageView
    return PageView.objects.filter(
        user=user,
        page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
    ).count() >= 100

# =========================== CONQUISTAS DE REDE SOCIAL - POSTS ===========================

@registrar_validador('primeiro_post_social')
def primeiro_post_social(user, request=None):
    """Criou o primeiro post na rede social"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user).exists()

@registrar_validador('5_posts_social')
def cinco_posts_social(user, request=None):
    """Criou 5 posts na rede social"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user).count() >= 5

@registrar_validador('10_posts_social')
def dez_posts_social(user, request=None):
    """Criou 10 posts na rede social"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user).count() >= 10

@registrar_validador('25_posts_social')
def vinte_cinco_posts_social(user, request=None):
    """Criou 25 posts na rede social"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user).count() >= 25

@registrar_validador('50_posts_social')
def cinquenta_posts_social(user, request=None):
    """Criou 50 posts na rede social"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user).count() >= 50

@registrar_validador('100_posts_social')
def cem_posts_social(user, request=None):
    """Criou 100 posts na rede social"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user).count() >= 100

@registrar_validador('primeiro_post_com_imagem')
def primeiro_post_com_imagem(user, request=None):
    """Criou o primeiro post com imagem"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, image__isnull=False).exists()

@registrar_validador('10_posts_com_imagem')
def dez_posts_com_imagem(user, request=None):
    """Criou 10 posts com imagem"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, image__isnull=False).count() >= 10

@registrar_validador('primeiro_post_com_video')
def primeiro_post_com_video(user, request=None):
    """Criou o primeiro post com vídeo"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, video__isnull=False).exists()

@registrar_validador('5_posts_com_video')
def cinco_posts_com_video(user, request=None):
    """Criou 5 posts com vídeo"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, video__isnull=False).count() >= 5

@registrar_validador('primeiro_post_fixado')
def primeiro_post_fixado(user, request=None):
    """Fixou o primeiro post no perfil"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, is_pinned=True).exists()

@registrar_validador('primeiro_post_editado')
def primeiro_post_editado(user, request=None):
    """Editou o primeiro post"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, is_edited=True).exists()

@registrar_validador('10_posts_editados')
def dez_posts_editados(user, request=None):
    """Editou 10 posts"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, is_edited=True).count() >= 10

# =========================== CONQUISTAS DE REDE SOCIAL - COMENTÁRIOS ===========================

@registrar_validador('primeiro_comentario_social')
def primeiro_comentario_social(user, request=None):
    """Fez o primeiro comentário em um post"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user).exists()

@registrar_validador('10_comentarios_social')
def dez_comentarios_social(user, request=None):
    """Fez 10 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user).count() >= 10

@registrar_validador('25_comentarios_social')
def vinte_cinco_comentarios_social(user, request=None):
    """Fez 25 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user).count() >= 25

@registrar_validador('50_comentarios_social')
def cinquenta_comentarios_social(user, request=None):
    """Fez 50 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user).count() >= 50

@registrar_validador('100_comentarios_social')
def cem_comentarios_social(user, request=None):
    """Fez 100 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user).count() >= 100

@registrar_validador('primeiro_comentario_com_imagem')
def primeiro_comentario_com_imagem(user, request=None):
    """Fez o primeiro comentário com imagem"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user, image__isnull=False).exists()

@registrar_validador('primeira_resposta_comentario')
def primeira_resposta_comentario(user, request=None):
    """Respondeu a um comentário pela primeira vez"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user, parent__isnull=False).exists()

@registrar_validador('10_respostas_comentarios')
def dez_respostas_comentarios(user, request=None):
    """Respondeu 10 comentários"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(author=user, parent__isnull=False).count() >= 10

# =========================== CONQUISTAS DE REDE SOCIAL - LIKES E REAÇÕES ===========================

@registrar_validador('primeiro_like_social')
def primeiro_like_social(user, request=None):
    """Deu o primeiro like em um post"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user).exists()

@registrar_validador('10_likes_social')
def dez_likes_social(user, request=None):
    """Deu 10 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user).count() >= 10

@registrar_validador('25_likes_social')
def vinte_cinco_likes_social(user, request=None):
    """Deu 25 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user).count() >= 25

@registrar_validador('50_likes_social')
def cinquenta_likes_social(user, request=None):
    """Deu 50 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user).count() >= 50

@registrar_validador('100_likes_social')
def cem_likes_social(user, request=None):
    """Deu 100 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user).count() >= 100

@registrar_validador('primeira_reacao_amor')
def primeira_reacao_amor(user, request=None):
    """Usou a reação de amor pela primeira vez"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user, reaction_type='love').exists()

@registrar_validador('primeira_reacao_haha')
def primeira_reacao_haha(user, request=None):
    """Usou a reação haha pela primeira vez"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user, reaction_type='haha').exists()

@registrar_validador('primeira_reacao_wow')
def primeira_reacao_wow(user, request=None):
    """Usou a reação wow pela primeira vez"""
    from apps.main.social.models import Like
    return Like.objects.filter(user=user, reaction_type='wow').exists()

@registrar_validador('todas_reacoes')
def todas_reacoes(user, request=None):
    """Usou todos os tipos de reações"""
    from apps.main.social.models import Like
    reacoes_usadas = Like.objects.filter(user=user).values_list('reaction_type', flat=True).distinct()
    return len(reacoes_usadas) >= 6  # like, love, haha, wow, sad, angry

@registrar_validador('primeiro_like_comentario')
def primeiro_like_comentario(user, request=None):
    """Deu o primeiro like em um comentário"""
    from apps.main.social.models import CommentLike
    return CommentLike.objects.filter(user=user).exists()

@registrar_validador('10_likes_comentarios')
def dez_likes_comentarios(user, request=None):
    """Deu 10 likes em comentários"""
    from apps.main.social.models import CommentLike
    return CommentLike.objects.filter(user=user).count() >= 10

# =========================== CONQUISTAS DE REDE SOCIAL - COMPARTILHAMENTOS ===========================

@registrar_validador('primeiro_compartilhamento')
def primeiro_compartilhamento(user, request=None):
    """Compartilhou o primeiro post"""
    from apps.main.social.models import Share
    return Share.objects.filter(user=user).exists()

@registrar_validador('5_compartilhamentos')
def cinco_compartilhamentos(user, request=None):
    """Compartilhou 5 posts"""
    from apps.main.social.models import Share
    return Share.objects.filter(user=user).count() >= 5

@registrar_validador('10_compartilhamentos')
def dez_compartilhamentos(user, request=None):
    """Compartilhou 10 posts"""
    from apps.main.social.models import Share
    return Share.objects.filter(user=user).count() >= 10

@registrar_validador('25_compartilhamentos')
def vinte_cinco_compartilhamentos(user, request=None):
    """Compartilhou 25 posts"""
    from apps.main.social.models import Share
    return Share.objects.filter(user=user).count() >= 25

# =========================== CONQUISTAS DE REDE SOCIAL - SEGUIR ===========================

@registrar_validador('primeiro_seguir')
def primeiro_seguir(user, request=None):
    """Seguiu o primeiro usuário"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(follower=user).exists()

@registrar_validador('5_seguindo')
def cinco_seguindo(user, request=None):
    """Está seguindo 5 usuários"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(follower=user).count() >= 5

@registrar_validador('10_seguindo')
def dez_seguindo(user, request=None):
    """Está seguindo 10 usuários"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(follower=user).count() >= 10

@registrar_validador('25_seguindo')
def vinte_cinco_seguindo(user, request=None):
    """Está seguindo 25 usuários"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(follower=user).count() >= 25

@registrar_validador('50_seguindo')
def cinquenta_seguindo(user, request=None):
    """Está seguindo 50 usuários"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(follower=user).count() >= 50

@registrar_validador('primeiro_seguidor')
def primeiro_seguidor(user, request=None):
    """Conseguiu o primeiro seguidor"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(following=user).exists()

@registrar_validador('5_seguidores')
def cinco_seguidores(user, request=None):
    """Tem 5 seguidores"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(following=user).count() >= 5

@registrar_validador('10_seguidores')
def dez_seguidores(user, request=None):
    """Tem 10 seguidores"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(following=user).count() >= 10

@registrar_validador('25_seguidores')
def vinte_cinco_seguidores(user, request=None):
    """Tem 25 seguidores"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(following=user).count() >= 25

@registrar_validador('50_seguidores')
def cinquenta_seguidores(user, request=None):
    """Tem 50 seguidores"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(following=user).count() >= 50

@registrar_validador('100_seguidores')
def cem_seguidores(user, request=None):
    """Tem 100 seguidores"""
    from apps.main.social.models import Follow
    return Follow.objects.filter(following=user).count() >= 100

# =========================== CONQUISTAS DE REDE SOCIAL - HASHTAGS ===========================

@registrar_validador('primeira_hashtag')
def primeira_hashtag(user, request=None):
    """Usou uma hashtag pela primeira vez"""
    from apps.main.social.models import PostHashtag
    return PostHashtag.objects.filter(post__author=user).exists()

@registrar_validador('5_hashtags_diferentes')
def cinco_hashtags_diferentes(user, request=None):
    """Usou 5 hashtags diferentes"""
    from apps.main.social.models import PostHashtag
    hashtags_unicas = PostHashtag.objects.filter(
        post__author=user
    ).values('hashtag').distinct().count()
    return hashtags_unicas >= 5

@registrar_validador('10_hashtags_diferentes')
def dez_hashtags_diferentes(user, request=None):
    """Usou 10 hashtags diferentes"""
    from apps.main.social.models import PostHashtag
    hashtags_unicas = PostHashtag.objects.filter(
        post__author=user
    ).values('hashtag').distinct().count()
    return hashtags_unicas >= 10

@registrar_validador('25_hashtags_diferentes')
def vinte_cinco_hashtags_diferentes(user, request=None):
    """Usou 25 hashtags diferentes"""
    from apps.main.social.models import PostHashtag
    hashtags_unicas = PostHashtag.objects.filter(
        post__author=user
    ).values('hashtag').distinct().count()
    return hashtags_unicas >= 25

@registrar_validador('50_hashtags_usadas')
def cinquenta_hashtags_usadas(user, request=None):
    """Usou hashtags em 50 posts"""
    from apps.main.social.models import PostHashtag
    return PostHashtag.objects.filter(post__author=user).count() >= 50

# =========================== CONQUISTAS DE REDE SOCIAL - ENGAJAMENTO RECEBIDO ===========================

@registrar_validador('primeiro_like_recebido')
def primeiro_like_recebido(user, request=None):
    """Recebeu o primeiro like em um post"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).exists()

@registrar_validador('10_likes_recebidos')
def dez_likes_recebidos(user, request=None):
    """Recebeu 10 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).count() >= 10

@registrar_validador('25_likes_recebidos')
def vinte_cinco_likes_recebidos(user, request=None):
    """Recebeu 25 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).count() >= 25

@registrar_validador('50_likes_recebidos')
def cinquenta_likes_recebidos(user, request=None):
    """Recebeu 50 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).count() >= 50

@registrar_validador('100_likes_recebidos')
def cem_likes_recebidos(user, request=None):
    """Recebeu 100 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).count() >= 100

@registrar_validador('250_likes_recebidos')
def duzentos_cinquenta_likes_recebidos(user, request=None):
    """Recebeu 250 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).count() >= 250

@registrar_validador('500_likes_recebidos')
def quinhentos_likes_recebidos(user, request=None):
    """Recebeu 500 likes em posts"""
    from apps.main.social.models import Like
    return Like.objects.filter(post__author=user).count() >= 500

@registrar_validador('primeiro_comentario_recebido')
def primeiro_comentario_recebido(user, request=None):
    """Recebeu o primeiro comentário em um post"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(post__author=user).exists()

@registrar_validador('10_comentarios_recebidos')
def dez_comentarios_recebidos(user, request=None):
    """Recebeu 10 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(post__author=user).count() >= 10

@registrar_validador('25_comentarios_recebidos')
def vinte_cinco_comentarios_recebidos(user, request=None):
    """Recebeu 25 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(post__author=user).count() >= 25

@registrar_validador('50_comentarios_recebidos')
def cinquenta_comentarios_recebidos(user, request=None):
    """Recebeu 50 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(post__author=user).count() >= 50

@registrar_validador('100_comentarios_recebidos')
def cem_comentarios_recebidos(user, request=None):
    """Recebeu 100 comentários em posts"""
    from apps.main.social.models import Comment
    return Comment.objects.filter(post__author=user).count() >= 100

@registrar_validador('post_10_likes')
def post_10_likes(user, request=None):
    """Tem um post com 10 ou mais likes"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, likes_count__gte=10).exists()

@registrar_validador('post_25_likes')
def post_25_likes(user, request=None):
    """Tem um post com 25 ou mais likes"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, likes_count__gte=25).exists()

@registrar_validador('post_50_likes')
def post_50_likes(user, request=None):
    """Tem um post com 50 ou mais likes"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, likes_count__gte=50).exists()

@registrar_validador('post_100_likes')
def post_100_likes(user, request=None):
    """Tem um post com 100 ou mais likes"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, likes_count__gte=100).exists()

@registrar_validador('post_viral')
def post_viral(user, request=None):
    """Tem um post com 250 ou mais likes"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, likes_count__gte=250).exists()

@registrar_validador('post_10_comentarios')
def post_10_comentarios(user, request=None):
    """Tem um post com 10 ou mais comentários"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, comments_count__gte=10).exists()

@registrar_validador('post_25_comentarios')
def post_25_comentarios(user, request=None):
    """Tem um post com 25 ou mais comentários"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, comments_count__gte=25).exists()

@registrar_validador('post_50_comentarios')
def post_50_comentarios(user, request=None):
    """Tem um post com 50 ou mais comentários"""
    from apps.main.social.models import Post
    return Post.objects.filter(author=user, comments_count__gte=50).exists()

@registrar_validador('primeiro_compartilhamento_recebido')
def primeiro_compartilhamento_recebido(user, request=None):
    """Teve um post compartilhado pela primeira vez"""
    from apps.main.social.models import Share
    return Share.objects.filter(post__author=user).exists()

@registrar_validador('10_compartilhamentos_recebidos')
def dez_compartilhamentos_recebidos(user, request=None):
    """Teve posts compartilhados 10 vezes"""
    from apps.main.social.models import Share
    return Share.objects.filter(post__author=user).count() >= 10

# =========================== CONQUISTAS DE REDE SOCIAL - PERFIL ===========================

@registrar_validador('perfil_social_completo')
def perfil_social_completo(user, request=None):
    """Completou o perfil social (tem bio e avatar)"""
    try:
        perfil = user.social_profile
        return bool(perfil.bio and perfil.avatar)
    except:
        return False

@registrar_validador('avatar_social')
def avatar_social(user, request=None):
    """Tem avatar no perfil social"""
    try:
        perfil = user.social_profile
        return bool(perfil.avatar)
    except:
        return False

@registrar_validador('bio_social')
def bio_social(user, request=None):
    """Tem biografia no perfil social"""
    try:
        perfil = user.social_profile
        return bool(perfil.bio)
    except:
        return False

@registrar_validador('imagem_capa_social')
def imagem_capa_social(user, request=None):
    """Tem imagem de capa no perfil social"""
    try:
        perfil = user.social_profile
        return bool(perfil.cover_image)
    except:
        return False

@registrar_validador('perfil_privado')
def perfil_privado(user, request=None):
    """Configurou o perfil como privado"""
    try:
        perfil = user.social_profile
        return perfil.is_private
    except:
        return False