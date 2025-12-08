from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from ..models import Recompensa
from apps.main.home.models import Conquista


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def dashboard(request):
    """Dashboard de gerenciamento de premiações de conquistas"""
    
    # Estatísticas
    total_recompensas_conquista = Recompensa.objects.filter(tipo='CONQUISTA').count()
    total_recompensas_multiplas = Recompensa.objects.filter(tipo='CONQUISTAS_MULTIPLAS').count()
    total_conquistas = Conquista.objects.count()
    total_recompensas = Recompensa.objects.filter(tipo__in=['CONQUISTA', 'CONQUISTAS_MULTIPLAS']).count()
    
    # Recompensas recentes
    recent_rewards = Recompensa.objects.filter(tipo__in=['CONQUISTA', 'CONQUISTAS_MULTIPLAS']).order_by('-created_at')[:10]
    
    context = {
        'total_recompensas_conquista': total_recompensas_conquista,
        'total_recompensas_multiplas': total_recompensas_multiplas,
        'total_conquistas': total_conquistas,
        'total_recompensas': total_recompensas,
        'recent_rewards': recent_rewards,
    }
    
    return render(request, 'achievement_rewards/manager/dashboard.html', context)


@staff_required
def reward_list(request):
    """Lista todas as premiações de conquistas"""
    reward_type = request.GET.get('type', 'all')  # 'conquista', 'multiplas', 'all'
    
    queryset = Recompensa.objects.filter(tipo__in=['CONQUISTA', 'CONQUISTAS_MULTIPLAS'])
    
    if reward_type == 'conquista':
        queryset = queryset.filter(tipo='CONQUISTA')
    elif reward_type == 'multiplas':
        queryset = queryset.filter(tipo='CONQUISTAS_MULTIPLAS')
    
    rewards = queryset.order_by('-created_at')
    
    context = {
        'rewards': rewards,
        'current_type': reward_type,
    }
    return render(request, 'achievement_rewards/manager/reward_list.html', context)


@staff_required
@transaction.atomic
def reward_create(request):
    """Criar nova premiação de conquista"""
    conquistas = Conquista.objects.all().order_by('nome')
    
    if request.method == 'POST':
        try:
            tipo = request.POST.get('tipo', '').strip()
            # Pega a referência do campo hidden ou dos campos específicos
            referencia = request.POST.get('referencia', '').strip()
            if not referencia:
                # Tenta pegar dos campos específicos
                referencia = request.POST.get('referencia_conquista', '').strip()
                if not referencia:
                    referencia = request.POST.get('referencia_quantidade', '').strip()
            
            item_id = request.POST.get('item_id', '').strip()
            item_name = request.POST.get('item_name', '').strip()
            enchant = request.POST.get('enchant', '0').strip()
            quantity = request.POST.get('quantity', '1').strip()
            
            # Validação básica
            error_occurred = False
            if not tipo:
                messages.error(request, _('Selecione o tipo de premiação.'))
                error_occurred = True
            
            if not referencia:
                if tipo == 'CONQUISTA':
                    messages.error(request, _('Selecione uma conquista.'))
                elif tipo == 'CONQUISTAS_MULTIPLAS':
                    messages.error(request, _('Preencha a quantidade de conquistas.'))
                else:
                    messages.error(request, _('Preencha o campo de referência.'))
                error_occurred = True
            
            if not item_id:
                messages.error(request, _('Preencha o Item ID.'))
                error_occurred = True
            
            if not item_name:
                messages.error(request, _('Preencha o nome do item.'))
                error_occurred = True
            
            # Validação específica por tipo
            if tipo == 'CONQUISTA':
                # Verifica se a conquista existe
                if referencia and not Conquista.objects.filter(codigo=referencia).exists():
                    messages.error(request, _('Código de conquista não encontrado: {}').format(referencia))
                    error_occurred = True
            elif tipo == 'CONQUISTAS_MULTIPLAS':
                # Verifica se é um número válido
                if referencia:
                    try:
                        int(referencia)
                    except ValueError:
                        messages.error(request, _('A referência deve ser um número para premiações por quantidade de conquistas.'))
                        error_occurred = True
            elif tipo:
                messages.error(request, _('Tipo de premiação inválido.'))
                error_occurred = True
            
            # Validação de item_id
            item_id_int = None
            if item_id:
                try:
                    item_id_int = int(item_id)
                    if item_id_int <= 0:
                        messages.error(request, _('Item ID deve ser um número positivo.'))
                        error_occurred = True
                except (ValueError, TypeError):
                    messages.error(request, _('Item ID deve ser um número válido.'))
                    error_occurred = True
            
            # Validação de enchant e quantity
            enchant_int = 0
            quantity_int = 1
            try:
                enchant_int = int(enchant) if enchant else 0
                quantity_int = int(quantity) if quantity else 1
                if quantity_int <= 0:
                    messages.error(request, _('Quantidade deve ser maior que zero.'))
                    error_occurred = True
            except (ValueError, TypeError):
                messages.error(request, _('Encantamento e quantidade devem ser números válidos.'))
                error_occurred = True
            
            # Se houver erro, renderiza o template com os dados preservados
            if error_occurred:
                context = {
                    'conquistas': conquistas,
                }
                return render(request, 'achievement_rewards/manager/reward_create.html', context)
            
            recompensa = Recompensa.objects.create(
                tipo=tipo,
                referencia=referencia,
                item_id=item_id_int,
                item_name=item_name,
                enchant=enchant_int,
                quantity=quantity_int,
                created_by=request.user
            )
            
            messages.success(request, _('Premiação criada com sucesso!'))
            return redirect('games:achievement_rewards_manager_reward_list')
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            messages.error(request, _('Erro ao criar premiação: {}').format(str(e)))
            # Log do erro para debug
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Erro ao criar premiação: {error_detail}')
    
    context = {
        'conquistas': conquistas,
    }
    return render(request, 'achievement_rewards/manager/reward_create.html', context)


@staff_required
@transaction.atomic
def reward_edit(request, reward_id):
    """Editar premiação de conquista"""
    recompensa = get_object_or_404(Recompensa, id=reward_id, tipo__in=['CONQUISTA', 'CONQUISTAS_MULTIPLAS'])
    conquistas = Conquista.objects.all().order_by('nome')
    
    if request.method == 'POST':
        try:
            tipo = request.POST.get('tipo')
            referencia = request.POST.get('referencia')
            item_id = request.POST.get('item_id')
            item_name = request.POST.get('item_name')
            enchant = request.POST.get('enchant', 0)
            quantity = request.POST.get('quantity', 1)
            
            if not all([tipo, referencia, item_id, item_name]):
                messages.error(request, _('Preencha todos os campos obrigatórios.'))
                return redirect('games:achievement_rewards_manager_reward_edit', reward_id=reward_id)
            
            # Validação específica por tipo
            if tipo == 'CONQUISTA':
                if not Conquista.objects.filter(codigo=referencia).exists():
                    messages.error(request, _('Código de conquista não encontrado.'))
                    return redirect('games:achievement_rewards_manager_reward_edit', reward_id=reward_id)
            elif tipo == 'CONQUISTAS_MULTIPLAS':
                try:
                    int(referencia)
                except ValueError:
                    messages.error(request, _('A referência deve ser um número para premiações por quantidade de conquistas.'))
                    return redirect('games:achievement_rewards_manager_reward_edit', reward_id=reward_id)
            
            recompensa.tipo = tipo
            recompensa.referencia = referencia
            recompensa.item_id = int(item_id)
            recompensa.item_name = item_name
            recompensa.enchant = int(enchant) if enchant else 0
            recompensa.quantity = int(quantity) if quantity else 1
            recompensa.save()
            
            messages.success(request, _('Premiação atualizada com sucesso!'))
            return redirect('games:achievement_rewards_manager_reward_list')
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar premiação: {}').format(str(e)))
    
    context = {
        'recompensa': recompensa,
        'conquistas': conquistas,
    }
    return render(request, 'achievement_rewards/manager/reward_edit.html', context)


@staff_required
@transaction.atomic
def reward_delete(request, reward_id):
    """Deletar premiação de conquista"""
    recompensa = get_object_or_404(Recompensa, id=reward_id, tipo__in=['CONQUISTA', 'CONQUISTAS_MULTIPLAS'])
    
    if request.method == 'POST':
        try:
            recompensa_nome = str(recompensa)
            recompensa.delete()
            messages.success(request, _('Premiação "{}" deletada com sucesso!').format(recompensa_nome))
            return redirect('games:achievement_rewards_manager_reward_list')
        except Exception as e:
            messages.error(request, _('Erro ao deletar premiação: {}').format(str(e)))
            return redirect('games:achievement_rewards_manager_reward_list')
    
    context = {
        'recompensa': recompensa,
    }
    return render(request, 'achievement_rewards/manager/reward_delete.html', context)

