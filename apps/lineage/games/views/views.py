from django.shortcuts import render, get_object_or_404
from ..models import *
from apps.main.home.decorator import conditional_otp_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
import random
from decimal import Decimal
from apps.lineage.wallet.models import Wallet
from apps.lineage.wallet.signals import aplicar_transacao
from apps.lineage.inventory.models import Inventory, InventoryLog, InventoryItem
from apps.lineage.games.services.box_opening import open_box
from apps.lineage.games.services.box_populate import populate_box_with_items, can_populate_box
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from apps.lineage.server.services.account_context import get_lineage_template_context
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import json
import time
from datetime import datetime, timezone as dt_timezone
import calendar


def parse_int(value, default=0):
    try:
        return int(str(value).replace('.', '').replace(',', ''))
    except (ValueError, TypeError):
        return default


@conditional_otp_required
@transaction.atomic
def spin_ajax(request):
    try:
        UserModel = get_user_model()

        # Lock the user row to avoid race conditions during concurrent spins
        user = UserModel.objects.select_for_update().get(pk=request.user.pk)

        if user.fichas <= 0:
            return JsonResponse({'error': _('Você não tem fichas suficientes.')}, status=400)

        prizes = list(Prize.objects.all())
        if not prizes:
            # Auto-popula a tabela de prêmios a partir dos Itens de caixas
            weight_by_rarity = {
                'COMUM': 60,
                'RARE': 25,
                'RARA': 25,
                'EPIC': 10,
                'EPICA': 10,
                'LEGENDARY': 5,
                'LENDARIA': 5,
            }
            items = Item.objects.filter(can_be_populated=True)
            created_any = False
            for it in items:
                Prize.objects.get_or_create(
                    item=it,
                    defaults={
                        'name': it.name,
                        'legacy_item_code': it.item_id,
                        'enchant': it.enchant,
                        'rarity': it.rarity,
                        'weight': weight_by_rarity.get(str(it.rarity).upper(), 10),
                    }
                )
                created_any = True
            prizes = list(Prize.objects.all())
            if not prizes:
                return JsonResponse({'error': _('Nenhum prêmio disponível.')}, status=400)

        # Configurável via GameConfig
        from ..models import GameConfig
        cfg = GameConfig.objects.first()
        fail_chance = cfg.fail_chance if cfg else 20  # fallback para 20%
        total_weight = sum(p.weight for p in prizes)
        fail_weight = total_weight * (fail_chance / (100 - fail_chance))

        choices = prizes + [None]  # `None` representa a falha
        weights = [p.weight for p in prizes] + [fail_weight]

        # Auditoria: seed e snapshot de pesos
        seed = int(time.time_ns())
        random.seed(seed)
        chosen = random.choices(choices, weights=weights, k=1)[0]

        # Deduz uma ficha de forma transacional
        user.fichas -= 1
        user.save(update_fields=["fichas"])

        if chosen is None:
            # Registrar auditoria mesmo em falha
            SpinHistory.objects.create(
                user=user,
                prize=prizes[0],  # dummy prize para manter FK não nula; alternativa seria permitir null
                fail_chance=fail_chance,
                seed=seed,
                weights_snapshot=json.dumps({
                    'prizes': [
                        {'id': p.id, 'weight': p.weight} for p in prizes
                    ],
                    'fail_weight': fail_weight
                })
            )
            
            # Registra no histórico de fichas (falha)
            TokenHistory.objects.create(
                user=user,
                transaction_type='spend',
                game_type='roulette',
                amount=1,
                description='Giro na roleta (sem prêmio)',
                metadata={'prize_id': None, 'fail': True}
            )
            
            return JsonResponse({'fail': True, 'message': _('Você não ganhou nenhum prêmio.')})

        SpinHistory.objects.create(
            user=user,
            prize=chosen,
            fail_chance=fail_chance,
            seed=seed,
            weights_snapshot=json.dumps({
                'prizes': [
                    {'id': p.id, 'weight': p.weight} for p in prizes
                ],
                'fail_weight': fail_weight
            })
        )
        
        # Registra no histórico de fichas (sucesso)
        TokenHistory.objects.create(
            user=user,
            transaction_type='spend',
            game_type='roulette',
            amount=1,
            description=f'Giro na roleta - Ganhou: {chosen.name}',
            metadata={'prize_id': chosen.id, 'prize_name': chosen.name, 'fail': False}
        )

        # Certifique-se de que o usuário tenha uma bag
        bag, created = Bag.objects.get_or_create(user=user)

        # Verifica se o item já existe na bag (mesma id + enchant)
        # Resolve os campos do prêmio de forma segura
        if chosen.item:
            resolved_item_id = chosen.item.item_id
            resolved_enchant = chosen.item.enchant
            resolved_name = chosen.item.name
        else:
            resolved_item_id = chosen.legacy_item_code
            resolved_enchant = chosen.enchant
            resolved_name = chosen.name
        
        bag_item, created = BagItem.objects.get_or_create(
            bag=bag,
            item_id=resolved_item_id,
            enchant=resolved_enchant,
            defaults={
                'item_name': resolved_name,
                'quantity': 1,
            }
        )

        if not created:
            bag_item.quantity += 1
            bag_item.save(update_fields=["quantity"])

        # Atualizar progresso de quests relacionadas à roleta
        try:
            from apps.lineage.games.services.quest_progress_tracker import check_and_update_all_quests
            check_and_update_all_quests(user)
        except Exception as e:
            # Não falhar se houver erro no tracking
            pass

        # Campos via Item quando disponível para resposta
        if chosen.item:
            resp_name = chosen.item.name
            resp_item_id = chosen.item.item_id
            resp_enchant = chosen.item.enchant
        else:
            resp_name = chosen.name
            resp_item_id = chosen.legacy_item_code
            resp_enchant = chosen.enchant
        
        return JsonResponse({
            'id': chosen.id,
            'name': resp_name,
            'item_id': resp_item_id,
            'enchant': resp_enchant,
            'rarity': chosen.rarity,
            'image_url': chosen.get_image_url()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': _('Erro ao processar o giro. Tente novamente.')}, status=500)


@conditional_otp_required
def roulette_page(request):
    prizes = Prize.objects.select_related('item').all()
    prize_data = []
    for prize in prizes:
        name = prize.item.name if prize.item else prize.name
        item_id = prize.item.item_id if prize.item else prize.legacy_item_code
        enchant = prize.item.enchant if prize.item else prize.enchant
        prize_data.append({
            'name': name,
            'image_url': prize.get_image_url(),
            'item_id': item_id,
            'enchant': enchant,
            'rarity': prize.rarity
        })

    total_spins = SpinHistory.objects.filter(user=request.user).count()
    fichas = request.user.fichas
    last_spin = SpinHistory.objects.filter(user=request.user).order_by('-created_at').first()

    return render(request, 'roulette/spin.html', {
        'prizes': prize_data,
        'fichas': fichas,
        'total_spins': total_spins,
        'last_spin': last_spin,
    })


@conditional_otp_required
def comprar_fichas(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        # Valida quantidade
        quantidade_str = request.POST.get('quantidade', '0')
        try:
            quantidade = int(quantidade_str)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Quantidade inválida'}, status=400)
        
        if quantidade <= 0:
            return JsonResponse({'error': 'Quantidade deve ser maior que zero'}, status=400)
        
        if quantidade > 10000:  # Limite máximo de segurança
            return JsonResponse({'error': 'Quantidade máxima permitida é 10.000 fichas'}, status=400)
        
        valor_unitario = Decimal('0.10')  # 10 centavos por ficha
        total = valor_unitario * quantidade

        # Busca ou cria wallet (mais seguro que get)
        wallet, created = Wallet.objects.get_or_create(usuario=request.user)

        # Aplica transação
        try:
            aplicar_transacao(
                wallet=wallet,
                tipo='SAIDA',
                valor=total,
                descricao=f'{quantidade} ficha(s) comprada(s)',
                origem='Wallet',
                destino='Sistema de Fichas'
            )
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erro ao processar transação: {str(e)}'}, status=500)

        # Credita as fichas
        try:
            request.user.fichas += quantidade
            request.user.save()
            
            # Registra compra no histórico de fichas
            TokenHistory.objects.create(
                user=request.user,
                transaction_type='purchase',
                game_type='purchase',
                amount=quantidade,
                description=f'Compra de {quantidade} ficha(s)',
                metadata={'quantity': quantidade, 'total_cost': float(total), 'cost_per_token': 0.10}
            )
            
            return JsonResponse({'success': True, 'fichas': request.user.fichas})
        except Exception as e:
            return JsonResponse({'error': f'Erro ao creditar fichas: {str(e)}'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': f'Erro inesperado: {str(e)}'}, status=500)


@conditional_otp_required
def box_dashboard_view(request):
    box_types = BoxType.objects.all()
    wallet = Wallet.objects.filter(usuario=request.user).first()

    # Busca todas as caixas do usuário
    all_user_boxes = Box.objects.filter(user=request.user).prefetch_related('items')
    
    # Cria um dicionário com o ID do tipo da caixa como chave
    # Calcula remaining_boosters diretamente para cada caixa
    # IMPORTANTE: Só mostra caixas com boosters restantes > 0
    # Se houver múltiplas caixas do mesmo tipo, mostra a mais recente (maior ID)
    box_map = {}
    for box in all_user_boxes.order_by('-id'):  # Ordena por ID decrescente (mais recente primeiro)
        remaining_boosters = box.items.filter(opened=False).count()
        
        # Só adiciona ao mapa se tiver boosters restantes (maior que 0)
        # Se remaining_boosters = 0, a caixa NÃO aparece no dashboard
        # Se já existe uma caixa deste tipo no mapa, não sobrescreve (mantém a primeira encontrada, que é a mais recente)
        if remaining_boosters > 0:
            if box.box_type.id not in box_map:  # Só adiciona se ainda não existe uma caixa deste tipo
                box.remaining_boosters = remaining_boosters
                box_map[box.box_type.id] = box

    return render(request, 'box/dashboard.html', {
        'box_types': box_types,
        'user_balance': wallet.saldo if wallet else 0,
        'user_fichas': request.user.fichas,
        'user_boxes': box_map
    })


@conditional_otp_required
def box_opening_home(request):
    boxes = Box.objects.filter(user=request.user).order_by('-id')
    return render(request, 'box/opening_home.html', {'boxes': boxes})


@conditional_otp_required
@transaction.atomic
def open_box_ajax(request, box_id):
    """API endpoint para abrir caixa via AJAX"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método não permitido. Use POST.'
        }, status=405)
    
    try:
        box = Box.objects.get(id=box_id)
    except Box.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Esta caixa não existe.'
        }, status=404)

    if box.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Essa caixa não pertence a você.'
        }, status=403)

    # Verificar se o usuário possui fichas suficientes
    if request.user.fichas <= 0:
        return JsonResponse({
            'success': False,
            'error': 'Você não tem fichas suficientes para abrir a caixa.'
        }, status=400)

    # Deduzir uma ficha do saldo
    request.user.fichas -= 1
    request.user.save()
    
    # Registra gasto no histórico de fichas
    TokenHistory.objects.create(
        user=request.user,
        transaction_type='spend',
        game_type='box_opening',
        amount=1,
        description=f'Abertura de caixa: {box.box_type.name}',
        metadata={'box_id': box.id, 'box_type_id': box.box_type.id}
    )

    # Abrir a caixa
    item, error = open_box(request.user, box_id)

    if error:
        return JsonResponse({
            'success': False,
            'error': error
        }, status=400)

    # Buscar a caixa novamente para calcular boosters restantes
    box = Box.objects.get(id=box_id)
    remaining_boosters = box.items.filter(opened=False).count()
    
    # Se a caixa zerou, deleta automaticamente
    box_type_id = box.box_type.id
    if remaining_boosters == 0:
        box.delete()
        remaining_boosters = 0  # Garante que será 0 na resposta
    
    # Salva os dados do resultado na sessão para a view de exibição
    request.session['box_open_result'] = {
        'item_id': item.id,
        'box_type_id': box_type_id,
        'remaining_boosters': remaining_boosters
    }
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'item': {
            'id': item.item_id,
            'name': item.name,
            'enchant': item.enchant,
            'rarity': item.rarity,
            'rarity_display': item.get_rarity_display(),
            'image_url': item.image.url if item.image else None,
        },
        'remaining_boosters': remaining_boosters,
        'user_fichas': request.user.fichas,
        'box_id': box_id,
        'box_type_id': box.box_type.id,
        'redirect_url': '/app/game/box/result/'
    })


@conditional_otp_required
def open_box_view(request):
    """View apenas para exibir o resultado visual - a abertura é feita via AJAX"""
    # Busca os dados do resultado na sessão (setados pelo AJAX)
    result_data = request.session.get('box_open_result', None)
    
    if not result_data:
        messages.warning(request, _("Nenhum resultado de abertura encontrado."))
        return redirect('games:box_user_dashboard')
    
    # Remove os dados da sessão após usar (para não mostrar novamente se recarregar)
    del request.session['box_open_result']
    request.session.modified = True
    
    try:
        # Busca o item do banco de dados
        item = Item.objects.get(id=result_data.get('item_id'))
        box_type_id = result_data.get('box_type_id')
        remaining_boosters = result_data.get('remaining_boosters', 0)
        
        return render(request, 'box/result.html', {
            'item': item,
            'box_type_id': box_type_id,
            'remaining_boosters': remaining_boosters
        })
    except Item.DoesNotExist:
        messages.warning(request, _("Item não encontrado."))
        return redirect('games:box_user_dashboard')


@conditional_otp_required
@transaction.atomic
def buy_box_view(request, box_type_id):
    """Apenas compra a caixa, sem abrir o primeiro booster"""
    try:
        box_type = BoxType.objects.get(id=box_type_id)
    except BoxType.DoesNotExist:
        messages.error(request, _("Tipo de caixa não encontrado."))
        return redirect('games:box_user_dashboard')

    if not Item.objects.exists():
        messages.error(request, _("Não há itens cadastrados para abrir caixas."))
        return redirect('games:box_user_dashboard')

    if not box_type.boosters_amount:
        messages.error(request, _("Essa caixa não contém itens disponíveis para a abertura."))
        return redirect('games:box_user_dashboard')

    # Verificar se a caixa pode ser populada com boosters ANTES de gastar o dinheiro
    can_populate, populate_error = can_populate_box(box_type)
    if not can_populate:
        messages.error(request, _(populate_error or "Não é possível popular esta caixa com boosters."))
        return redirect('games:box_user_dashboard')

    total = box_type.price
    wallet = Wallet.objects.get(usuario=request.user)

    if wallet.saldo < total:
        messages.error(request, _("Saldo insuficiente para comprar a caixa."))
        return redirect('games:box_user_dashboard')

    try:
        aplicar_transacao(
            wallet=wallet,
            tipo='SAIDA',
            valor=total,
            descricao=f'Compra de caixa {box_type.name}',
            origem='Wallet',
            destino='Sistema de Caixas'
        )
        
        # Deletar TODAS as caixas existentes do mesmo tipo do usuário (para garantir apenas uma ativa)
        existing_boxes = Box.objects.filter(user=request.user, box_type=box_type)
        if existing_boxes.exists():
            existing_boxes.delete()
        
        # Criar a caixa e preencher com itens (sem abrir)
        box = Box.objects.create(user=request.user, box_type=box_type)
        populate_box_with_items(box)
        
        # Verificar se a caixa foi populada corretamente (deve ter pelo menos 1 booster)
        box.refresh_from_db()
        boosters_count = box.items.filter(opened=False).count()
        if boosters_count == 0:
            # Se não foi populada, lança exceção para reverter a transação automaticamente
            raise ValueError(_("Não foi possível popular a caixa com boosters. Verifique se há itens disponíveis com can_be_populated=True para todas as raridades necessárias."))
        
        messages.success(request, _("Caixa comprada com sucesso! Você pode abrir os boosters quando tiver fichas."))
        return redirect('games:box_user_dashboard')

    except ValueError as e:
        messages.error(request, _("Erro na transação: ") + str(e))
        return redirect('games:box_user_dashboard')


@conditional_otp_required
@transaction.atomic
def buy_and_open_box_view(request, box_type_id):
    # Limpa qualquer resultado anterior da sessão para evitar conflitos
    if 'box_open_result' in request.session:
        del request.session['box_open_result']
        request.session.modified = True
    
    try:
        box_type = BoxType.objects.get(id=box_type_id)
    except BoxType.DoesNotExist:
        messages.error(request, _("Tipo de caixa não encontrado."))
        return redirect('games:box_user_dashboard')

    # Verificar se há itens cadastrados no banco de dados
    if not Item.objects.exists():
        messages.error(request, _("Não há itens cadastrados para abrir caixas."))
        return redirect('games:box_user_dashboard')

    # Verificar se o tipo de caixa tem itens disponíveis para a raridade que ele define
    if not box_type.boosters_amount:
        messages.error(request, _("Essa caixa não contém itens disponíveis para a abertura."))
        return redirect('games:box_user_dashboard')

    # Verificar se a caixa pode ser populada com boosters ANTES de gastar o dinheiro
    can_populate, populate_error = can_populate_box(box_type)
    if not can_populate:
        messages.error(request, _(populate_error or "Não é possível popular esta caixa com boosters."))
        return redirect('games:box_user_dashboard')

    # Verificar se o usuário tem saldo suficiente para comprar a caixa
    total = box_type.price  # O preço da caixa é definido no modelo BoxType

    wallet = Wallet.objects.get(usuario=request.user)

    if wallet.saldo < total:
        messages.error(request, _("Saldo insuficiente para comprar a caixa."))
        return redirect('games:box_user_dashboard')

    # Verificar se o usuário possui fichas suficientes
    if request.user.fichas <= 0:
        messages.warning(request, _("Você não tem fichas suficientes para abrir a caixa."))
        return redirect('games:box_user_dashboard')

    # Aplicar a transação de saída da carteira para o sistema de caixas
    try:
        aplicar_transacao(
            wallet=wallet,
            tipo='SAIDA',
            valor=total,
            descricao=f'Compra de caixa {box_type.name}',
            origem='Wallet',
            destino='Sistema de Caixas'
        )
        
        # Deletar TODAS as caixas existentes do mesmo tipo do usuário (para garantir apenas uma ativa)
        existing_boxes = Box.objects.filter(user=request.user, box_type=box_type)
        if existing_boxes.exists():
            existing_boxes.delete()
        
        # Criar a caixa e preencher com itens
        box = Box.objects.create(user=request.user, box_type=box_type)
        populate_box_with_items(box)
        
        # Verificar se a caixa foi populada corretamente (deve ter pelo menos 1 booster)
        box.refresh_from_db()
        boosters_count = box.items.filter(opened=False).count()
        if boosters_count == 0:
            # Se não foi populada, lança exceção para reverter a transação automaticamente
            raise ValueError(_("Não foi possível popular a caixa com boosters. Verifique se há itens disponíveis com can_be_populated=True para todas as raridades necessárias."))
        
        # Deduzir uma ficha do saldo
        request.user.fichas -= 1
        request.user.save()
        
        # Registra gasto no histórico de fichas
        TokenHistory.objects.create(
            user=request.user,
            transaction_type='spend',
            game_type='box_opening',
            amount=1,
            description=f'Compra e abertura de caixa: {box_type.name}',
            metadata={'box_id': box.id, 'box_type_id': box_type.id}
        )
        
        # Abrir a caixa diretamente (primeiro booster)
        item, error = open_box(request.user, box.id)
        
        if error:
            # Se houver erro ao abrir, a transação já foi feita mas não conseguimos abrir
            # Neste caso, mantemos a caixa criada mas mostramos o erro
            messages.warning(request, error)
            return redirect('games:box_user_dashboard')
        
        # Buscar a caixa novamente para calcular boosters restantes
        box.refresh_from_db()
        remaining_boosters = box.items.filter(opened=False).count()
        
        # Se a caixa zerou, deleta automaticamente (não deve acontecer na compra, mas por segurança)
        box_type_id = box.box_type.id
        if remaining_boosters == 0:
            box.delete()
            remaining_boosters = 0  # Garante que será 0 na resposta
        
        # Salva os dados do resultado na sessão para a view de exibição
        request.session['box_open_result'] = {
            'item_id': item.id,
            'box_type_id': box_type_id,
            'remaining_boosters': remaining_boosters
        }
        request.session.modified = True
        
        # Redireciona para a URL fixa de resultado
        return redirect('games:box_user_open_box')

    except ValueError as e:
        messages.error(request, _("Erro na transação: ") + str(e))
        return redirect('games:box_user_dashboard')


@conditional_otp_required
@transaction.atomic
def reset_box_view(request, box_id):
    """Reseta uma caixa, deletando todos os itens e recriando-os, cobrando o preço novamente"""
    try:
        box = Box.objects.get(id=box_id)
    except Box.DoesNotExist:
        messages.warning(request, _("Esta caixa não existe."))
        return redirect('games:box_user_dashboard')

    if box.user != request.user:
        messages.warning(request, _("Essa caixa não pertence a você."))
        return redirect('games:box_user_dashboard')

    # Verificar se o usuário tem saldo suficiente para resetar (comprar novamente)
    box_type = box.box_type
    total = box_type.price

    wallet = Wallet.objects.get(usuario=request.user)

    if wallet.saldo < total:
        messages.error(request, _("Saldo insuficiente para resetar a caixa. É necessário comprar a caixa novamente."))
        return redirect('games:box_user_dashboard')

    # Verificar se a caixa pode ser populada com boosters ANTES de gastar o dinheiro
    can_populate, populate_error = can_populate_box(box_type)
    if not can_populate:
        messages.error(request, _(populate_error or "Não é possível popular esta caixa com boosters."))
        return redirect('games:box_user_dashboard')

    # Aplicar a transação de saída da carteira
    try:
        aplicar_transacao(
            wallet=wallet,
            tipo='SAIDA',
            valor=total,
            descricao=f'Reset de caixa {box_type.name}',
            origem='Wallet',
            destino='Sistema de Caixas'
        )
        
        # Deletar TODAS as outras caixas do mesmo tipo do usuário (para garantir apenas uma ativa)
        other_boxes = Box.objects.filter(user=request.user, box_type=box_type).exclude(id=box_id)
        if other_boxes.exists():
            other_boxes.delete()
        
        # Deletar todos os BoxItem da caixa atual
        box.items.all().delete()

        # Recriar os itens da caixa atual
        populate_box_with_items(box)
        
        # Verificar se a caixa foi populada corretamente (deve ter pelo menos 1 booster)
        box.refresh_from_db()
        boosters_count = box.items.filter(opened=False).count()
        if boosters_count == 0:
            # Se não foi populada, lança exceção para reverter a transação automaticamente
            raise ValueError(_("Não foi possível popular a caixa com boosters. Verifique se há itens disponíveis com can_be_populated=True para todas as raridades necessárias."))
        
        messages.success(request, _("Caixa resetada com sucesso! O preço foi cobrado novamente."))
    except ValueError as e:
        messages.error(request, _("Erro na transação: ") + str(e))
    except Exception as e:
        messages.error(request, _("Erro ao resetar a caixa: ") + str(e))

    return redirect('games:box_user_dashboard')


@conditional_otp_required
def bag_dashboard(request):
    try:
        bag = request.user.bag
        bag_items = bag.items.all()
    except Bag.DoesNotExist:
        bag = None
        bag_items = []

    personagens = Inventory.objects.filter(user=request.user).values_list('character_name', flat=True)

    return render(request, 'pages/bag_dashboard.html', {
        'bag': bag,
        'items': bag_items,
        'personagens': personagens,
    })


@conditional_otp_required
@transaction.atomic
def transferir_item_bag(request):
    if request.method == 'POST':
        item_id = parse_int(request.POST.get('item_id'))
        enchant = parse_int(request.POST.get('enchant'))
        quantity = parse_int(request.POST.get('quantity'))
        character_name_destino = request.POST.get('character_name_destino')

        bag = request.user.bag
        try:
            bag_item = BagItem.objects.get(bag=bag, item_id=item_id, enchant=enchant)
            if bag_item.quantity < quantity:
                messages.error(request, _('Quantidade insuficiente na Bag.'))
                return redirect('games:bag_dashboard')

            inventario_destino = get_object_or_404(Inventory, user=request.user, character_name=character_name_destino)

            # Remover da Bag
            bag_item.quantity -= quantity
            if bag_item.quantity == 0:
                bag_item.delete()
            else:
                bag_item.save()

            # Adicionar ao Inventário
            inventory_item, created = InventoryItem.objects.get_or_create(
                inventory=inventario_destino,
                item_id=item_id,
                enchant=enchant,
                defaults={'item_name': bag_item.item_name, 'quantity': quantity}
            )
            if not created:
                inventory_item.quantity += quantity
                inventory_item.save()

            # Log opcional
            InventoryLog.objects.create(
                user=request.user,
                inventory=inventario_destino,
                item_id=item_id,
                item_name=bag_item.item_name,
                enchant=enchant,
                quantity=quantity,
                acao='BAG_PARA_INVENTARIO',
                origem='BAG',
                destino=character_name_destino
            )

            messages.success(request, _('Item transferido com sucesso.'))
        except BagItem.DoesNotExist:
            messages.error(request, _('Item não encontrado na Bag.'))
        return redirect('games:bag_dashboard')


@conditional_otp_required
@transaction.atomic
def esvaziar_bag_para_inventario(request):
    if request.method == 'POST':
        character_name_destino = request.POST.get('character_name_destino')
        inventario_destino = get_object_or_404(Inventory, character_name=character_name_destino)
        bag = request.user.bag

        for bag_item in bag.items.all():
            inventory_item, created = InventoryItem.objects.get_or_create(
                inventory=inventario_destino,
                item_id=bag_item.item_id,
                enchant=bag_item.enchant,
                defaults={'item_name': bag_item.item_name, 'quantity': bag_item.quantity}
            )
            if not created:
                inventory_item.quantity += bag_item.quantity
                inventory_item.save()

            InventoryLog.objects.create(
                user=request.user,
                inventory=inventario_destino,
                item_id=bag_item.item_id,
                item_name=bag_item.item_name,
                enchant=bag_item.enchant,
                quantity=bag_item.quantity,
                acao='BAG_PARA_INVENTARIO',
                origem='BAG',
                destino=character_name_destino
            )

        bag.items.all().delete()
        messages.success(request, _('Todos os itens foram transferidos para o inventário.'))
        return redirect('games:bag_dashboard')


# ==============================
# Daily Bonus Views
# ==============================

def _now_utc():
    return datetime.now(dt_timezone.utc)


def _current_bonus_day(reset_hour_utc: int):
    now = _now_utc()
    anchor = now
    if now.hour < reset_hour_utc:
        # Antes do reset, considerar o dia anterior
        anchor = now.replace(day=now.day - 1 if now.day > 1 else 1)
    return anchor.day


def _get_month_bounds(dt):
    """
    Retorna o primeiro e último momento do mês para uma data.
    Útil para filtrar claims apenas do mês atual.
    """
    first_day = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Calcula o primeiro dia do próximo mês
    if dt.month == 12:
        last_day = dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        last_day = dt.replace(month=dt.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return first_day, last_day


def validate_daily_bonus_claim_security(user, season, day_of_month, request=None):
    """
    Valida se um usuário pode reclamar o prêmio diário.
    Retorna (True, None) se permitido, ou (False, mensagem_erro) se bloqueado.
    """
    from ..models import DailyBonusClaim
    from django.utils import timezone
    from datetime import timedelta
    import calendar
    
    # 1. Verifica se o usuário já reclamou este dia no mês/ano atual
    now = timezone.now()
    first_day_of_month, last_day_of_month = _get_month_bounds(now)
    
    if DailyBonusClaim.objects.filter(
        user=user, 
        season=season, 
        day_of_month=day_of_month,
        created_at__gte=first_day_of_month,
        created_at__lt=last_day_of_month
    ).exists():
        return False, _("Você já reclamou o prêmio deste dia.")
    
    # 2. Verifica contas muito recentes (menos de 1 hora)
    if user.date_joined > timezone.now() - timedelta(hours=1):
        # Conta muito recente - verifica se há múltiplas contas do mesmo IP
        if request:
            from python_ipware import IpWare
            ipw = IpWare(precedence=("X_FORWARDED_FOR", "HTTP_X_FORWARDED_FOR"))
            ip_address, is_routable = ipw.get_client_ip(meta=request.META)
            
            if ip_address:
                # Verifica quantas contas do mesmo IP reclamaram este dia no mês/ano atual
                accounts_same_ip = DailyBonusClaim.objects.filter(
                    season=season,
                    day_of_month=day_of_month,
                    ip_address=str(ip_address),
                    created_at__gte=first_day_of_month,
                    created_at__lt=last_day_of_month
                ).values('user').distinct().count()
                
                if accounts_same_ip > 0:
                    return False, _("Múltiplas contas do mesmo IP não podem reclamar os mesmos prêmios diários.")
        
        # Verifica se há múltiplas contas com o mesmo domínio de email
        email_domain = user.email.split('@')[1] if '@' in user.email else None
        if email_domain:
            UserModel = get_user_model()
            # Conta quantos usuários do mesmo domínio de email reclamaram este dia
            same_domain_users = UserModel.objects.filter(
                email__endswith=f'@{email_domain}',
                date_joined__gt=timezone.now() - timedelta(hours=24)
            ).exclude(id=user.id).values_list('id', flat=True)
            
            same_domain_claims = DailyBonusClaim.objects.filter(
                season=season,
                day_of_month=day_of_month,
                user_id__in=same_domain_users,
                created_at__gte=first_day_of_month,
                created_at__lt=last_day_of_month
            ).count()
            
            if same_domain_claims > 0:
                return False, _("Múltiplas contas com emails do mesmo domínio não podem reclamar os mesmos prêmios diários.")
    
    # 3. Verifica limite de prêmios reclamados por IP em um período (últimas 24h)
    if request:
        from python_ipware import IpWare
        ipw = IpWare(precedence=("X_FORWARDED_FOR", "HTTP_X_FORWARDED_FOR"))
        ip_address, is_routable = ipw.get_client_ip(meta=request.META)
        
        if ip_address:
            # Conta quantas reivindicações este IP fez nas últimas 24h
            recent_claims = DailyBonusClaim.objects.filter(
                ip_address=str(ip_address),
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Limite de 3 reivindicações por IP em 24h
            if recent_claims >= 3:
                return False, _("Limite de prêmios diários reclamados atingido para este endereço IP. Tente novamente mais tarde.")
    
    return True, None


@conditional_otp_required
def daily_bonus_dashboard(request):
    from ..models import DailyBonusSeason, DailyBonusDay, DailyBonusClaim

    season = DailyBonusSeason.objects.filter(is_active=True).first()
    if not season:
        return render(request, 'daily_bonus/dashboard.html', {
            'season': None,
            'days': [],
            'today': None,
            'can_claim': False,
            'allow_retroactive': False,
        })

    today_day = _current_bonus_day(season.reset_hour_utc)
    # Quantidade de dias do mês atual (UTC)
    now = _now_utc()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    month_days = range(1, days_in_month + 1)
    day_defs = {d.day_of_month: d for d in DailyBonusDay.objects.filter(season=season)}
    # Filtra claims apenas do mês/ano atual para permitir reset mensal
    first_day_of_month, last_day_of_month = _get_month_bounds(now)
    claims = DailyBonusClaim.objects.filter(
        user=request.user, 
        season=season,
        created_at__gte=first_day_of_month,
        created_at__lt=last_day_of_month
    )
    claimed_days = set(c.day_of_month for c in claims)

    context_days = []
    for d in month_days:
        dd = day_defs.get(d)
        can_claim_this_day = False
        if season.allow_retroactive_claim:
            # Com resgate retroativo, pode resgatar qualquer dia anterior que não foi reclamado
            can_claim_this_day = (d not in claimed_days) and (d < today_day)
        else:
            # Sem resgate retroativo, só pode resgatar o dia de hoje
            can_claim_this_day = (d == today_day) and (d not in claimed_days)
        
        context_days.append({
            'day': d,
            'mode': dd.mode if dd else 'RANDOM',
            'fixed_item': dd.fixed_item if dd else None,
            'claimed': d in claimed_days,
            'is_today': d == today_day,
            'can_claim': can_claim_this_day,
        })

    # Só permite claim se o dia existe no mês corrente
    can_claim = (today_day not in claimed_days) and (1 <= today_day <= days_in_month)

    return render(request, 'daily_bonus/dashboard.html', {
        'season': season,
        'days': context_days,
        'today': today_day,
        'can_claim': can_claim,
        'allow_retroactive': season.allow_retroactive_claim,
    })


@conditional_otp_required
@transaction.atomic
def daily_bonus_claim(request):
    from ..models import DailyBonusSeason, DailyBonusDay, DailyBonusClaim, DailyBonusPoolEntry, Item

    season = DailyBonusSeason.objects.filter(is_active=True).select_for_update().first()
    if not season:
        messages.error(request, _('Nenhuma temporada de bônus diária ativa.'))
        return redirect('games:daily_bonus_dashboard')

    today_day = _current_bonus_day(season.reset_hour_utc)
    # Validar contra o número de dias do mês corrente (UTC)
    now = _now_utc()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    
    # Permite resgate retroativo se configurado e se um dia específico foi fornecido
    target_day = today_day
    if season.allow_retroactive_claim and 'day' in request.GET:
        try:
            requested_day = int(request.GET.get('day'))
            if 1 <= requested_day <= days_in_month and requested_day < today_day:
                target_day = requested_day
            else:
                messages.error(request, _('Dia inválido para resgate retroativo.'))
                return redirect('games:daily_bonus_dashboard')
        except (ValueError, TypeError):
            messages.error(request, _('Dia inválido.'))
            return redirect('games:daily_bonus_dashboard')
    elif not season.allow_retroactive_claim:
        # Sem resgate retroativo, só permite o dia de hoje
        if not (1 <= today_day <= days_in_month):
            messages.error(request, _('Fora da janela de dias válidos.'))
            return redirect('games:daily_bonus_dashboard')
    
    if not (1 <= target_day <= days_in_month):
        messages.error(request, _('Fora da janela de dias válidos.'))
        return redirect('games:daily_bonus_dashboard')

    # Verifica se já reclamou (com lock para evitar race conditions)
    # Filtra apenas claims do mês/ano atual para permitir reset mensal
    first_day_of_month, last_day_of_month = _get_month_bounds(now)
    
    claim_exists = DailyBonusClaim.objects.select_for_update().filter(
        user=request.user, 
        season=season, 
        day_of_month=target_day,
        created_at__gte=first_day_of_month,
        created_at__lt=last_day_of_month
    ).exists()
    
    if claim_exists:
        if target_day == today_day:
            messages.info(request, _('Você já resgatou o prêmio de hoje.'))
        else:
            messages.info(request, _('Você já resgatou o prêmio deste dia.'))
        return redirect('games:daily_bonus_dashboard')

    # Validações de segurança para evitar multiplicação de itens
    is_valid, error_message = validate_daily_bonus_claim_security(
        request.user, 
        season, 
        target_day, 
        request
    )
    if not is_valid:
        messages.error(request, error_message)
        return redirect('games:daily_bonus_dashboard')

    # Resolver prêmio do dia
    day_def = DailyBonusDay.objects.filter(season=season, day_of_month=target_day).first()
    chosen_item = None
    if day_def and day_def.mode == 'FIXED' and day_def.fixed_item:
        chosen_item = day_def.fixed_item
    else:
        pool = list(DailyBonusPoolEntry.objects.filter(season=season))
        if not pool:
            messages.error(request, _('Pool de itens da temporada está vazio.'))
            return redirect('games:daily_bonus_dashboard')
        choices = [p.item for p in pool]
        weights = [p.weight for p in pool]
        chosen_item = random.choices(choices, weights=weights, k=1)[0]

    # Enviar para a Bag
    bag, created = Bag.objects.get_or_create(user=request.user)
    bag_item, created = BagItem.objects.get_or_create(
        bag=bag,
        item_id=chosen_item.item_id,
        enchant=chosen_item.enchant,
        defaults={'item_name': chosen_item.name, 'quantity': 1}
    )
    if not created:
        bag_item.quantity += 1
        bag_item.save(update_fields=['quantity'])

    # Registra a reivindicação com IP e user agent
    from python_ipware import IpWare
    ipw = IpWare(precedence=("X_FORWARDED_FOR", "HTTP_X_FORWARDED_FOR"))
    ip_address, is_routable = ipw.get_client_ip(meta=request.META) if request else (None, False)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    
    DailyBonusClaim.objects.create(
        user=request.user, 
        season=season, 
        day_of_month=target_day,
        ip_address=str(ip_address) if ip_address else None,
        user_agent=user_agent or None
    )

    if target_day == today_day:
        messages.success(request, _('Prêmio diário resgatado com sucesso!'))
    else:
        messages.success(request, _('Prêmio retroativo do dia {} resgatado com sucesso!').format(target_day))
    return redirect('games:daily_bonus_dashboard')


@conditional_otp_required
def daily_bonus_history(request):
    """Visualizar histórico de coletas do bônus diário"""
    from ..models import DailyBonusSeason, DailyBonusClaim
    from django.db.models import Count
    from collections import defaultdict
    
    season = DailyBonusSeason.objects.filter(is_active=True).first()
    if not season:
        return render(request, 'daily_bonus/history.html', {
            'season': None,
            'history_by_month': {},
            'total_claims': 0,
        })
    
    # Busca todos os claims do usuário para esta season, ordenados por data
    all_claims = DailyBonusClaim.objects.filter(
        user=request.user,
        season=season
    ).order_by('-created_at')
    
    # Agrupa por mês/ano
    history_by_month = defaultdict(lambda: {
        'year': None,
        'month': None,
        'month_name': None,
        'days_claimed': set(),
        'total_days': 0,
        'claims': []
    })
    
    for claim in all_claims:
        claim_date = claim.created_at
        month_key = f"{claim_date.year}-{claim_date.month:02d}"
        
        if month_key not in history_by_month:
            month_names = [
                _('Janeiro'), _('Fevereiro'), _('Março'), _('Abril'),
                _('Maio'), _('Junho'), _('Julho'), _('Agosto'),
                _('Setembro'), _('Outubro'), _('Novembro'), _('Dezembro')
            ]
            days_in_month = calendar.monthrange(claim_date.year, claim_date.month)[1]
            
            history_by_month[month_key] = {
                'year': claim_date.year,
                'month': claim_date.month,
                'month_name': month_names[claim_date.month - 1],
                'days_claimed': set(),
                'total_days': days_in_month,
                'days_list': list(range(1, days_in_month + 1)),
                'claims': []
            }
        
        history_by_month[month_key]['days_claimed'].add(claim.day_of_month)
        history_by_month[month_key]['claims'].append(claim)
    
    # Converte sets para sorted lists e ordena por mês/ano (mais recente primeiro)
    for month_key in history_by_month:
        history_by_month[month_key]['days_claimed'] = sorted(history_by_month[month_key]['days_claimed'])
        history_by_month[month_key]['claims'] = sorted(
            history_by_month[month_key]['claims'],
            key=lambda x: x.created_at,
            reverse=True
        )
    
    # Ordena os meses (mais recente primeiro)
    sorted_months = sorted(
        history_by_month.items(),
        key=lambda x: (x[1]['year'], x[1]['month']),
        reverse=True
    )
    history_by_month = dict(sorted_months)
    
    total_claims = all_claims.count()
    
    return render(request, 'daily_bonus/history.html', {
        'season': season,
        'history_by_month': history_by_month,
        'total_claims': total_claims,
    })


@conditional_otp_required
def tokens_history(request):
    """Visualizar histórico de fichas do usuário"""
    history = TokenHistory.objects.filter(user=request.user).order_by('-created_at')
    
    # Paginação
    paginator = Paginator(history, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    from utils.pagination_helper import prepare_pagination_context
    pagination_context = prepare_pagination_context(page_obj)
    
    # Estatísticas
    total_spent = TokenHistory.objects.filter(
        user=request.user,
        transaction_type='spend'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_earned = TokenHistory.objects.filter(
        user=request.user,
        transaction_type='earn'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_purchased = TokenHistory.objects.filter(
        user=request.user,
        transaction_type='purchase'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'history': page_obj,
        'page_obj': page_obj,
        'total_spent': total_spent,
        'total_earned': total_earned,
        'total_purchased': total_purchased,
        'current_fichas': request.user.fichas,
        **pagination_context,
    }
    context.update(get_lineage_template_context(request))
    return render(request, 'games/tokens_history.html', context)
