import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from django.utils import timezone
from django.utils.translation import get_language

from .services import AIAssistantService
from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatBotConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket para o chatbot de IA"""

    async def connect(self):
        """Conecta o usuário ao WebSocket"""
        if self.scope["user"].is_anonymous:
            raise DenyConnection("Usuário não autenticado")

        self.user = self.scope["user"]
        self.user_group_name = f"chatbot_{self.user.id}"
        self.session = None

        # Adicionar ao grupo do usuário
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

        # Enviar mensagem de boas-vindas
        await self.send(text_data=json.dumps({
            "type": "welcome",
            "message": "Olá! Sou o assistente virtual do PDL. Como posso ajudá-lo hoje?",
            "timestamp": timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Desconecta o usuário"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Recebe mensagem do cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'message':
                await self.handle_user_message(data)
            elif message_type == 'create_session':
                await self.handle_create_session()
            elif message_type == 'load_session':
                await self.handle_load_session(data.get('session_id'))
            elif message_type == 'create_solicitation':
                await self.handle_create_solicitation(data)
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Tipo de mensagem desconhecido"
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Formato JSON inválido"
            }))
        except Exception as e:
            logger.error(f"Erro em receive: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Erro interno do servidor"
            }))

    async def handle_user_message(self, data):
        """Processa mensagem do usuário e gera resposta da IA"""
        message_content = data.get('message', '').strip()

        if not message_content:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Mensagem vazia não é permitida"
            }))
            return

        # Obter ou criar sessão
        if not self.session:
            self.session = await self.get_or_create_session()

        # Salvar mensagem do usuário
        user_message = await self.save_message(
            session=self.session,
            role='user',
            content=message_content
        )

        # Enviar confirmação de recebimento
        await self.send(text_data=json.dumps({
            "type": "message_received",
            "message_id": user_message.id,
            "timestamp": user_message.created_at.isoformat()
        }))

        # Enviar indicador de digitação
        await self.send(text_data=json.dumps({
            "type": "typing",
            "status": True
        }))

        try:
            # Obter histórico de mensagens
            history = await self.get_conversation_history(self.session)

            # Gerar resposta da IA (chamada síncrona em contexto async)
            language = get_language()
            
            # Wrapper para gerar resposta de forma assíncrona
            def generate_response():
                service = AIAssistantService()
                return service.generate_response(message_content, history, language)
            
            response_text, metadata = await database_sync_to_async(generate_response)()

            # Salvar mensagem da IA
            assistant_message = await self.save_message(
                session=self.session,
                role='assistant',
                content=response_text,
                metadata=metadata,
                tokens_used=metadata.get('tokens_used', 0)
            )

            # Atualizar título da sessão se for a primeira mensagem
            message_count = await self.get_message_count(self.session)
            if message_count == 2:  # user + assistant
                await self.update_session_title(self.session, message_content)

            # Enviar resposta
            await self.send(text_data=json.dumps({
                "type": "message",
                "message": {
                    "id": assistant_message.id,
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": assistant_message.created_at.isoformat(),
                    "metadata": metadata
                }
            }))

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
            
            # Mensagem de erro amigável para o usuário
            error_message_user = (
                "Desculpe, ocorreu um erro ao processar sua mensagem. "
                "Por favor, tente novamente ou crie uma solicitação de suporte se o problema persistir."
            )
            
            # Salvar mensagem de erro amigável no banco
            try:
                await self.save_message(
                    session=self.session,
                    role='assistant',
                    content=error_message_user,
                    metadata={"error": True, "error_type": "processing_error"},
                    tokens_used=0
                )
            except Exception as save_error:
                logger.error(f"Erro ao salvar mensagem de erro: {str(save_error)}")
            
            await self.send(text_data=json.dumps({
                "type": "message",
                "message": {
                    "id": None,
                    "role": "assistant",
                    "content": error_message_user,
                    "timestamp": timezone.now().isoformat(),
                    "metadata": {"error": True}
                }
            }))
        finally:
            # Remover indicador de digitação
            await self.send(text_data=json.dumps({
                "type": "typing",
                "status": False
            }))

    async def handle_create_session(self):
        """Cria uma nova sessão de chat"""
        self.session = await self.create_new_session()
        await self.send(text_data=json.dumps({
            "type": "session_created",
            "session_id": self.session.id,
            "timestamp": self.session.created_at.isoformat()
        }))

    async def handle_load_session(self, session_id):
        """Carrega uma sessão existente"""
        if not session_id:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "ID da sessão não fornecido"
            }))
            return

        self.session = await self.load_session(session_id)

        if not self.session:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Sessão não encontrada"
            }))
            return

        # Carregar histórico de mensagens
        messages = await self.get_conversation_history(self.session)
        
        await self.send(text_data=json.dumps({
            "type": "session_loaded",
            "session_id": self.session.id,
            "messages": messages,
            "timestamp": self.session.created_at.isoformat()
        }))

    async def handle_create_solicitation(self, data):
        """Cria uma solicitação baseada na conversa"""
        if not self.session:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Nenhuma sessão ativa"
            }))
            return

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'general')
        priority = data.get('priority', 'medium')

        if not title or not description:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Título e descrição são obrigatórios"
            }))
            return

        try:
            solicitation = await self.create_solicitation_from_session(
                session=self.session,
                title=title,
                description=description,
                category=category,
                priority=priority
            )

            await self.send(text_data=json.dumps({
                "type": "solicitation_created",
                "solicitation": {
                    "id": solicitation.id,
                    "protocol": solicitation.protocol,
                    "title": solicitation.title,
                    "status": solicitation.status
                }
            }))

        except Exception as e:
            logger.error(f"Erro ao criar solicitação: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Erro ao criar solicitação: {str(e)}"
            }))

    # Métodos auxiliares usando database_sync_to_async

    @database_sync_to_async
    def get_or_create_session(self):
        """Obtém ou cria uma sessão de chat para o usuário"""
        session, created = ChatSession.objects.get_or_create(
            user=self.user,
            is_active=True
        )
        if created:
            session.save()
        return session

    @database_sync_to_async
    def create_new_session(self):
        """Cria uma nova sessão de chat"""
        session = ChatSession.objects.create(
            user=self.user,
            is_active=True
        )
        return session

    @database_sync_to_async
    def load_session(self, session_id):
        """Carrega uma sessão por ID"""
        try:
            return ChatSession.objects.get(
                id=session_id,
                user=self.user
            )
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def get_conversation_history(self, session):
        """Obtém histórico de conversa formatado para a IA"""
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        return history

    @database_sync_to_async
    def save_message(self, session, role, content, metadata=None, tokens_used=0):
        """Salva uma mensagem no banco de dados"""
        message = ChatMessage.objects.create(
            session=session,
            role=role,
            content=content,
            metadata=metadata or {},
            tokens_used=tokens_used,
            created_by=self.user
        )
        return message

    @database_sync_to_async
    def update_session_title(self, session, first_message):
        """Atualiza o título da sessão baseado na primeira mensagem"""
        if not session.title:
            title = first_message[:50] + "..." if len(first_message) > 50 else first_message
            session.title = title
            session.save()

    @database_sync_to_async
    def get_message_count(self, session):
        """Retorna o número de mensagens de uma sessão"""
        return ChatMessage.objects.filter(session=session).count()

    @database_sync_to_async
    def create_solicitation_from_session(self, session, title, description, category, priority):
        """Cria uma solicitação relacionada à sessão"""
        from apps.main.solicitation.models import Solicitation

        # Obter contexto da conversa
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        conversation_context = "\n".join([
            f"{msg.role}: {msg.content}" for msg in messages
        ])
        
        full_description = f"{description}\n\n---\nContexto da conversa com o assistente:\n{conversation_context}"

        solicitation = Solicitation.objects.create(
            user=self.user,
            title=title,
            description=full_description,
            category=category,
            priority=priority,
            created_by=self.user
        )

        # Associar solicitação à sessão
        session.solicitation = solicitation
        session.save()

        return solicitation
