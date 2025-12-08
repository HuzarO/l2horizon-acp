"""
Módulo para calcular o progresso das conquistas
"""
from apps.main.home.models import Conquista, ConquistaUsuario
from .validators import VALIDADORES_CONQUISTAS


def calcular_progresso_conquista(user, conquista):
    """
    Calcula o progresso de uma conquista específica para o usuário.
    
    Retorna um dicionário com:
    - completada: bool (se a conquista já foi completada)
    - progresso_atual: int (valor atual)
    - progresso_necessario: int (valor necessário)
    - progresso_percent: int (porcentagem de 0-100)
    - falta: int (quanto falta para completar)
    - descricao_progresso: str (descrição do progresso)
    """
    codigo = conquista.codigo
    
    # Verifica se já completou
    ja_completou = ConquistaUsuario.objects.filter(usuario=user, conquista=conquista).exists()
    
    if ja_completou:
        return {
            'completada': True,
            'progresso_atual': 100,
            'progresso_necessario': 100,
            'progresso_percent': 100,
            'falta': 0,
            'descricao_progresso': 'Conquista completada! ✅'
        }
    
    # Tenta calcular o progresso baseado no código
    progresso = _calcular_progresso_por_codigo(user, codigo)
    
    if progresso is None:
        # Se não conseguiu calcular, verifica se pode completar
        validador = VALIDADORES_CONQUISTAS.get(codigo)
        if validador:
            pode_completar = validador(user, request=None)
            return {
                'completada': pode_completar,
                'progresso_atual': 100 if pode_completar else 0,
                'progresso_necessario': 100,
                'progresso_percent': 100 if pode_completar else 0,
                'falta': 0 if pode_completar else 1,
                'descricao_progresso': 'Completada!' if pode_completar else 'Não completada'
            }
        return {
            'completada': False,
            'progresso_atual': 0,
            'progresso_necessario': 1,
            'progresso_percent': 0,
            'falta': 1,
            'descricao_progresso': 'Progresso não disponível'
        }
    
    return progresso


def _calcular_progresso_por_codigo(user, codigo):
    """Calcula o progresso baseado no código da conquista"""
    
    # =========================== LEILÕES ===========================
    if codigo == '10_leiloes':
        atual = user.auctions.count()
        return _criar_progresso(atual, 10, f'{atual}/10 leilões criados')
    
    if codigo == '100_leiloes':
        atual = user.auctions.count()
        return _criar_progresso(atual, 100, f'{atual}/100 leilões criados')
    
    if codigo == 'leiloeiro_profissional':
        atual = user.auctions.count()
        return _criar_progresso(atual, 25, f'{atual}/25 leilões criados')
    
    if codigo == 'leiloeiro_mestre':
        atual = user.auctions.count()
        return _criar_progresso(atual, 50, f'{atual}/50 leilões criados')
    
    # =========================== LANCES ===========================
    from apps.lineage.auction.models import Bid
    if codigo == '50_lances':
        atual = Bid.objects.filter(bidder=user).count()
        return _criar_progresso(atual, 50, f'{atual}/50 lances realizados')
    
    if codigo == '300_lances':
        atual = Bid.objects.filter(bidder=user).count()
        return _criar_progresso(atual, 300, f'{atual}/300 lances realizados')
    
    if codigo == '500_lances':
        atual = Bid.objects.filter(bidder=user).count()
        return _criar_progresso(atual, 500, f'{atual}/500 lances realizados')
    
    if codigo == 'lanceador_profissional':
        atual = Bid.objects.filter(bidder=user).count()
        return _criar_progresso(atual, 100, f'{atual}/100 lances realizados')
    
    if codigo == 'lanceador_mestre':
        atual = Bid.objects.filter(bidder=user).count()
        return _criar_progresso(atual, 200, f'{atual}/200 lances realizados')
    
    # =========================== VENCEDOR LEILÕES ===========================
    from apps.lineage.auction.models import Auction
    if codigo == 'vencedor_serie':
        atual = Auction.objects.filter(highest_bidder=user, status='finished').count()
        return _criar_progresso(atual, 3, f'{atual}/3 leilões vencidos')
    
    if codigo == 'vencedor_mestre':
        atual = Auction.objects.filter(highest_bidder=user, status='finished').count()
        return _criar_progresso(atual, 10, f'{atual}/10 leilões vencidos')
    
    if codigo == '25_vencedor_leiloes':
        atual = Auction.objects.filter(highest_bidder=user, status='finished').count()
        return _criar_progresso(atual, 25, f'{atual}/25 leilões vencidos')
    
    if codigo == '50_vencedor_leiloes':
        atual = Auction.objects.filter(highest_bidder=user, status='finished').count()
        return _criar_progresso(atual, 50, f'{atual}/50 leilões vencidos')
    
    # =========================== NÍVEIS ===========================
    if codigo in ['nivel_10', 'nivel_25', 'nivel_50', 'nivel_75', 'nivel_100']:
        try:
            perfil = user.perfilgamer
            nivel_alvo = int(codigo.split('_')[1])
            nivel_atual = perfil.level
            return _criar_progresso(nivel_atual, nivel_alvo, f'Nível {nivel_atual}/{nivel_alvo}')
        except:
            return None
    
    # =========================== XP ===========================
    if codigo in ['1000_xp', '5000_xp', '10000_xp', '25000_xp', '50000_xp', '100000_xp']:
        try:
            perfil = user.perfilgamer
            xp_total = perfil.xp
            level_atual = perfil.level
            
            # Adiciona XP de todos os níveis anteriores
            for nivel in range(1, level_atual):
                xp_total += 100 + (nivel - 1) * 25
            
            xp_alvo = int(codigo.split('_')[0])
            return _criar_progresso(xp_total, xp_alvo, f'{xp_total:,}/{xp_alvo:,} XP acumulado')
        except:
            return None
    
    # =========================== TRANSACOES ===========================
    from apps.lineage.wallet.models import TransacaoWallet, TransacaoBonus
    if codigo in ['100_transacoes', '250_transacoes', '500_transacoes', '1000_transacoes']:
        transacoes_normais = TransacaoWallet.objects.filter(wallet__usuario=user).count()
        transacoes_bonus = TransacaoBonus.objects.filter(wallet__usuario=user).count()
        atual = transacoes_normais + transacoes_bonus
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} transações realizadas')
    
    # =========================== BONUS ===========================
    if codigo in ['bonus_mestre', 'bonus_expert', '50_bonus', '100_bonus']:
        atual = TransacaoBonus.objects.filter(wallet__usuario=user, tipo='ENTRADA').count()
        alvos = {
            'bonus_mestre': 10,
            'bonus_expert': 25,
            '50_bonus': 50,
            '100_bonus': 100
        }
        alvo = alvos.get(codigo, 10)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} bônus recebidos')
    
    # =========================== COMPRAS ===========================
    from apps.lineage.shop.models import ShopPurchase
    if codigo in ['comprador_frequente', 'comprador_vip', '30_compras', '50_compras']:
        atual = ShopPurchase.objects.filter(user=user).count()
        alvos = {
            'comprador_frequente': 5,
            'comprador_vip': 15,
            '30_compras': 30,
            '50_compras': 50
        }
        alvo = alvos.get(codigo, 5)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} compras realizadas')
    
    # =========================== CUPONS ===========================
    from apps.lineage.shop.models import Cart
    if codigo in ['cupom_mestre', 'cupom_expert', '25_cupons', '50_cupons']:
        atual = Cart.objects.filter(user=user, promocao_aplicada__isnull=False).count()
        alvos = {
            'cupom_mestre': 5,
            'cupom_expert': 15,
            '25_cupons': 25,
            '50_cupons': 50
        }
        alvo = alvos.get(codigo, 5)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} cupons aplicados')
    
    # =========================== PAGAMENTOS ===========================
    from apps.lineage.payment.models import Pagamento
    if codigo in ['patrocinador_ouro', 'patrocinador_diamante', '25_pagamentos', '50_pagamentos']:
        atual = Pagamento.objects.filter(usuario=user, status='approved').count()
        alvos = {
            'patrocinador_ouro': 5,
            'patrocinador_diamante': 10,
            '25_pagamentos': 25,
            '50_pagamentos': 50
        }
        alvo = alvos.get(codigo, 5)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} pagamentos aprovados')
    
    # =========================== AMIZADES ===========================
    from apps.main.message.models import Friendship
    if codigo in ['rede_social', 'rede_social_mestre', '30_amigos', '50_amigos']:
        atual = Friendship.objects.filter(user=user, accepted=True).count()
        alvos = {
            'rede_social': 5,
            'rede_social_mestre': 15,
            '30_amigos': 30,
            '50_amigos': 50
        }
        alvo = alvos.get(codigo, 5)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} amigos aceitos')
    
    # =========================== SOLICITAÇÕES ===========================
    from apps.main.solicitation.models import Solicitation
    if codigo in ['solicitante_frequente', 'solicitante_expert', '30_solicitacoes']:
        atual = Solicitation.objects.filter(user=user).count()
        alvos = {
            'solicitante_frequente': 5,
            'solicitante_expert': 15,
            '30_solicitacoes': 30
        }
        alvo = alvos.get(codigo, 5)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} solicitações abertas')
    
    if codigo in ['resolvedor_problemas', 'resolvedor_mestre', '25_solicitacoes_resolvidas']:
        atual = Solicitation.objects.filter(user=user, status='closed').count()
        alvos = {
            'resolvedor_problemas': 3,
            'resolvedor_mestre': 10,
            '25_solicitacoes_resolvidas': 25
        }
        alvo = alvos.get(codigo, 3)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} solicitações resolvidas')
    
    # =========================== INVENTÁRIO ===========================
    from apps.lineage.inventory.models import InventoryItem, InventoryLog
    if codigo in ['colecionador_itens', 'mestre_inventario', '100_itens_inventario', '200_itens_inventario']:
        atual = InventoryItem.objects.filter(inventory__user=user).count()
        alvos = {
            'colecionador_itens': 10,
            'mestre_inventario': 50,
            '100_itens_inventario': 100,
            '200_itens_inventario': 200
        }
        alvo = alvos.get(codigo, 10)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} itens no inventário')
    
    if codigo in ['trocador_incansavel', '50_trocas_itens']:
        atual = InventoryLog.objects.filter(user=user, acao='TROCA_ENTRE_PERSONAGENS').count()
        alvos = {
            'trocador_incansavel': 10,
            '50_trocas_itens': 50
        }
        alvo = alvos.get(codigo, 10)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} trocas realizadas')
    
    if codigo in ['50_insercoes_jogo', '100_insercoes_jogo']:
        atual = InventoryLog.objects.filter(user=user, acao='INSERIU_NO_JOGO').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} inserções no jogo')
    
    # =========================== TRANSFERÊNCIAS ===========================
    if codigo in ['gerenciador_economico', '50_transferencias_jogo', '100_transferencias_jogo']:
        atual = TransacaoWallet.objects.filter(
            wallet__usuario=user,
            tipo="SAIDA",
            descricao__icontains="Transferência para o servidor"
        ).count()
        alvos = {
            'gerenciador_economico': 20,
            '50_transferencias_jogo': 50,
            '100_transferencias_jogo': 100
        }
        alvo = alvos.get(codigo, 20)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} transferências para o jogo')
    
    if codigo in ['benfeitor_comunitario', '50_transferencias_jogadores']:
        atual = TransacaoWallet.objects.filter(
            wallet__usuario=user,
            tipo="SAIDA",
            descricao__icontains="Transferência para jogador"
        ).count()
        alvos = {
            'benfeitor_comunitario': 10,
            '50_transferencias_jogadores': 50
        }
        alvo = alvos.get(codigo, 10)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} transferências para jogadores')
    
    # =========================== JOGOS - SPINS ===========================
    from apps.lineage.games.models import SpinHistory
    if codigo in ['10_spins', '50_spins', '100_spins']:
        atual = SpinHistory.objects.filter(user=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} giros na roleta')
    
    # =========================== JOGOS - CAIXAS ===========================
    from apps.lineage.games.models import Box
    if codigo in ['10_caixas_abertas', '50_caixas_abertas', '100_caixas_abertas']:
        atual = Box.objects.filter(user=user, opened=True).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} caixas abertas')
    
    # =========================== JOGOS - SLOT MACHINE ===========================
    from apps.lineage.games.models import SlotMachineHistory
    if codigo in ['10_jogadas_slot', '50_jogadas_slot', '100_jogadas_slot']:
        atual = SlotMachineHistory.objects.filter(user=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} jogadas na Slot Machine')
    
    if codigo == 'jackpot_mestre':
        atual = SlotMachineHistory.objects.filter(user=user, is_jackpot=True).count()
        return _criar_progresso(atual, 3, f'{atual}/3 jackpots ganhos')
    
    # =========================== JOGOS - DICE GAME ===========================
    from apps.lineage.games.models import DiceGameHistory
    if codigo in ['10_jogadas_dice', '50_jogadas_dice']:
        atual = DiceGameHistory.objects.filter(user=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} jogadas no Dice Game')
    
    if codigo in ['10_vitorias_dice', '50_vitorias_dice']:
        atual = DiceGameHistory.objects.filter(user=user, won=True).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} vitórias no Dice Game')
    
    # =========================== JOGOS - FISHING ===========================
    from apps.lineage.games.models import FishingHistory
    if codigo in ['10_peixes_capturados', '50_peixes_capturados', '100_peixes_capturados']:
        atual = FishingHistory.objects.filter(user=user, success=True).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} peixes capturados')
    
    from apps.lineage.games.models import FishingRod
    if codigo in ['vara_nivel_5', 'vara_nivel_10', 'vara_nivel_20']:
        try:
            rod = user.fishingrod
            nivel_atual = rod.level
            nivel_alvo = int(codigo.split('_')[2])
            return _criar_progresso(nivel_atual, nivel_alvo, f'Vara nível {nivel_atual}/{nivel_alvo}')
        except:
            return None
    
    # =========================== BATTLE PASS ===========================
    from apps.lineage.games.models import UserBattlePassProgress
    if codigo in ['battle_pass_nivel_10', 'battle_pass_nivel_25', 'battle_pass_nivel_50']:
        progress = UserBattlePassProgress.objects.filter(user=user).first()
        if not progress:
            nivel_atual = 0
        else:
            current_level = progress.get_current_level()
            nivel_atual = current_level.level if current_level else 0
        
        nivel_alvo = int(codigo.split('_')[3])
        return _criar_progresso(nivel_atual, nivel_alvo, f'Battle Pass nível {nivel_atual}/{nivel_alvo}')
    
    from apps.lineage.games.models import BattlePassQuestProgress
    if codigo in ['10_quests_battle_pass', '25_quests_battle_pass']:
        atual = BattlePassQuestProgress.objects.filter(user=user, completed=True).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} quests completadas')
    
    # =========================== DAILY BONUS ===========================
    from apps.lineage.games.models import DailyBonusClaim
    if codigo in ['daily_bonus_7dias', 'daily_bonus_30dias', 'daily_bonus_100dias']:
        atual = DailyBonusClaim.objects.filter(user=user).count()
        alvos = {
            'daily_bonus_7dias': 7,
            'daily_bonus_30dias': 30,
            'daily_bonus_100dias': 100
        }
        alvo = alvos.get(codigo, 7)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} dias de Daily Bonus')
    
    # =========================== MARKETPLACE ===========================
    from apps.lineage.marketplace.models import CharacterTransfer, MarketplaceTransaction
    if codigo in ['5_transacoes_marketplace', '10_transacoes_marketplace']:
        compras = CharacterTransfer.objects.filter(buyer=user).count()
        vendas = CharacterTransfer.objects.filter(seller=user).count()
        transacoes = MarketplaceTransaction.objects.filter(user=user).count()
        atual = compras + vendas + transacoes
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} transações no Marketplace')
    
    # =========================== BAGS ===========================
    from apps.lineage.games.models import BagItem
    if codigo in ['10_itens_bag', '50_itens_bag', '100_itens_bag']:
        atual = BagItem.objects.filter(bag__user=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} itens coletados em bags')
    
    # =========================== FEED SOCIAL ===========================
    from apps.main.home.models import PageView
    if codigo in ['10_visitas_feed', '50_visitas_feed', '100_visitas_feed']:
        atual = PageView.objects.filter(user=user, page_category='social_feed').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} visitas ao feed social')
    
    # =========================== EXPLORAÇÃO - TOPS ===========================
    if codigo in ['20_visitas_tops', '50_visitas_tops']:
        atual = PageView.objects.filter(user=user, page_category='tops').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} visitas aos tops')
    
    if codigo == '5_paginas_tops':
        atual = PageView.objects.filter(user=user, page_category='tops').values('url_path').distinct().count()
        return _criar_progresso(atual, 5, f'{atual}/5 páginas diferentes de tops visitadas')
    
    if codigo == 'todas_paginas_tops':
        atual = PageView.objects.filter(user=user, page_category='tops').values('url_path').distinct().count()
        return _criar_progresso(atual, 8, f'{atual}/8 páginas de tops visitadas')
    
    # =========================== EXPLORAÇÃO - HEROES ===========================
    if codigo in ['10_visitas_heroes', '25_visitas_heroes']:
        atual = PageView.objects.filter(user=user, page_category='heroes').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} visitas aos heroes')
    
    if codigo == 'todas_paginas_heroes':
        atual = PageView.objects.filter(user=user, page_category='heroes').values('url_path').distinct().count()
        return _criar_progresso(atual, 3, f'{atual}/3 páginas de heroes visitadas')
    
    # =========================== EXPLORAÇÃO - SIEGE ===========================
    if codigo in ['10_visitas_siege', '25_visitas_siege']:
        atual = PageView.objects.filter(user=user, page_category='siege').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} visitas ao Castle Siege')
    
    # =========================== EXPLORAÇÃO - BOSS JEWEL ===========================
    if codigo in ['10_visitas_boss_jewel', '25_visitas_boss_jewel']:
        atual = PageView.objects.filter(user=user, page_category='boss_jewel').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} visitas ao Boss Jewel Locations')
    
    # =========================== EXPLORAÇÃO - GRANDBOSS ===========================
    if codigo in ['10_visitas_grandboss', '25_visitas_grandboss']:
        atual = PageView.objects.filter(user=user, page_category='grandboss').count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} visitas ao Grand Boss Status')
    
    # =========================== EXPLORAÇÃO GERAL ===========================
    if codigo == 'explorador_iniciante':
        categorias = PageView.objects.filter(
            user=user,
            page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
        ).values('page_category').distinct().count()
        return _criar_progresso(categorias, 3, f'{categorias}/3 categorias exploradas')
    
    if codigo == 'explorador_avancado':
        categorias = PageView.objects.filter(
            user=user,
            page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
        ).values('page_category').distinct().count()
        return _criar_progresso(categorias, 5, f'{categorias}/5 categorias exploradas')
    
    if codigo in ['explorador_mestre', 'explorador_legendario']:
        atual = PageView.objects.filter(
            user=user,
            page_category__in=['tops', 'heroes', 'siege', 'boss_jewel', 'grandboss']
        ).count()
        alvos = {
            'explorador_mestre': 50,
            'explorador_legendario': 100
        }
        alvo = alvos.get(codigo, 50)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} páginas de exploração visitadas')
    
    # =========================== REDE SOCIAL - POSTS ===========================
    from apps.main.social.models import Post
    if codigo in ['5_posts_social', '10_posts_social', '25_posts_social', '50_posts_social', '100_posts_social']:
        atual = Post.objects.filter(author=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} posts criados')
    
    if codigo == '10_posts_com_imagem':
        atual = Post.objects.filter(author=user, image__isnull=False).count()
        return _criar_progresso(atual, 10, f'{atual}/10 posts com imagem')
    
    if codigo == '5_posts_com_video':
        atual = Post.objects.filter(author=user, video__isnull=False).count()
        return _criar_progresso(atual, 5, f'{atual}/5 posts com vídeo')
    
    if codigo == '10_posts_editados':
        atual = Post.objects.filter(author=user, is_edited=True).count()
        return _criar_progresso(atual, 10, f'{atual}/10 posts editados')
    
    # =========================== REDE SOCIAL - COMENTÁRIOS ===========================
    from apps.main.social.models import Comment
    if codigo in ['10_comentarios_social', '25_comentarios_social', '50_comentarios_social', '100_comentarios_social']:
        atual = Comment.objects.filter(author=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} comentários feitos')
    
    if codigo == '10_respostas_comentarios':
        atual = Comment.objects.filter(author=user, parent__isnull=False).count()
        return _criar_progresso(atual, 10, f'{atual}/10 respostas a comentários')
    
    # =========================== REDE SOCIAL - LIKES ===========================
    from apps.main.social.models import Like
    if codigo in ['10_likes_social', '25_likes_social', '50_likes_social', '100_likes_social']:
        atual = Like.objects.filter(user=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} likes dados')
    
    from apps.main.social.models import CommentLike
    if codigo == '10_likes_comentarios':
        atual = CommentLike.objects.filter(user=user).count()
        return _criar_progresso(atual, 10, f'{atual}/10 likes em comentários')
    
    # =========================== REDE SOCIAL - COMPARTILHAMENTOS ===========================
    from apps.main.social.models import Share
    if codigo in ['5_compartilhamentos', '10_compartilhamentos', '25_compartilhamentos']:
        atual = Share.objects.filter(user=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} compartilhamentos')
    
    # =========================== REDE SOCIAL - SEGUIR ===========================
    from apps.main.social.models import Follow
    if codigo in ['5_seguindo', '10_seguindo', '25_seguindo', '50_seguindo']:
        atual = Follow.objects.filter(follower=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'Seguindo {atual}/{alvo} usuários')
    
    if codigo in ['5_seguidores', '10_seguidores', '25_seguidores', '50_seguidores', '100_seguidores']:
        atual = Follow.objects.filter(following=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} seguidores')
    
    # =========================== REDE SOCIAL - HASHTAGS ===========================
    from apps.main.social.models import PostHashtag
    if codigo in ['5_hashtags_diferentes', '10_hashtags_diferentes', '25_hashtags_diferentes']:
        atual = PostHashtag.objects.filter(post__author=user).values('hashtag').distinct().count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} hashtags diferentes usadas')
    
    if codigo == '50_hashtags_usadas':
        atual = PostHashtag.objects.filter(post__author=user).count()
        return _criar_progresso(atual, 50, f'{atual}/50 hashtags usadas em posts')
    
    # =========================== REDE SOCIAL - ENGAJAMENTO RECEBIDO ===========================
    if codigo in ['10_likes_recebidos', '25_likes_recebidos', '50_likes_recebidos', '100_likes_recebidos', '250_likes_recebidos', '500_likes_recebidos']:
        atual = Like.objects.filter(post__author=user).count()
        alvos = {
            '10_likes_recebidos': 10,
            '25_likes_recebidos': 25,
            '50_likes_recebidos': 50,
            '100_likes_recebidos': 100,
            '250_likes_recebidos': 250,
            '500_likes_recebidos': 500
        }
        alvo = alvos.get(codigo, 10)
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} likes recebidos')
    
    if codigo in ['10_comentarios_recebidos', '25_comentarios_recebidos', '50_comentarios_recebidos', '100_comentarios_recebidos']:
        atual = Comment.objects.filter(post__author=user).count()
        alvo = int(codigo.split('_')[0])
        return _criar_progresso(atual, alvo, f'{atual}/{alvo} comentários recebidos')
    
    if codigo in ['post_10_likes', 'post_25_likes', 'post_50_likes', 'post_100_likes', 'post_viral']:
        from django.db.models import Max
        alvos = {
            'post_10_likes': 10,
            'post_25_likes': 25,
            'post_50_likes': 50,
            'post_100_likes': 100,
            'post_viral': 250
        }
        alvo = alvos.get(codigo, 10)
        posts_com_likes = Post.objects.filter(author=user, likes_count__gte=alvo)
        tem_post = posts_com_likes.exists()
        if tem_post:
            maior_likes = posts_com_likes.order_by('-likes_count').first().likes_count
            return _criar_progresso(maior_likes, alvo, f'Post com {maior_likes} likes (meta: {alvo})')
        else:
            maior_likes = Post.objects.filter(author=user).aggregate(max_likes=Max('likes_count'))['max_likes'] or 0
            return _criar_progresso(maior_likes, alvo, f'Maior post tem {maior_likes} likes (meta: {alvo})')
    
    if codigo in ['post_10_comentarios', 'post_25_comentarios', 'post_50_comentarios']:
        from django.db.models import Max
        alvos = {
            'post_10_comentarios': 10,
            'post_25_comentarios': 25,
            'post_50_comentarios': 50
        }
        alvo = alvos.get(codigo, 10)
        posts_com_comentarios = Post.objects.filter(author=user, comments_count__gte=alvo)
        tem_post = posts_com_comentarios.exists()
        if tem_post:
            maior_comentarios = posts_com_comentarios.order_by('-comments_count').first().comments_count
            return _criar_progresso(maior_comentarios, alvo, f'Post com {maior_comentarios} comentários (meta: {alvo})')
        else:
            maior_comentarios = Post.objects.filter(author=user).aggregate(max_comentarios=Max('comments_count'))['max_comentarios'] or 0
            return _criar_progresso(maior_comentarios, alvo, f'Maior post tem {maior_comentarios} comentários (meta: {alvo})')
    
    if codigo == '10_compartilhamentos_recebidos':
        atual = Share.objects.filter(post__author=user).count()
        return _criar_progresso(atual, 10, f'{atual}/10 compartilhamentos recebidos')
    
    return None


def _criar_progresso(atual, necessario, descricao):
    """Cria um dicionário de progresso padronizado"""
    if atual >= necessario:
        return {
            'completada': True,
            'progresso_atual': necessario,
            'progresso_necessario': necessario,
            'progresso_percent': 100,
            'falta': 0,
            'descricao_progresso': descricao
        }
    
    percent = min(100, int((atual / necessario) * 100)) if necessario > 0 else 0
    falta = necessario - atual
    
    return {
        'completada': False,
        'progresso_atual': atual,
        'progresso_necessario': necessario,
        'progresso_percent': percent,
        'falta': falta,
        'descricao_progresso': descricao
    }

