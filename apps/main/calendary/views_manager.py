from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Event


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def manager_dashboard(request):
    """Dashboard de gerenciamento do Calendário"""
    
    # Estatísticas gerais
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_date__gte=timezone.now()).count()
    past_events = Event.objects.filter(end_date__lt=timezone.now()).count()
    ongoing_events = Event.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).count()
    
    # Eventos próximos (próximos 7 dias)
    next_week = timezone.now() + timedelta(days=7)
    upcoming_week_events = Event.objects.filter(
        start_date__gte=timezone.now(),
        start_date__lte=next_week
    ).order_by('start_date')[:5]
    
    # Eventos por cor
    events_by_color = Event.objects.values('className').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'ongoing_events': ongoing_events,
        'upcoming_week_events': upcoming_week_events,
        'events_by_color': events_by_color,
    }
    
    return render(request, 'calendary/manager/dashboard.html', context)


@staff_required
def event_list(request):
    """Lista todos os eventos"""
    events = Event.objects.select_related('user').order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'upcoming':
        events = events.filter(start_date__gte=timezone.now())
    elif status_filter == 'past':
        events = events.filter(end_date__lt=timezone.now())
    elif status_filter == 'ongoing':
        events = events.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
    
    color_filter = request.GET.get('color', 'all')
    if color_filter != 'all':
        events = events.filter(className=color_filter)
    
    context = {
        'events': events,
        'status_filter': status_filter,
        'color_filter': color_filter,
    }
    return render(request, 'calendary/manager/event_list.html', context)


@staff_required
@transaction.atomic
def event_create(request):
    """Criar novo evento"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            user_id = request.POST.get('user')
            className = request.POST.get('className', 'bg-red')
            
            if not title or not start_date or not end_date:
                messages.error(request, _('Preencha todos os campos obrigatórios.'))
                return redirect('calendary:manager_event_create')
            
            # Validar datas
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if end < start:
                messages.error(request, _('A data de término não pode ser anterior à data de início.'))
                return redirect('calendary:manager_event_create')
            
            event = Event.objects.create(
                title=title,
                start_date=start,
                end_date=end,
                className=className,
                user_id=int(user_id) if user_id else None
            )
            
            messages.success(request, _('Evento criado com sucesso!'))
            return redirect('calendary:manager_event_detail', event_id=event.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao criar evento: {}').format(str(e)))
    
    from apps.main.home.models import User
    users = User.objects.all().order_by('username')
    context = {
        'users': users,
        'color_choices': Event._meta.get_field('className').choices,
    }
    return render(request, 'calendary/manager/event_create.html', context)


@staff_required
@transaction.atomic
def event_edit(request, event_id):
    """Editar evento existente"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        try:
            event.title = request.POST.get('title', event.title)
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            user_id = request.POST.get('user')
            event.className = request.POST.get('className', event.className)
            
            if start_date and end_date:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                if end < start:
                    messages.error(request, _('A data de término não pode ser anterior à data de início.'))
                    return redirect('calendary:manager_event_edit', event_id=event.id)
                
                event.start_date = start
                event.end_date = end
            
            if user_id:
                event.user_id = int(user_id) if user_id else None
            else:
                event.user = None
            
            event.save()
            
            messages.success(request, _('Evento atualizado com sucesso!'))
            return redirect('calendary:manager_event_detail', event_id=event.id)
            
        except Exception as e:
            messages.error(request, _('Erro ao atualizar evento: {}').format(str(e)))
    
    from apps.main.home.models import User
    users = User.objects.all().order_by('username')
    context = {
        'event': event,
        'users': users,
        'color_choices': Event._meta.get_field('className').choices,
    }
    return render(request, 'calendary/manager/event_edit.html', context)


@staff_required
def event_detail(request, event_id):
    """Detalhes do evento"""
    event = get_object_or_404(Event.objects.select_related('user'), id=event_id)
    
    # Calcular duração
    duration = None
    status = None
    now = timezone.now()
    
    if event.start_date and event.end_date:
        duration = event.end_date - event.start_date
        
        if now < event.start_date:
            status = 'upcoming'
        elif event.start_date <= now <= event.end_date:
            status = 'ongoing'
        else:
            status = 'past'
    
    context = {
        'event': event,
        'duration': duration,
        'status': status,
        'now': now,
    }
    return render(request, 'calendary/manager/event_detail.html', context)


@staff_required
@transaction.atomic
def event_delete(request, event_id):
    """Deletar evento"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, _('Evento "{}" deletado com sucesso!').format(event_title))
        return redirect('calendary:manager_event_list')
    
    context = {
        'event': event,
    }
    return render(request, 'calendary/manager/event_delete.html', context)

