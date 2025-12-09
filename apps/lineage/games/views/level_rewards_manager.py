from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from ..models import Recompensa


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def dashboard(request):
    """Dashboard de gerenciamento de recompensas por level"""
    
    # Estatísticas
    total_recompensas = Recompensa.objects.filter(tipo='NIVEL').count()
    
    # Níveis únicos com recompensas
    niveis_com_recompensa = Recompensa.objects.filter(tipo='NIVEL').values('referencia').annotate(
        count=Count('id')
    ).order_by('referencia')
    
    # Recompensas recentes
    recent_rewards = Recompensa.objects.filter(tipo='NIVEL').order_by('-created_at')[:10]
    
    # Estatísticas por nível
    nivel_stats = {}
    for item in niveis_com_recompensa:
        nivel = item['referencia']
        nivel_stats[nivel] = item['count']
    
    context = {
        'total_recompensas': total_recompensas,
        'niveis_com_recompensa': niveis_com_recompensa,
        'nivel_stats': nivel_stats,
        'recent_rewards': recent_rewards,
    }
    
    return render(request, 'level_rewards/manager/dashboard.html', context)


@staff_required
def reward_list(request):
    """Lista todas as recompensas por level"""
    nivel_filter = request.GET.get('nivel', '')
    
    queryset = Recompensa.objects.filter(tipo='NIVEL')
    
    if nivel_filter:
        try:
            nivel_int = int(nivel_filter)
            queryset = queryset.filter(referencia=str(nivel_int))
        except ValueError:
            pass
    
    rewards = queryset.order_by('referencia', '-created_at')
    
    # Níveis únicos para filtro
    niveis_unicos = Recompensa.objects.filter(tipo='NIVEL').values_list('referencia', flat=True).distinct().order_by('referencia')
    
    context = {
        'rewards': rewards,
        'current_nivel': nivel_filter,
        'niveis_unicos': niveis_unicos,
    }
    return render(request, 'level_rewards/manager/reward_list.html', context)


@staff_required
@transaction.atomic
def reward_create(request):
    """Criar nova recompensa por level"""
    
    if request.method == 'POST':
        try:
            nivel = request.POST.get('nivel', '').strip()
            item_id = request.POST.get('item_id', '').strip()
            item_name = request.POST.get('item_name', '').strip()
            enchant = request.POST.get('enchant', '0').strip()
            quantity = request.POST.get('quantity', '1').strip()
            
            # Validação básica
            error_occurred = False
            
            if not nivel:
                messages.error(request, _('Preencha o nível.'))
                error_occurred = True
            else:
                try:
                    nivel_int = int(nivel)
                    if nivel_int <= 0:
                        messages.error(request, _('O nível deve ser maior que zero.'))
                        error_occurred = True
                except (ValueError, TypeError):
                    messages.error(request, _('O nível deve ser um número válido.'))
                    error_occurred = True
            
            if not item_id:
                messages.error(request, _('Preencha o Item ID.'))
                error_occurred = True
            else:
                try:
                    item_id_int = int(item_id)
                    if item_id_int <= 0:
                        messages.error(request, _('Item ID deve ser um número positivo.'))
                        error_occurred = True
                except (ValueError, TypeError):
                    messages.error(request, _('Item ID deve ser um número válido.'))
                    error_occurred = True
            
            if not item_name:
                messages.error(request, _('Preencha o nome do item.'))
                error_occurred = True
            
            # Validação de enchant e quantity
            enchant_int = 0
            quantity_int = 1
            try:
                enchant_int = int(enchant) if enchant else 0
                if enchant_int < 0:
                    messages.error(request, _('Encantamento não pode ser negativo.'))
                    error_occurred = True
                    
                quantity_int = int(quantity) if quantity else 1
                if quantity_int <= 0:
                    messages.error(request, _('Quantidade deve ser maior que zero.'))
                    error_occurred = True
            except (ValueError, TypeError):
                messages.error(request, _('Encantamento e quantidade devem ser números válidos.'))
                error_occurred = True
            
            # Se houver erro, renderiza o template novamente
            if error_occurred:
                return render(request, 'level_rewards/manager/reward_create.html', {})
            
            recompensa = Recompensa.objects.create(
                tipo='NIVEL',
                referencia=str(nivel_int),
                item_id=item_id_int,
                item_name=item_name,
                enchant=enchant_int,
                quantity=quantity_int,
                created_by=request.user
            )
            
            messages.success(request, _('Recompensa por level criada com sucesso!'))
            return redirect('games:level_rewards_manager_reward_list')
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            messages.error(request, _('Erro ao criar recompensa: {}').format(str(e)))
            # Log do erro para debug
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Erro ao criar recompensa por level: {error_detail}')
    
    return render(request, 'level_rewards/manager/reward_create.html', {})


@staff_required
@transaction.atomic
def reward_edit(request, reward_id):
    """Editar recompensa por level"""
    recompensa = get_object_or_404(Recompensa, id=reward_id, tipo='NIVEL')
    
    if request.method == 'POST':
        try:
            nivel = request.POST.get('nivel')
            item_id = request.POST.get('item_id')
            item_name = request.POST.get('item_name')
            enchant = request.POST.get('enchant', 0)
            quantity = request.POST.get('quantity', 1)
            
            if not all([nivel, item_id, item_name]):
                messages.error(request, _('Preencha todos os campos obrigatórios.'))
                return redirect('games:level_rewards_manager_reward_edit', reward_id=reward_id)
            
            # Validação
            try:
                nivel_int = int(nivel)
                if nivel_int <= 0:
                    messages.error(request, _('O nível deve ser maior que zero.'))
                    return redirect('games:level_rewards_manager_reward_edit', reward_id=reward_id)
                
                item_id_int = int(item_id)
                if item_id_int <= 0:
                    messages.error(request, _('Item ID deve ser um número positivo.'))
                    return redirect('games:level_rewards_manager_reward_edit', reward_id=reward_id)
                
                enchant_int = int(enchant) if enchant else 0
                if enchant_int < 0:
                    messages.error(request, _('Encantamento não pode ser negativo.'))
                    return redirect('games:level_rewards_manager_reward_edit', reward_id=reward_id)
                
                quantity_int = int(quantity) if quantity else 1
                if quantity_int <= 0:
                    messages.error(request, _('Quantidade deve ser maior que zero.'))
                    return redirect('games:level_rewards_manager_reward_edit', reward_id=reward_id)
            except (ValueError, TypeError):
                messages.error(request, _('Valores numéricos inválidos.'))
                return redirect('games:level_rewards_manager_reward_edit', reward_id=reward_id)
            
            recompensa.referencia = str(nivel_int)
            recompensa.item_id = item_id_int
            recompensa.item_name = item_name
            recompensa.enchant = enchant_int
            recompensa.quantity = quantity_int
            recompensa.save()
            
            messages.success(request, _('Recompensa atualizada com sucesso!'))
            return redirect('games:level_rewards_manager_reward_list')
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar recompensa: {}').format(str(e)))
    
    context = {
        'recompensa': recompensa,
    }
    return render(request, 'level_rewards/manager/reward_edit.html', context)


@staff_required
@transaction.atomic
def reward_delete(request, reward_id):
    """Deletar recompensa por level"""
    recompensa = get_object_or_404(Recompensa, id=reward_id, tipo='NIVEL')
    
    if request.method == 'POST':
        try:
            recompensa_nome = str(recompensa)
            recompensa.delete()
            messages.success(request, _('Recompensa "{}" deletada com sucesso!').format(recompensa_nome))
            return redirect('games:level_rewards_manager_reward_list')
        except Exception as e:
            messages.error(request, _('Erro ao deletar recompensa: {}').format(str(e)))
            return redirect('games:level_rewards_manager_reward_list')
    
    context = {
        'recompensa': recompensa,
    }
    return render(request, 'level_rewards/manager/reward_delete.html', context)

