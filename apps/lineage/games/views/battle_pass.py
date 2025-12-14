from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.lineage.games.models import UserBattlePassProgress, BattlePassSeason, BattlePassReward, BattlePassItemExchange, Bag, BagItem, BattlePassLevel
from apps.lineage.games.services.battle_pass_service import BattlePassService
from apps.main.home.decorator import conditional_otp_required
from django.shortcuts import redirect, get_object_or_404
from apps.lineage.wallet.models import Wallet
from apps.lineage.wallet.signals import aplicar_transacao
from django.contrib import messages
from django.utils.translation import gettext_lazy as gettext


@conditional_otp_required
def battle_pass_view(request):
    season = BattlePassService.get_active_season()

    if not season:
        return render(request, 'battlepass/no_active_season.html')

    progress, created = UserBattlePassProgress.objects.get_or_create(
        user=request.user,
        season=season
    )

    # Usa o service para calcular o progresso
    progress_data = BattlePassService.calculate_progress(progress)
    time_remaining = BattlePassService.get_season_time_remaining(season)

    levels_queryset = season.battlepasslevel_set.order_by('level').prefetch_related('battlepassreward_set')
    
    # Paginação - 12 níveis por página
    paginator = Paginator(levels_queryset, 12)
    page = request.GET.get('page')
    
    try:
        levels_page = paginator.page(page)
    except PageNotAnInteger:
        levels_page = paginator.page(1)
    except EmptyPage:
        levels_page = paginator.page(paginator.num_pages)
    
    from utils.pagination_helper import prepare_pagination_context
    pagination_context = prepare_pagination_context(levels_page)
    
    context = {
        'season': season,
        'progress': progress,
        'levels': levels_page,
        'current_level': progress_data['current_level_number'],
        'next_level': progress_data['next_level'].level if progress_data['next_level'] else None,
        'current_xp': progress_data['current_xp'],
        'xp_for_next_level': progress_data['xp_for_next_level'],
        'progress_percentage': progress_data['progress_percentage'],
        'is_max_level': progress_data['is_max_level'],
        'time_remaining': time_remaining,
        'has_other_pages': levels_page.has_other_pages(),
        'has_previous': levels_page.has_previous(),
        'has_next': levels_page.has_next(),
        'previous_page_number': levels_page.previous_page_number() if levels_page.has_previous() else None,
        'next_page_number': levels_page.next_page_number() if levels_page.has_next() else None,
        'current_page': levels_page.number,
        'num_pages': paginator.num_pages,
        'total_levels': paginator.count,
        **pagination_context,
    }
    
    return render(request, 'battlepass/battle_pass.html', context)


@conditional_otp_required
def claim_reward(request, reward_id):
    reward = get_object_or_404(BattlePassReward, id=reward_id)
    progress = get_object_or_404(UserBattlePassProgress, user=request.user, season=reward.level.season)

    # Usa o service para validar se pode resgatar
    can_claim, reason = BattlePassService.can_claim_reward(progress, reward)
    
    if can_claim:
        # Adiciona o item à bag do usuário
        bag_item = reward.add_to_user_bag(request.user)
        if bag_item:
            messages.success(request, gettext("Recompensa resgatada com sucesso!"))
        else:
            messages.warning(request, gettext("Recompensa resgatada, mas não há item associado."))
        progress.claimed_rewards.add(reward)
    else:
        messages.error(request, gettext(reason))

    return redirect('games:battle_pass')


@conditional_otp_required
def buy_battle_pass_premium_view(request):
    season = BattlePassService.get_active_season()

    if not season:
        messages.error(request, gettext("Nenhuma temporada ativa no momento."))
        return redirect('games:battle_pass')

    progress, created = UserBattlePassProgress.objects.get_or_create(user=request.user, season=season)

    if progress.has_premium:
        messages.info(request, gettext("Você já possui o Passe de Batalha Premium."))
        return redirect('games:battle_pass')

    PREMIUM_PRICE = season.premium_price

    try:
        wallet = Wallet.objects.get(usuario=request.user)
    except Wallet.DoesNotExist:
        messages.error(request, gettext("Carteira não encontrada."))
        return redirect('games:battle_pass')

    if request.method == 'POST':
        # Confirmação da compra
        if wallet.saldo < PREMIUM_PRICE:
            messages.error(request, gettext("Saldo insuficiente para adquirir o Passe Premium."))
            return redirect('games:battle_pass')

        try:
            aplicar_transacao(
                wallet=wallet,
                tipo='SAIDA',
                valor=PREMIUM_PRICE,
                descricao=f'Compra do Battle Pass Premium - {season.name}',
                origem='Wallet',
                destino='Sistema de Battle Pass'
            )
            progress.has_premium = True
            progress.save()
            messages.success(request, gettext("Passe de Batalha Premium ativado com sucesso!"))
            return redirect('games:battle_pass')
        except ValueError as e:
            messages.error(request, gettext("Erro na transação: ") + str(e))
            return redirect('games:battle_pass')

    # GET: Mostrar tela de confirmação
    remaining_balance = wallet.saldo - PREMIUM_PRICE if wallet.saldo >= PREMIUM_PRICE else 0
    return render(request, 'battlepass/confirm_premium_purchase.html', {
        'season': season,
        'premium_price': PREMIUM_PRICE,
        'wallet': wallet,
        'remaining_balance': remaining_balance
    })


@conditional_otp_required
def exchange_items_view(request):
    season = BattlePassService.get_active_season()
    if not season:
        messages.error(request, gettext("Não há temporada ativa no momento."))
        return redirect('games:battle_pass')

    progress, created = UserBattlePassProgress.objects.get_or_create(
        user=request.user,
        season=season
    )
    exchanges = BattlePassItemExchange.objects.filter(is_active=True)

    # Usa o service para calcular o progresso
    progress_data = BattlePassService.calculate_progress(progress)

    # Verifica quais itens o usuário possui
    try:
        bag = Bag.objects.get(user=request.user)
        user_items = BagItem.objects.filter(bag=bag)
        item_ids = set(user_items.values_list('item_id', 'enchant'))
        
        for exchange in exchanges:
            exchange.has_item = (exchange.item_id, exchange.item_enchant) in item_ids
            if exchange.has_item:
                exchange.item_quantity = user_items.get(
                    item_id=exchange.item_id,
                    enchant=exchange.item_enchant
                ).quantity
    except Bag.DoesNotExist:
        for exchange in exchanges:
            exchange.has_item = False

    return render(request, 'battlepass/exchange_items.html', {
        'exchanges': exchanges,
        'progress': progress,
        'current_level': progress_data['current_level_number'],
        'next_level': progress_data['next_level'].level if progress_data['next_level'] else None,
        'current_xp': progress_data['current_xp'],
        'xp_for_next_level': progress_data['xp_for_next_level'],
        'progress_percentage': progress_data['progress_percentage'],
    })


@conditional_otp_required
def exchange_item(request, exchange_id):
    exchange = get_object_or_404(BattlePassItemExchange, id=exchange_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            messages.error(request, gettext("Quantidade inválida."))
            return redirect('games:exchange_items')
            
        success, message = exchange.exchange(request.user, quantity)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('games:exchange_items')


@conditional_otp_required
def battle_pass_history_view(request):
    """Visualização do histórico do Battle Pass"""
    season = BattlePassService.get_active_season()
    
    if not season:
        messages.error(request, gettext("Não há temporada ativa no momento."))
        return redirect('games:battle_pass')
    
    from ..models import BattlePassHistory, BattlePassReward
    from django.core.paginator import Paginator
    
    history = BattlePassHistory.objects.filter(
        user=request.user,
        season=season
    ).order_by('-created_at')
    
    paginator = Paginator(history, 20)
    page = request.GET.get('page', 1)
    
    try:
        history_page = paginator.page(page)
    except:
        history_page = paginator.page(1)
    
    from utils.pagination_helper import prepare_pagination_context
    pagination_context = prepare_pagination_context(history_page)
    
    # Buscar rewards para exibir ícones de itens
    reward_ids = []
    for item in history_page:
        if item.metadata and 'reward_id' in item.metadata:
            reward_ids.append(item.metadata['reward_id'])
    
    rewards_dict = {}
    if reward_ids:
        rewards = BattlePassReward.objects.filter(id__in=reward_ids).select_related('level')
        rewards_dict = {r.id: r for r in rewards}
    
    # Adicionar reward ao contexto de cada item e informações de item do metadata
    for item in history_page:
        if item.metadata:
            # Se tem reward_id, buscar o reward
            if 'reward_id' in item.metadata:
                reward_id = item.metadata['reward_id']
                item.reward = rewards_dict.get(reward_id)
            # Se tem informações de item diretamente no metadata (para item_exchanged, etc)
            elif 'item_id' in item.metadata:
                item.item_id = item.metadata.get('item_id')
                item.item_name = item.metadata.get('item_name')
                item.item_enchant = item.metadata.get('item_enchant', 0)
                item.item_amount = item.metadata.get('item_amount', 1)
    
    context = {
        'season': season,
        'history': history_page,
        **pagination_context,
    }
    
    return render(request, 'battlepass/history.html', context)


@conditional_otp_required
def battle_pass_statistics_view(request):
    """Visualização de estatísticas do Battle Pass"""
    season = BattlePassService.get_active_season()
    
    if not season:
        messages.error(request, gettext("Não há temporada ativa no momento."))
        return redirect('games:battle_pass')
    
    from ..models import BattlePassStatistics, BattlePassHistory
    from django.db.models import Count, Avg, Max
    
    progress, created = UserBattlePassProgress.objects.get_or_create(
        user=request.user,
        season=season
    )
    
    stats, created = BattlePassStatistics.objects.get_or_create(
        user=request.user,
        season=season
    )
    
    # Estatísticas adicionais
    progress_data = BattlePassService.calculate_progress(progress)
    
    # Ranking (posição entre todos os usuários)
    all_progress = UserBattlePassProgress.objects.filter(season=season).order_by('-xp')
    rank = 0
    for idx, p in enumerate(all_progress, 1):
        if p.user == request.user:
            rank = idx
            break
    
    # Estatísticas gerais da temporada
    total_users = UserBattlePassProgress.objects.filter(season=season).count()
    avg_xp = UserBattlePassProgress.objects.filter(season=season).aggregate(Avg('xp'))['xp__avg'] or 0
    max_xp = UserBattlePassProgress.objects.filter(season=season).aggregate(Max('xp'))['xp__max'] or 0
    
    # Histórico recente (últimas 10 ações)
    recent_history = BattlePassHistory.objects.filter(
        user=request.user,
        season=season
    ).order_by('-created_at')[:10]
    
    # Buscar rewards para exibir ícones de itens no histórico recente
    reward_ids = []
    for item in recent_history:
        if item.metadata and 'reward_id' in item.metadata:
            reward_ids.append(item.metadata['reward_id'])
    
    rewards_dict = {}
    if reward_ids:
        from ..models import BattlePassReward
        rewards = BattlePassReward.objects.filter(id__in=reward_ids).select_related('level')
        rewards_dict = {r.id: r for r in rewards}
    
    # Adicionar reward ao contexto de cada item e informações de item do metadata
    for item in recent_history:
        if item.metadata:
            # Se tem reward_id, buscar o reward
            if 'reward_id' in item.metadata:
                reward_id = item.metadata['reward_id']
                item.reward = rewards_dict.get(reward_id)
            # Se tem informações de item diretamente no metadata (para item_exchanged, etc)
            elif 'item_id' in item.metadata:
                item.item_id = item.metadata.get('item_id')
                item.item_name = item.metadata.get('item_name')
                item.item_enchant = item.metadata.get('item_enchant', 0)
                item.item_amount = item.metadata.get('item_amount', 1)
    
    context = {
        'season': season,
        'progress': progress,
        'stats': stats,
        'progress_data': progress_data,
        'rank': rank,
        'total_users': total_users,
        'avg_xp': int(avg_xp),
        'max_xp': max_xp,
        'recent_history': recent_history,
    }
    
    return render(request, 'battlepass/statistics.html', context)


@conditional_otp_required
def toggle_auto_claim(request):
    """Ativa/desativa auto-claim de recompensas free"""
    season = BattlePassService.get_active_season()
    
    if not season:
        messages.error(request, gettext("Não há temporada ativa no momento."))
        return redirect('games:battle_pass')
    
    progress, created = UserBattlePassProgress.objects.get_or_create(
        user=request.user,
        season=season
    )
    
    progress.auto_claim_free = not progress.auto_claim_free
    progress.save()
    
    if progress.auto_claim_free:
        messages.success(request, gettext("Auto-resgate de recompensas free ativado!"))
        # Tenta resgatar recompensas disponíveis imediatamente
        claimed = progress.auto_claim_free_rewards()
        if claimed > 0:
            messages.info(request, gettext(f"{claimed} recompensa(s) free foram resgatadas automaticamente!"))
    else:
        messages.info(request, gettext("Auto-resgate de recompensas free desativado."))
    
    return redirect('games:battle_pass')
