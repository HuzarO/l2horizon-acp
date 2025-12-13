from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView
from django.utils.translation import gettext_lazy as _
from .models import ChatSession, ChatMessage


class ChatBotView(LoginRequiredMixin, View):
    """View principal do chatbot"""
    template_name = 'pages/chatbot.html'

    def get(self, request):
        # Limpar mensagens Django para não gerar notificações flutuantes
        from django.contrib.messages import get_messages
        list(get_messages(request))  # Consumir todas as mensagens para limpar
        
        context = {
            'segment': 'chatbot',
            'parent': 'ai_assistant',
            'messages': [],  # Sobrescrever messages Django para evitar notificações
        }
        return render(request, self.template_name, context)


class ChatSessionListView(LoginRequiredMixin, ListView):
    """Lista de sessões de chat do usuário"""
    model = ChatSession
    template_name = 'pages/chatbot_sessions.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        # Anotar com contagem de mensagens para melhor performance
        from django.db.models import Count
        return ChatSession.objects.filter(
            user=self.request.user
        ).annotate(
            message_count=Count('messages')
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Limpar mensagens Django para não gerar notificações flutuantes
        from django.contrib.messages import get_messages
        list(get_messages(self.request))  # Consumir todas as mensagens para limpar
        
        context['segment'] = 'chatbot_sessions'
        context['parent'] = 'ai_assistant'
        context['messages'] = []  # Sobrescrever messages Django para evitar notificações
        return context


class ChatSessionDetailView(LoginRequiredMixin, View):
    """Detalhes de uma sessão de chat específica"""
    template_name = 'pages/chatbot_session_detail.html'

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            messages = ChatMessage.objects.filter(session=session).order_by('created_at')
            
            # Sanitizar mensagens para remover detalhes técnicos de erros
            cleaned_messages = []
            for msg in messages:
                # Se a mensagem contém detalhes técnicos de erro, limpar
                if msg.role == 'assistant' and msg.content:
                    cleaned_content = self._sanitize_error_message(msg.content)
                    # Criar uma cópia da mensagem com conteúdo limpo (sem modificar o banco)
                    msg.cleaned_content = cleaned_content
                cleaned_messages.append(msg)
            
            # Limpar mensagens Django para não gerar notificações flutuantes
            from django.contrib.messages import get_messages
            # Consumir todas as mensagens Django para limpar o storage
            list(get_messages(request))
            
            # Limpar mensagens Django do contexto para evitar notificações
            from django.contrib.messages import get_messages
            list(get_messages(request))  # Consumir mensagens do storage
            
            context = {
                'session': session,
                'chat_messages': cleaned_messages,  # Renomeado para evitar conflito
                'messages': [],  # Sobrescrever messages Django para evitar notificações
                'segment': 'chatbot_session',
                'parent': 'ai_assistant',
            }
            return render(request, self.template_name, context)
        except ChatSession.DoesNotExist:
            from django.http import Http404
            raise Http404(_("Sessão não encontrada"))
    
    def _sanitize_error_message(self, content):
        """Remove detalhes técnicos de mensagens de erro"""
        import re
        
        # Se contém Error code ou detalhes de API, substituir por mensagem amigável
        if re.search(r'Error code:\s*\d+', content) or 'invalid_request_error' in content.lower():
            # Verificar tipo de erro
            if 'credit balance is too low' in content.lower() or 'credits' in content.lower():
                return (
                    "Desculpe, o serviço de IA está temporariamente indisponível. "
                    "Nossa equipe foi notificada e está trabalhando para resolver. "
                    "Por favor, crie uma solicitação de suporte para que possamos atendê-lo diretamente."
                )
            elif 'invalid_request_error' in content.lower() or '400' in content:
                return (
                    "Desculpe, houve um problema ao processar sua solicitação. "
                    "Por favor, tente reformular sua pergunta ou crie uma solicitação de suporte."
                )
            elif '401' in content or 'unauthorized' in content.lower():
                return (
                    "Desculpe, há um problema de configuração com o serviço de IA. "
                    "Nossa equipe foi notificada. Por favor, crie uma solicitação de suporte."
                )
            elif '429' in content or 'rate limit' in content.lower():
                return (
                    "Desculpe, o serviço está temporariamente sobrecarregado. "
                    "Por favor, aguarde alguns instantes e tente novamente."
                )
            else:
                return (
                    "Desculpe, ocorreu um erro ao processar sua mensagem. "
                    "Por favor, tente novamente ou crie uma solicitação de suporte."
                )
        
        return content
