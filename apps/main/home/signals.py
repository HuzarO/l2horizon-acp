from django.db import connection
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import PerfilGamer, Conquista


@receiver(post_migrate)
def populate_initial_data(sender, **kwargs):
    if sender.name == 'apps.main.home':  # Verifica se o aplicativo é o seu
        # Caminho para os arquivos SQL
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_sql_file = os.path.join(base_dir, 'home/sql', 'home_state.sql')
        city_sql_file = os.path.join(base_dir, 'home/sql', 'home_city.sql')

        with connection.cursor() as cursor:
            # Verifica se a tabela State está vazia e popula se necessário
            cursor.execute("SELECT COUNT(*) FROM home_state;")
            if cursor.fetchone()[0] == 0:
                with open(state_sql_file, 'r', encoding='utf-8') as file:  # Adiciona encoding='utf-8'
                    sql = file.read()
                    cursor.execute(sql)

            # Verifica se a tabela City está vazia e popula se necessário
            cursor.execute("SELECT COUNT(*) FROM home_city;")
            if cursor.fetchone()[0] == 0:
                with open(city_sql_file, 'r', encoding='utf-8') as file:  # Adiciona encoding='utf-8'
                    sql = file.read()
                    cursor.execute(sql)


@receiver(post_save, sender=User)
def criar_perfil_gamer(sender, instance, created, **kwargs):
    if created:
        PerfilGamer.objects.create(user=instance)


@receiver(post_migrate)
def criar_conquistas_iniciais(sender, **kwargs):
    # Cria as conquistas iniciais, caso não existam
    conquistas = [
        {'codigo': 'primeiro_login', 'nome': 'Primeiro Login', 'descricao': 'Realizou o primeiro login no sistema'},
        {'codigo': '10_leiloes', 'nome': '10 Leilões', 'descricao': 'Criou 10 leilões no sistema'},
        {'codigo': 'primeira_solicitacao', 'nome': 'Primeira Solicitação', 'descricao': 'Fez sua primeira solicitação'},
        {'codigo': 'avatar_editado', 'nome': 'Avatar Editado', 'descricao': 'Editou seu avatar pela primeira vez'},
        {'codigo': 'endereco_cadastrado', 'nome': 'Endereço Cadastrado', 'descricao': 'Cadastrou seu endereço'},
        {'codigo': 'email_verificado', 'nome': 'Email Verificado', 'descricao': 'Verificou seu e-mail'},
        {'codigo': '2fa_ativado', 'nome': '2FA Ativado', 'descricao': 'Ativou a autenticação de dois fatores (2FA)'},
        {'codigo': 'idioma_trocado', 'nome': 'Idioma Trocado', 'descricao': 'Alterou o idioma do perfil'},
        {'codigo': 'primeiro_amigo', 'nome': 'Primeiro Amigo', 'descricao': 'Fez seu primeiro pedido de amizade'},
        {'codigo': 'primeiro_amigo_aceito', 'nome': 'Primeiro Amigo Aceito', 'descricao': 'Aceitou seu primeiro pedido de amizade'},
        {'codigo': 'primeira_compra', 'nome': 'Primeira Compra', 'descricao': 'Realizou sua primeira compra na loja'},
        {'codigo': 'primeiro_lance', 'nome': 'Primeiro Lance', 'descricao': 'Realizou seu primeiro lance em um leilão'},
        {'codigo': 'primeiro_cupom', 'nome': 'Primeiro Cupom', 'descricao': 'Aplicou um código promocional pela primeira vez'},
        {'codigo': 'primeiro_pedido_pagamento', 'nome': 'Primeira Contribuição', 'descricao': 'Iniciou sua primeira contribuição para o servidor'},
        {'codigo': 'primeiro_pagamento_concluido', 'nome': 'Patrocinador Oficial', 'descricao': 'Realizou seu primeiro apoio financeiro ao servidor'},
        {'codigo': 'primeira_transferencia_para_o_jogo', 'nome': 'Mestre da Economia', 'descricao': 'Realizou sua primeira transferência de moedas para o personagem no servidor'},
        {'codigo': 'primeira_transferencia_para_jogador', 'nome': 'Aliado Generoso', 'descricao': 'Enviou moedas para outro jogador pela primeira vez'},
        {'codigo': 'primeira_retirada_item', 'nome': 'Caçador de Tesouros', 'descricao': 'Retirou seu primeiro item do jogo para o inventário online'},
        {'codigo': 'primeira_insercao_item', 'nome': 'De Volta à Batalha', 'descricao': 'Inseriu um item do inventário online no servidor pela primeira vez'},
        {'codigo': 'primeira_troca_itens', 'nome': 'Comerciante Astuto', 'descricao': 'Realizou sua primeira troca de item entre personagens'},
        {'codigo': 'nivel_10', 'nome': 'Veterano Iniciante', 'descricao': 'Alcançou o nível 10 no sistema'},
        {'codigo': '50_lances', 'nome': 'Lanceador Experiente', 'descricao': 'Realizou 50 lances em leilões'},
        {'codigo': 'primeiro_vencedor_leilao', 'nome': 'Vencedor de Leilão', 'descricao': 'Venceu seu primeiro leilão'},
        {'codigo': '1000_xp', 'nome': 'Mestre da Experiência', 'descricao': 'Acumulou 1000 pontos de experiência'},
        {'codigo': '100_transacoes', 'nome': 'Mestre das Transações', 'descricao': 'Realizou 100 transações na carteira'},
        {'codigo': 'primeiro_bonus', 'nome': 'Bônus Recebido', 'descricao': 'Recebeu seu primeiro bônus de compra'},
        {'codigo': 'nivel_25', 'nome': 'Veterano Avançado', 'descricao': 'Alcançou o nível 25 no sistema'},
        {'codigo': 'primeira_solicitacao_resolvida', 'nome': 'Problema Resolvido', 'descricao': 'Teve sua primeira solicitação de suporte resolvida'},
        {'codigo': 'colecionador_itens', 'nome': 'Colecionador de Itens', 'descricao': 'Possui 10 ou mais itens no inventário'},
        {'codigo': 'mestre_inventario', 'nome': 'Mestre do Inventário', 'descricao': 'Possui 50 ou mais itens no inventário'},
        {'codigo': 'trocador_incansavel', 'nome': 'Trocador Incansável', 'descricao': 'Realizou 10 ou mais trocas de itens'},
        {'codigo': 'gerenciador_economico', 'nome': 'Gerenciador Econômico', 'descricao': 'Realizou 20 ou mais transferências para o jogo'},
        {'codigo': 'benfeitor_comunitario', 'nome': 'Benfeitor Comunitário', 'descricao': 'Realizou 10 ou mais transferências para outros jogadores'},
        {'codigo': '250_transacoes', 'nome': 'Mestre das Transações', 'descricao': 'Realizou 250 transações na carteira'},
        {'codigo': '500_transacoes', 'nome': 'Expert das Transações', 'descricao': 'Realizou 500 transações na carteira'},
        {'codigo': 'bonus_diario_7dias', 'nome': 'Fiel ao Bônus', 'descricao': 'Recebeu bônus diário por 7 dias consecutivos'},
        {'codigo': 'bonus_diario_30dias', 'nome': 'Viciado no Bônus', 'descricao': 'Recebeu bônus diário por 30 dias consecutivos'},
        {'codigo': 'bonus_mestre', 'nome': 'Mestre dos Bônus', 'descricao': 'Recebeu 10 ou mais bônus'},
        {'codigo': 'bonus_expert', 'nome': 'Expert dos Bônus', 'descricao': 'Recebeu 25 ou mais bônus'},
        {'codigo': 'patrocinador_ouro', 'nome': 'Patrocinador Ouro', 'descricao': 'Realizou 5 ou mais pagamentos aprovados'},
        {'codigo': 'patrocinador_diamante', 'nome': 'Patrocinador Diamante', 'descricao': 'Realizou 10 ou mais pagamentos aprovados'},
        {'codigo': 'comprador_frequente', 'nome': 'Comprador Frequente', 'descricao': 'Realizou 5 ou mais compras na loja'},
        {'codigo': 'comprador_vip', 'nome': 'Comprador VIP', 'descricao': 'Realizou 15 ou mais compras na loja'},
        {'codigo': 'leiloeiro_profissional', 'nome': 'Leiloeiro Profissional', 'descricao': 'Criou 25 ou mais leilões'},
        {'codigo': 'leiloeiro_mestre', 'nome': 'Leiloeiro Mestre', 'descricao': 'Criou 50 ou mais leilões'},
        {'codigo': 'lanceador_profissional', 'nome': 'Lanceador Profissional', 'descricao': 'Realizou 100 ou mais lances'},
        {'codigo': 'lanceador_mestre', 'nome': 'Lanceador Mestre', 'descricao': 'Realizou 200 ou mais lances'},
        {'codigo': 'vencedor_serie', 'nome': 'Vencedor em Série', 'descricao': 'Venceu 3 ou mais leilões'},
        {'codigo': 'vencedor_mestre', 'nome': 'Vencedor Mestre', 'descricao': 'Venceu 10 ou mais leilões'},
        {'codigo': 'cupom_mestre', 'nome': 'Mestre dos Cupons', 'descricao': 'Aplicou 5 ou mais cupons promocionais'},
        {'codigo': 'cupom_expert', 'nome': 'Expert dos Cupons', 'descricao': 'Aplicou 15 ou mais cupons promocionais'},
        {'codigo': 'solicitante_frequente', 'nome': 'Solicitante Frequente', 'descricao': 'Abriu 5 ou mais solicitações de suporte'},
        {'codigo': 'solicitante_expert', 'nome': 'Solicitante Expert', 'descricao': 'Abriu 15 ou mais solicitações de suporte'},
        {'codigo': 'resolvedor_problemas', 'nome': 'Resolvedor de Problemas', 'descricao': 'Teve 3 ou mais solicitações resolvidas'},
        {'codigo': 'resolvedor_mestre', 'nome': 'Resolvedor Mestre', 'descricao': 'Teve 10 ou mais solicitações resolvidas'},
        {'codigo': 'rede_social', 'nome': 'Rede Social', 'descricao': 'Tem 5 ou mais amigos aceitos'},
        {'codigo': 'rede_social_mestre', 'nome': 'Mestre da Rede Social', 'descricao': 'Tem 15 ou mais amigos aceitos'},
        {'codigo': 'nivel_50', 'nome': 'Veterano Experiente', 'descricao': 'Alcançou o nível 50 no sistema'},
        {'codigo': 'nivel_75', 'nome': 'Veterano Mestre', 'descricao': 'Alcançou o nível 75 no sistema'},
        {'codigo': 'nivel_100', 'nome': 'Lenda do Sistema', 'descricao': 'Alcançou o nível 100 no sistema'},
        {'codigo': '5000_xp', 'nome': 'Mestre da Experiência', 'descricao': 'Acumulou 5000 pontos de experiência'},
        {'codigo': '10000_xp', 'nome': 'Lenda da Experiência', 'descricao': 'Acumulou 10000 pontos de experiência'},
        
        # =========================== CONQUISTAS DE JOGOS ===========================
        {'codigo': 'primeiro_spin', 'nome': 'Primeiro Giro', 'descricao': 'Realizou o primeiro giro na roleta'},
        {'codigo': '10_spins', 'nome': '10 Giros', 'descricao': 'Realizou 10 giros na roleta'},
        {'codigo': '50_spins', 'nome': '50 Giros', 'descricao': 'Realizou 50 giros na roleta'},
        {'codigo': '100_spins', 'nome': '100 Giros', 'descricao': 'Realizou 100 giros na roleta'},
        {'codigo': 'primeiro_premio_roleta', 'nome': 'Primeiro Prêmio', 'descricao': 'Ganhou o primeiro prêmio na roleta'},
        {'codigo': 'primeira_caixa_aberta', 'nome': 'Primeira Caixa', 'descricao': 'Abriu a primeira caixa'},
        {'codigo': '10_caixas_abertas', 'nome': '10 Caixas Abertas', 'descricao': 'Abriu 10 caixas'},
        {'codigo': '50_caixas_abertas', 'nome': '50 Caixas Abertas', 'descricao': 'Abriu 50 caixas'},
        {'codigo': '100_caixas_abertas', 'nome': '100 Caixas Abertas', 'descricao': 'Abriu 100 caixas'},
        {'codigo': 'item_epico_caixa', 'nome': 'Item Épico', 'descricao': 'Obteve um item épico de uma caixa'},
        {'codigo': 'item_lendario_caixa', 'nome': 'Item Lendário', 'descricao': 'Obteve um item lendário de uma caixa'},
        {'codigo': 'primeira_jogada_slot', 'nome': 'Primeira Jogada Slot', 'descricao': 'Realizou a primeira jogada na Slot Machine'},
        {'codigo': '10_jogadas_slot', 'nome': '10 Jogadas Slot', 'descricao': 'Realizou 10 jogadas na Slot Machine'},
        {'codigo': '50_jogadas_slot', 'nome': '50 Jogadas Slot', 'descricao': 'Realizou 50 jogadas na Slot Machine'},
        {'codigo': '100_jogadas_slot', 'nome': '100 Jogadas Slot', 'descricao': 'Realizou 100 jogadas na Slot Machine'},
        {'codigo': 'primeiro_jackpot', 'nome': 'Primeiro Jackpot', 'descricao': 'Ganhou o primeiro jackpot na Slot Machine'},
        {'codigo': 'jackpot_mestre', 'nome': 'Mestre do Jackpot', 'descricao': 'Ganhou 3 ou mais jackpots'},
        {'codigo': 'primeira_jogada_dice', 'nome': 'Primeira Jogada Dice', 'descricao': 'Realizou a primeira jogada no Dice Game'},
        {'codigo': '10_jogadas_dice', 'nome': '10 Jogadas Dice', 'descricao': 'Realizou 10 jogadas no Dice Game'},
        {'codigo': '50_jogadas_dice', 'nome': '50 Jogadas Dice', 'descricao': 'Realizou 50 jogadas no Dice Game'},
        {'codigo': 'primeira_vitoria_dice', 'nome': 'Primeira Vitória Dice', 'descricao': 'Ganhou a primeira aposta no Dice Game'},
        {'codigo': '10_vitorias_dice', 'nome': '10 Vitórias Dice', 'descricao': 'Ganhou 10 apostas no Dice Game'},
        {'codigo': '50_vitorias_dice', 'nome': '50 Vitórias Dice', 'descricao': 'Ganhou 50 apostas no Dice Game'},
        {'codigo': 'primeira_pescaria', 'nome': 'Primeira Pescaria', 'descricao': 'Realizou a primeira pescaria'},
        {'codigo': '10_peixes_capturados', 'nome': '10 Peixes Capturados', 'descricao': 'Capturou 10 peixes'},
        {'codigo': '50_peixes_capturados', 'nome': '50 Peixes Capturados', 'descricao': 'Capturou 50 peixes'},
        {'codigo': '100_peixes_capturados', 'nome': '100 Peixes Capturados', 'descricao': 'Capturou 100 peixes'},
        {'codigo': 'peixe_raro', 'nome': 'Peixe Raro', 'descricao': 'Capturou um peixe raro'},
        {'codigo': 'peixe_epico', 'nome': 'Peixe Épico', 'descricao': 'Capturou um peixe épico'},
        {'codigo': 'peixe_lendario', 'nome': 'Peixe Lendário', 'descricao': 'Capturou um peixe lendário'},
        {'codigo': 'vara_nivel_5', 'nome': 'Vara Nível 5', 'descricao': 'Alcançou o nível 5 na vara de pesca'},
        {'codigo': 'vara_nivel_10', 'nome': 'Vara Nível 10', 'descricao': 'Alcançou o nível 10 na vara de pesca'},
        {'codigo': 'vara_nivel_20', 'nome': 'Vara Nível 20', 'descricao': 'Alcançou o nível 20 na vara de pesca'},
        
        # =========================== CONQUISTAS DE BATTLE PASS ===========================
        {'codigo': 'primeiro_battle_pass', 'nome': 'Primeiro Battle Pass', 'descricao': 'Participou do primeiro Battle Pass'},
        {'codigo': 'battle_pass_nivel_10', 'nome': 'Battle Pass Nível 10', 'descricao': 'Alcançou o nível 10 no Battle Pass'},
        {'codigo': 'battle_pass_nivel_25', 'nome': 'Battle Pass Nível 25', 'descricao': 'Alcançou o nível 25 no Battle Pass'},
        {'codigo': 'battle_pass_nivel_50', 'nome': 'Battle Pass Nível 50', 'descricao': 'Alcançou o nível 50 no Battle Pass'},
        {'codigo': 'primeira_quest_battle_pass', 'nome': 'Primeira Quest', 'descricao': 'Completou a primeira quest do Battle Pass'},
        {'codigo': '10_quests_battle_pass', 'nome': '10 Quests Completas', 'descricao': 'Completou 10 quests do Battle Pass'},
        {'codigo': '25_quests_battle_pass', 'nome': '25 Quests Completas', 'descricao': 'Completou 25 quests do Battle Pass'},
        {'codigo': 'primeiro_milestone_battle_pass', 'nome': 'Primeiro Milestone', 'descricao': 'Alcançou o primeiro milestone do Battle Pass'},
        {'codigo': 'battle_pass_premium', 'nome': 'Battle Pass Premium', 'descricao': 'Comprou o Battle Pass Premium'},
        
        # =========================== CONQUISTAS DE DAILY BONUS ===========================
        {'codigo': 'primeiro_daily_bonus', 'nome': 'Primeiro Daily Bonus', 'descricao': 'Recebeu o primeiro Daily Bonus'},
        {'codigo': 'daily_bonus_7dias', 'nome': 'Daily Bonus 7 Dias', 'descricao': 'Recebeu Daily Bonus por 7 dias'},
        {'codigo': 'daily_bonus_30dias', 'nome': 'Daily Bonus 30 Dias', 'descricao': 'Recebeu Daily Bonus por 30 dias'},
        {'codigo': 'daily_bonus_100dias', 'nome': 'Daily Bonus 100 Dias', 'descricao': 'Recebeu Daily Bonus por 100 dias'},
        
        # =========================== CONQUISTAS DE MARKETPLACE ===========================
        {'codigo': 'primeira_transacao_marketplace', 'nome': 'Primeira Transação', 'descricao': 'Realizou a primeira transação no Marketplace'},
        {'codigo': '5_transacoes_marketplace', 'nome': '5 Transações Marketplace', 'descricao': 'Realizou 5 ou mais transações no Marketplace'},
        {'codigo': '10_transacoes_marketplace', 'nome': '10 Transações Marketplace', 'descricao': 'Realizou 10 ou mais transações no Marketplace'},
        {'codigo': 'primeira_transferencia_personagem', 'nome': 'Primeira Transferência', 'descricao': 'Realizou a primeira transferência de personagem'},
        
        # =========================== CONQUISTAS DE BAGS ===========================
        {'codigo': 'primeira_bag', 'nome': 'Primeira Bag', 'descricao': 'Obteve a primeira bag'},
        {'codigo': '10_itens_bag', 'nome': '10 Itens em Bags', 'descricao': 'Coletou 10 ou mais itens em bags'},
        {'codigo': '50_itens_bag', 'nome': '50 Itens em Bags', 'descricao': 'Coletou 50 ou mais itens em bags'},
        {'codigo': '100_itens_bag', 'nome': '100 Itens em Bags', 'descricao': 'Coletou 100 ou mais itens em bags'},
        
        # =========================== CONQUISTAS ADICIONAIS DE INVENTÁRIO ===========================
        {'codigo': '100_itens_inventario', 'nome': '100 Itens no Inventário', 'descricao': 'Possui 100 ou mais itens no inventário'},
        {'codigo': '200_itens_inventario', 'nome': '200 Itens no Inventário', 'descricao': 'Possui 200 ou mais itens no inventário'},
        {'codigo': '50_insercoes_jogo', 'nome': '50 Inserções', 'descricao': 'Inseriu 50 ou mais itens no jogo'},
        {'codigo': '100_insercoes_jogo', 'nome': '100 Inserções', 'descricao': 'Inseriu 100 ou mais itens no jogo'},
        {'codigo': '50_trocas_itens', 'nome': '50 Trocas', 'descricao': 'Realizou 50 ou mais trocas de itens'},
        
        # =========================== CONQUISTAS ADICIONAIS DE XP ===========================
        {'codigo': '25000_xp', 'nome': '25000 XP', 'descricao': 'Acumulou 25000 pontos de experiência'},
        {'codigo': '50000_xp', 'nome': '50000 XP', 'descricao': 'Acumulou 50000 pontos de experiência'},
        {'codigo': '100000_xp', 'nome': '100000 XP', 'descricao': 'Acumulou 100000 pontos de experiência'},
        
        # =========================== CONQUISTAS ADICIONAIS DE TRANSFERÊNCIAS ===========================
        {'codigo': '50_transferencias_jogo', 'nome': '50 Transferências para Jogo', 'descricao': 'Realizou 50 ou mais transferências para o jogo'},
        {'codigo': '100_transferencias_jogo', 'nome': '100 Transferências para Jogo', 'descricao': 'Realizou 100 ou mais transferências para o jogo'},
        {'codigo': '50_transferencias_jogadores', 'nome': '50 Transferências para Jogadores', 'descricao': 'Realizou 50 ou mais transferências para outros jogadores'},
        
        # =========================== CONQUISTAS ADICIONAIS DE LEILÕES ===========================
        {'codigo': '100_leiloes', 'nome': '100 Leilões', 'descricao': 'Criou 100 ou mais leilões'},
        {'codigo': '300_lances', 'nome': '300 Lances', 'descricao': 'Realizou 300 ou mais lances'},
        {'codigo': '500_lances', 'nome': '500 Lances', 'descricao': 'Realizou 500 ou mais lances'},
        {'codigo': '25_vencedor_leiloes', 'nome': '25 Vitórias em Leilões', 'descricao': 'Venceu 25 ou mais leilões'},
        {'codigo': '50_vencedor_leiloes', 'nome': '50 Vitórias em Leilões', 'descricao': 'Venceu 50 ou mais leilões'},
        
        # =========================== CONQUISTAS ADICIONAIS DE COMPRAS ===========================
        {'codigo': '30_compras', 'nome': '30 Compras', 'descricao': 'Realizou 30 ou mais compras na loja'},
        {'codigo': '50_compras', 'nome': '50 Compras', 'descricao': 'Realizou 50 ou mais compras na loja'},
        {'codigo': '25_cupons', 'nome': '25 Cupons', 'descricao': 'Aplicou 25 ou mais cupons promocionais'},
        {'codigo': '50_cupons', 'nome': '50 Cupons', 'descricao': 'Aplicou 50 ou mais cupons promocionais'},
        
        # =========================== CONQUISTAS ADICIONAIS DE PAGAMENTOS ===========================
        {'codigo': '25_pagamentos', 'nome': '25 Pagamentos', 'descricao': 'Realizou 25 ou mais pagamentos aprovados'},
        {'codigo': '50_pagamentos', 'nome': '50 Pagamentos', 'descricao': 'Realizou 50 ou mais pagamentos aprovados'},
        
        # =========================== CONQUISTAS ADICIONAIS DE AMIZADES ===========================
        {'codigo': '30_amigos', 'nome': '30 Amigos', 'descricao': 'Tem 30 ou mais amigos aceitos'},
        {'codigo': '50_amigos', 'nome': '50 Amigos', 'descricao': 'Tem 50 ou mais amigos aceitos'},
        
        # =========================== CONQUISTAS ADICIONAIS DE SOLICITAÇÕES ===========================
        {'codigo': '30_solicitacoes', 'nome': '30 Solicitações', 'descricao': 'Abriu 30 ou mais solicitações de suporte'},
        {'codigo': '25_solicitacoes_resolvidas', 'nome': '25 Solicitações Resolvidas', 'descricao': 'Teve 25 ou mais solicitações resolvidas'},
        
        # =========================== CONQUISTAS ADICIONAIS DE TRANSACOES ===========================
        {'codigo': '1000_transacoes', 'nome': '1000 Transações', 'descricao': 'Realizou 1000 transações na carteira'},
        {'codigo': '50_bonus', 'nome': '50 Bônus', 'descricao': 'Recebeu 50 ou mais bônus'},
        {'codigo': '100_bonus', 'nome': '100 Bônus', 'descricao': 'Recebeu 100 ou mais bônus'},
        
        # =========================== CONQUISTAS DE FEED SOCIAL ===========================
        {'codigo': 'primeira_visita_feed', 'nome': 'Primeira Visita ao Feed', 'descricao': 'Visitou o feed social pela primeira vez'},
        {'codigo': '10_visitas_feed', 'nome': '10 Visitas ao Feed', 'descricao': 'Visitou o feed social 10 vezes'},
        {'codigo': '50_visitas_feed', 'nome': '50 Visitas ao Feed', 'descricao': 'Visitou o feed social 50 vezes'},
        {'codigo': '100_visitas_feed', 'nome': '100 Visitas ao Feed', 'descricao': 'Visitou o feed social 100 vezes'},
        
        # =========================== CONQUISTAS DE EXPLORAÇÃO - TOPS ===========================
        {'codigo': 'primeira_visita_tops', 'nome': 'Primeira Visita aos Tops', 'descricao': 'Visitou uma página de tops pela primeira vez'},
        {'codigo': '5_paginas_tops', 'nome': '5 Páginas de Tops', 'descricao': 'Visitou 5 páginas diferentes de tops'},
        {'codigo': 'todas_paginas_tops', 'nome': 'Todas as Páginas de Tops', 'descricao': 'Visitou todas as páginas de tops'},
        {'codigo': '20_visitas_tops', 'nome': '20 Visitas aos Tops', 'descricao': 'Visitou páginas de tops 20 vezes'},
        {'codigo': '50_visitas_tops', 'nome': '50 Visitas aos Tops', 'descricao': 'Visitou páginas de tops 50 vezes'},
        
        # =========================== CONQUISTAS DE EXPLORAÇÃO - HEROES ===========================
        {'codigo': 'primeira_visita_heroes', 'nome': 'Primeira Visita aos Heroes', 'descricao': 'Visitou uma página de heroes pela primeira vez'},
        {'codigo': 'todas_paginas_heroes', 'nome': 'Todas as Páginas de Heroes', 'descricao': 'Visitou todas as páginas de heroes'},
        {'codigo': '10_visitas_heroes', 'nome': '10 Visitas aos Heroes', 'descricao': 'Visitou páginas de heroes 10 vezes'},
        {'codigo': '25_visitas_heroes', 'nome': '25 Visitas aos Heroes', 'descricao': 'Visitou páginas de heroes 25 vezes'},
        
        # =========================== CONQUISTAS DE EXPLORAÇÃO - CASTLE SIEGE ===========================
        {'codigo': 'primeira_visita_siege', 'nome': 'Primeira Visita ao Castle Siege', 'descricao': 'Visitou a página de Castle Siege pela primeira vez'},
        {'codigo': '10_visitas_siege', 'nome': '10 Visitas ao Castle Siege', 'descricao': 'Visitou a página de Castle Siege 10 vezes'},
        {'codigo': '25_visitas_siege', 'nome': '25 Visitas ao Castle Siege', 'descricao': 'Visitou a página de Castle Siege 25 vezes'},
        
        # =========================== CONQUISTAS DE EXPLORAÇÃO - BOSS JEWEL LOCATIONS ===========================
        {'codigo': 'primeira_visita_boss_jewel', 'nome': 'Primeira Visita Boss Jewel', 'descricao': 'Visitou a página de Boss Jewel Locations pela primeira vez'},
        {'codigo': '10_visitas_boss_jewel', 'nome': '10 Visitas Boss Jewel', 'descricao': 'Visitou a página de Boss Jewel Locations 10 vezes'},
        {'codigo': '25_visitas_boss_jewel', 'nome': '25 Visitas Boss Jewel', 'descricao': 'Visitou a página de Boss Jewel Locations 25 vezes'},
        
        # =========================== CONQUISTAS DE EXPLORAÇÃO - GRAND BOSS STATUS ===========================
        {'codigo': 'primeira_visita_grandboss', 'nome': 'Primeira Visita Grand Boss', 'descricao': 'Visitou a página de Grand Boss Status pela primeira vez'},
        {'codigo': '10_visitas_grandboss', 'nome': '10 Visitas Grand Boss', 'descricao': 'Visitou a página de Grand Boss Status 10 vezes'},
        {'codigo': '25_visitas_grandboss', 'nome': '25 Visitas Grand Boss', 'descricao': 'Visitou a página de Grand Boss Status 25 vezes'},
        
        # =========================== CONQUISTAS DE EXPLORAÇÃO GERAL ===========================
        {'codigo': 'explorador_iniciante', 'nome': 'Explorador Iniciante', 'descricao': 'Visitou 5 páginas diferentes de exploração'},
        {'codigo': 'explorador_avancado', 'nome': 'Explorador Avançado', 'descricao': 'Visitou todas as categorias de exploração'},
        {'codigo': 'explorador_mestre', 'nome': 'Explorador Mestre', 'descricao': 'Visitou 50 páginas de exploração no total'},
        {'codigo': 'explorador_legendario', 'nome': 'Explorador Lendário', 'descricao': 'Visitou 100 páginas de exploração no total'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - POSTS ===========================
        {'codigo': 'primeiro_post_social', 'nome': 'Primeiro Post', 'descricao': 'Criou o primeiro post na rede social'},
        {'codigo': '5_posts_social', 'nome': '5 Posts', 'descricao': 'Criou 5 posts na rede social'},
        {'codigo': '10_posts_social', 'nome': '10 Posts', 'descricao': 'Criou 10 posts na rede social'},
        {'codigo': '25_posts_social', 'nome': '25 Posts', 'descricao': 'Criou 25 posts na rede social'},
        {'codigo': '50_posts_social', 'nome': '50 Posts', 'descricao': 'Criou 50 posts na rede social'},
        {'codigo': '100_posts_social', 'nome': '100 Posts', 'descricao': 'Criou 100 posts na rede social'},
        {'codigo': 'primeiro_post_com_imagem', 'nome': 'Primeiro Post com Imagem', 'descricao': 'Criou o primeiro post com imagem'},
        {'codigo': '10_posts_com_imagem', 'nome': '10 Posts com Imagem', 'descricao': 'Criou 10 posts com imagem'},
        {'codigo': 'primeiro_post_com_video', 'nome': 'Primeiro Post com Vídeo', 'descricao': 'Criou o primeiro post com vídeo'},
        {'codigo': '5_posts_com_video', 'nome': '5 Posts com Vídeo', 'descricao': 'Criou 5 posts com vídeo'},
        {'codigo': 'primeiro_post_fixado', 'nome': 'Primeiro Post Fixado', 'descricao': 'Fixou o primeiro post no perfil'},
        {'codigo': 'primeiro_post_editado', 'nome': 'Primeiro Post Editado', 'descricao': 'Editou o primeiro post'},
        {'codigo': '10_posts_editados', 'nome': '10 Posts Editados', 'descricao': 'Editou 10 posts'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - COMENTÁRIOS ===========================
        {'codigo': 'primeiro_comentario_social', 'nome': 'Primeiro Comentário', 'descricao': 'Fez o primeiro comentário em um post'},
        {'codigo': '10_comentarios_social', 'nome': '10 Comentários', 'descricao': 'Fez 10 comentários em posts'},
        {'codigo': '25_comentarios_social', 'nome': '25 Comentários', 'descricao': 'Fez 25 comentários em posts'},
        {'codigo': '50_comentarios_social', 'nome': '50 Comentários', 'descricao': 'Fez 50 comentários em posts'},
        {'codigo': '100_comentarios_social', 'nome': '100 Comentários', 'descricao': 'Fez 100 comentários em posts'},
        {'codigo': 'primeiro_comentario_com_imagem', 'nome': 'Primeiro Comentário com Imagem', 'descricao': 'Fez o primeiro comentário com imagem'},
        {'codigo': 'primeira_resposta_comentario', 'nome': 'Primeira Resposta', 'descricao': 'Respondeu a um comentário pela primeira vez'},
        {'codigo': '10_respostas_comentarios', 'nome': '10 Respostas', 'descricao': 'Respondeu 10 comentários'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - LIKES E REAÇÕES ===========================
        {'codigo': 'primeiro_like_social', 'nome': 'Primeiro Like', 'descricao': 'Deu o primeiro like em um post'},
        {'codigo': '10_likes_social', 'nome': '10 Likes', 'descricao': 'Deu 10 likes em posts'},
        {'codigo': '25_likes_social', 'nome': '25 Likes', 'descricao': 'Deu 25 likes em posts'},
        {'codigo': '50_likes_social', 'nome': '50 Likes', 'descricao': 'Deu 50 likes em posts'},
        {'codigo': '100_likes_social', 'nome': '100 Likes', 'descricao': 'Deu 100 likes em posts'},
        {'codigo': 'primeira_reacao_amor', 'nome': 'Primeira Reação de Amor', 'descricao': 'Usou a reação de amor pela primeira vez'},
        {'codigo': 'primeira_reacao_haha', 'nome': 'Primeira Reação Haha', 'descricao': 'Usou a reação haha pela primeira vez'},
        {'codigo': 'primeira_reacao_wow', 'nome': 'Primeira Reação Wow', 'descricao': 'Usou a reação wow pela primeira vez'},
        {'codigo': 'todas_reacoes', 'nome': 'Todas as Reações', 'descricao': 'Usou todos os tipos de reações'},
        {'codigo': 'primeiro_like_comentario', 'nome': 'Primeiro Like em Comentário', 'descricao': 'Deu o primeiro like em um comentário'},
        {'codigo': '10_likes_comentarios', 'nome': '10 Likes em Comentários', 'descricao': 'Deu 10 likes em comentários'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - COMPARTILHAMENTOS ===========================
        {'codigo': 'primeiro_compartilhamento', 'nome': 'Primeiro Compartilhamento', 'descricao': 'Compartilhou o primeiro post'},
        {'codigo': '5_compartilhamentos', 'nome': '5 Compartilhamentos', 'descricao': 'Compartilhou 5 posts'},
        {'codigo': '10_compartilhamentos', 'nome': '10 Compartilhamentos', 'descricao': 'Compartilhou 10 posts'},
        {'codigo': '25_compartilhamentos', 'nome': '25 Compartilhamentos', 'descricao': 'Compartilhou 25 posts'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - SEGUIR ===========================
        {'codigo': 'primeiro_seguir', 'nome': 'Primeiro Seguir', 'descricao': 'Seguiu o primeiro usuário'},
        {'codigo': '5_seguindo', 'nome': '5 Seguindo', 'descricao': 'Está seguindo 5 usuários'},
        {'codigo': '10_seguindo', 'nome': '10 Seguindo', 'descricao': 'Está seguindo 10 usuários'},
        {'codigo': '25_seguindo', 'nome': '25 Seguindo', 'descricao': 'Está seguindo 25 usuários'},
        {'codigo': '50_seguindo', 'nome': '50 Seguindo', 'descricao': 'Está seguindo 50 usuários'},
        {'codigo': 'primeiro_seguidor', 'nome': 'Primeiro Seguidor', 'descricao': 'Conseguiu o primeiro seguidor'},
        {'codigo': '5_seguidores', 'nome': '5 Seguidores', 'descricao': 'Tem 5 seguidores'},
        {'codigo': '10_seguidores', 'nome': '10 Seguidores', 'descricao': 'Tem 10 seguidores'},
        {'codigo': '25_seguidores', 'nome': '25 Seguidores', 'descricao': 'Tem 25 seguidores'},
        {'codigo': '50_seguidores', 'nome': '50 Seguidores', 'descricao': 'Tem 50 seguidores'},
        {'codigo': '100_seguidores', 'nome': '100 Seguidores', 'descricao': 'Tem 100 seguidores'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - HASHTAGS ===========================
        {'codigo': 'primeira_hashtag', 'nome': 'Primeira Hashtag', 'descricao': 'Usou uma hashtag pela primeira vez'},
        {'codigo': '5_hashtags_diferentes', 'nome': '5 Hashtags Diferentes', 'descricao': 'Usou 5 hashtags diferentes'},
        {'codigo': '10_hashtags_diferentes', 'nome': '10 Hashtags Diferentes', 'descricao': 'Usou 10 hashtags diferentes'},
        {'codigo': '25_hashtags_diferentes', 'nome': '25 Hashtags Diferentes', 'descricao': 'Usou 25 hashtags diferentes'},
        {'codigo': '50_hashtags_usadas', 'nome': '50 Hashtags Usadas', 'descricao': 'Usou hashtags em 50 posts'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - ENGAJAMENTO RECEBIDO ===========================
        {'codigo': 'primeiro_like_recebido', 'nome': 'Primeiro Like Recebido', 'descricao': 'Recebeu o primeiro like em um post'},
        {'codigo': '10_likes_recebidos', 'nome': '10 Likes Recebidos', 'descricao': 'Recebeu 10 likes em posts'},
        {'codigo': '25_likes_recebidos', 'nome': '25 Likes Recebidos', 'descricao': 'Recebeu 25 likes em posts'},
        {'codigo': '50_likes_recebidos', 'nome': '50 Likes Recebidos', 'descricao': 'Recebeu 50 likes em posts'},
        {'codigo': '100_likes_recebidos', 'nome': '100 Likes Recebidos', 'descricao': 'Recebeu 100 likes em posts'},
        {'codigo': '250_likes_recebidos', 'nome': '250 Likes Recebidos', 'descricao': 'Recebeu 250 likes em posts'},
        {'codigo': '500_likes_recebidos', 'nome': '500 Likes Recebidos', 'descricao': 'Recebeu 500 likes em posts'},
        {'codigo': 'primeiro_comentario_recebido', 'nome': 'Primeiro Comentário Recebido', 'descricao': 'Recebeu o primeiro comentário em um post'},
        {'codigo': '10_comentarios_recebidos', 'nome': '10 Comentários Recebidos', 'descricao': 'Recebeu 10 comentários em posts'},
        {'codigo': '25_comentarios_recebidos', 'nome': '25 Comentários Recebidos', 'descricao': 'Recebeu 25 comentários em posts'},
        {'codigo': '50_comentarios_recebidos', 'nome': '50 Comentários Recebidos', 'descricao': 'Recebeu 50 comentários em posts'},
        {'codigo': '100_comentarios_recebidos', 'nome': '100 Comentários Recebidos', 'descricao': 'Recebeu 100 comentários em posts'},
        {'codigo': 'post_10_likes', 'nome': 'Post com 10 Likes', 'descricao': 'Tem um post com 10 ou mais likes'},
        {'codigo': 'post_25_likes', 'nome': 'Post com 25 Likes', 'descricao': 'Tem um post com 25 ou mais likes'},
        {'codigo': 'post_50_likes', 'nome': 'Post com 50 Likes', 'descricao': 'Tem um post com 50 ou mais likes'},
        {'codigo': 'post_100_likes', 'nome': 'Post com 100 Likes', 'descricao': 'Tem um post com 100 ou mais likes'},
        {'codigo': 'post_viral', 'nome': 'Post Viral', 'descricao': 'Tem um post com 250 ou mais likes'},
        {'codigo': 'post_10_comentarios', 'nome': 'Post com 10 Comentários', 'descricao': 'Tem um post com 10 ou mais comentários'},
        {'codigo': 'post_25_comentarios', 'nome': 'Post com 25 Comentários', 'descricao': 'Tem um post com 25 ou mais comentários'},
        {'codigo': 'post_50_comentarios', 'nome': 'Post com 50 Comentários', 'descricao': 'Tem um post com 50 ou mais comentários'},
        {'codigo': 'primeiro_compartilhamento_recebido', 'nome': 'Primeiro Compartilhamento Recebido', 'descricao': 'Teve um post compartilhado pela primeira vez'},
        {'codigo': '10_compartilhamentos_recebidos', 'nome': '10 Compartilhamentos Recebidos', 'descricao': 'Teve posts compartilhados 10 vezes'},
        
        # =========================== CONQUISTAS DE REDE SOCIAL - PERFIL ===========================
        {'codigo': 'perfil_social_completo', 'nome': 'Perfil Social Completo', 'descricao': 'Completou o perfil social (tem bio e avatar)'},
        {'codigo': 'avatar_social', 'nome': 'Avatar Social', 'descricao': 'Tem avatar no perfil social'},
        {'codigo': 'bio_social', 'nome': 'Bio Social', 'descricao': 'Tem biografia no perfil social'},
        {'codigo': 'imagem_capa_social', 'nome': 'Imagem de Capa', 'descricao': 'Tem imagem de capa no perfil social'},
        {'codigo': 'perfil_privado', 'nome': 'Perfil Privado', 'descricao': 'Configurou o perfil como privado'},
    ]

    for conquista in conquistas:
        # Se a conquista ainda não existir, cria uma nova
        if not Conquista.objects.filter(codigo=conquista['codigo']).exists():
            Conquista.objects.create(
                codigo=conquista['codigo'],
                nome=conquista['nome'],
                descricao=conquista['descricao']
            )
