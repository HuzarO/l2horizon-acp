from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db import transaction

from .models import Notification, NotificationReward
from utils.notifications import send_notification
from apps.lineage.games.models import Item
from apps.lineage.inventory.models import CustomItem


@staff_member_required
def manager_dashboard(request):
    """Dashboard de gerenciamento de notificações"""
    
    # Estatísticas gerais
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(viewed=False).count()
    notifications_with_rewards = Notification.objects.filter(rewards__isnull=False).distinct().count()
    total_rewards_claimed = Notification.objects.filter(rewards_claimed=True).count()
    
    # Notificações por tipo
    notifications_by_type = Notification.objects.values('notification_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Notificações recentes
    recent_notifications = Notification.objects.select_related('user').prefetch_related('rewards').order_by('-created_at')[:10]
    
    # Prêmios mais entregues
    top_rewards = NotificationReward.objects.values('item_name', 'item_id').annotate(
        total_amount=Count('id'),
        total_quantity=Count('item_amount')
    ).order_by('-total_amount')[:5]
    
    context = {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'notifications_with_rewards': notifications_with_rewards,
        'total_rewards_claimed': total_rewards_claimed,
        'notifications_by_type': notifications_by_type,
        'recent_notifications': recent_notifications,
        'top_rewards': top_rewards,
    }
    
    return render(request, 'notification/manager/dashboard.html', context)


@staff_member_required
def notification_list(request):
    """Lista todas as notificações"""
    
    # Filtros
    notification_type = request.GET.get('type', '')
    has_rewards = request.GET.get('has_rewards', '')
    viewed = request.GET.get('viewed', '')
    search = request.GET.get('search', '')
    
    notifications = Notification.objects.select_related('user').prefetch_related('rewards').all()
    
    # Aplicar filtros
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if has_rewards == 'yes':
        notifications = notifications.filter(rewards__isnull=False).distinct()
    elif has_rewards == 'no':
        notifications = notifications.filter(rewards__isnull=True)
    
    if viewed == 'yes':
        notifications = notifications.filter(viewed=True)
    elif viewed == 'no':
        notifications = notifications.filter(viewed=False)
    
    if search:
        notifications = notifications.filter(
            Q(message__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Ordenação
    order_by = request.GET.get('order_by', '-created_at')
    notifications = notifications.order_by(order_by)
    
    # Paginação
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    notifications_page = paginator.get_page(page)
    
    context = {
        'notifications': notifications_page,
        'notification_type': notification_type,
        'has_rewards': has_rewards,
        'viewed': viewed,
        'search': search,
        'order_by': order_by,
    }
    
    return render(request, 'notification/manager/list.html', context)


@staff_member_required
def notification_create(request):
    """Criar nova notificação"""
    
    if request.method == 'POST':
        try:
            # Dados básicos
            notification_type = request.POST.get('notification_type', 'user')
            message = request.POST.get('message', '')
            link = request.POST.get('link', '') or None
            user_id = request.POST.get('user_id', '') or None
            is_public = request.POST.get('is_public', '') == 'on'
            
            if not message:
                messages.error(request, _('A mensagem é obrigatória.'))
                return redirect('notification:manager_create')
            
            # Determinar usuário
            user = None
            if not is_public and user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    messages.error(request, _('Usuário não encontrado.'))
                    return redirect('notification:manager_create')
            
            # Processar prêmios
            rewards = []
            reward_count = int(request.POST.get('reward_count', 0))
            
            for i in range(reward_count):
                reward_type = request.POST.get(f'reward_{i}_type', 'item')
                item_id = request.POST.get(f'reward_{i}_item_id', '')
                item_name = request.POST.get(f'reward_{i}_item_name', '')
                item_enchant = int(request.POST.get(f'reward_{i}_item_enchant', 0) or 0)
                item_amount = int(request.POST.get(f'reward_{i}_item_amount', 1) or 1)
                fichas_amount = request.POST.get(f'reward_{i}_fichas_amount', '')
                
                if reward_type == 'fichas' and fichas_amount:
                    # Prêmio de fichas
                    fichas_amount = int(fichas_amount or 0)
                    if fichas_amount > 0:
                        rewards.append({
                            'fichas_amount': fichas_amount,
                        })
                elif reward_type == 'item' and item_id and item_name:
                    # Prêmio de item
                    rewards.append({
                        'item_id': int(item_id),
                        'item_name': item_name,
                        'item_enchant': item_enchant,
                        'item_amount': item_amount,
                    })
            
            # Criar notificação
            notification = send_notification(
                user=user if not is_public else None,
                notification_type=notification_type,
                message=message,
                created_by=request.user,
                link=link,
                rewards=rewards if rewards else None
            )
            
            messages.success(request, _('Notificação criada com sucesso!'))
            return redirect('notification:manager_detail', pk=notification.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao criar notificação: {}').format(str(e)))
    
    # Buscar itens para autocomplete
    items = Item.objects.all()[:100]  # Limitar para performance
    custom_items = CustomItem.objects.all()[:100]
    
    context = {
        'items': items,
        'custom_items': custom_items,
    }
    
    return render(request, 'notification/manager/create.html', context)


@staff_member_required
def notification_detail(request, pk):
    """Detalhes de uma notificação"""
    
    notification = get_object_or_404(
        Notification.objects.select_related('user').prefetch_related('rewards'),
        pk=pk
    )
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notification/manager/detail.html', context)


@staff_member_required
def notification_delete(request, pk):
    """Deletar notificação"""
    
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk)
        notification.delete()
        messages.success(request, _('Notificação deletada com sucesso!'))
        return redirect('notification:manager_list')
    
    return redirect('notification:manager_detail', pk=pk)


@staff_member_required
def get_item_info(request):
    """API para buscar informações de um item"""
    
    item_id = request.GET.get('item_id')
    
    if not item_id:
        return JsonResponse({'error': 'item_id é obrigatório'}, status=400)
    
    try:
        item_id = int(item_id)
        
        # Tentar buscar em CustomItem primeiro
        try:
            custom_item = CustomItem.objects.get(item_id=item_id)
            return JsonResponse({
                'item_id': custom_item.item_id,
                'item_name': custom_item.nome or f'Item {item_id}',
                'found': True,
            })
        except CustomItem.DoesNotExist:
            pass
        
        # Tentar buscar em Item
        try:
            item = Item.objects.get(id=item_id)
            return JsonResponse({
                'item_id': item_id,
                'item_name': item.name or f'Item {item_id}',
                'found': True,
            })
        except Item.DoesNotExist:
            pass
        
        # Item não encontrado, retornar apenas o ID
        return JsonResponse({
            'item_id': item_id,
            'item_name': f'Item {item_id}',
            'found': False,
        })
        
    except ValueError:
        return JsonResponse({'error': 'item_id inválido'}, status=400)

