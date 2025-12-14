import os
import logging
import json
import re
from typing import List, Dict, Optional, Tuple
from anthropic import Anthropic
import google.generativeai as genai
import openai
from django.conf import settings
from django.utils.translation import get_language
from apps.main.faq.models import FAQ, FAQTranslation
from apps.main.solicitation.models import Solicitation
from apps.main.solicitation.choices import CATEGORY_CHOICES, PRIORITY_CHOICES
from .models import AIProviderConfig

logger = logging.getLogger(__name__)


class AIAssistantService:
    """Serviço para interação com a IA (Anthropic/Claude, Google Gemini ou xAI Grok)"""

    def __init__(self):
        # Obter provedor ativo da configuração
        self.provider = AIProviderConfig.get_active_provider()
        
        # Inicializar clientes baseado no provedor
        self.anthropic_client = None
        self.gemini_client = None
        self.grok_client = None
        
        if self.provider == 'anthropic':
            api_key = os.environ.get('ANTHROPIC_API_KEY') or getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY não configurada. O serviço de IA não funcionará.")
            else:
                self.anthropic_client = Anthropic(api_key=api_key)
        elif self.provider == 'gemini':
            api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
            if not api_key:
                logger.warning("GEMINI_API_KEY não configurada. O serviço de IA não funcionará.")
            else:
                genai.configure(api_key=api_key)
                # O cliente será criado dinamicamente em _generate_gemini_response
                self.gemini_client = True  # Flag para indicar que está configurado
        elif self.provider == 'grok':
            api_key = os.environ.get('XAI_API_KEY') or getattr(settings, 'XAI_API_KEY', None)
            if not api_key:
                logger.warning("XAI_API_KEY não configurada. O serviço de IA não funcionará.")
            else:
                # Grok usa o SDK da OpenAI com base_url customizado
                self.grok_client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://api.x.ai/v1"
                )

    def get_faq_context(self, language: str = 'pt') -> str:
        """Obtém contexto das FAQs públicas para incluir no prompt"""
        try:
            faqs = FAQ.objects.filter(is_public=True)
            context_parts = []
            
            for faq in faqs[:20]:  # Limitar a 20 FAQs para não exceder o contexto
                translation = faq.translations.filter(language=language).first()
                if translation:
                    context_parts.append(
                        f"P: {translation.question}\nR: {translation.answer}\n"
                    )
            
            return "\n".join(context_parts) if context_parts else ""
        except Exception as e:
            logger.error(f"Erro ao buscar FAQs: {str(e)}")
            return ""

    def get_solicitation_categories_context(self) -> str:
        """Retorna contexto sobre categorias de solicitação"""
        categories = dict(CATEGORY_CHOICES)
        priorities = dict(PRIORITY_CHOICES)
        
        return f"""
Categorias de solicitação disponíveis:
{chr(10).join([f"- {key}: {value}" for key, value in categories.items()])}

Prioridades disponíveis:
{chr(10).join([f"- {key}: {value}" for key, value in priorities.items()])}
"""

    def create_system_prompt(self, language: str = 'pt') -> str:
        """Cria o prompt do sistema para a IA"""
        faq_context = self.get_faq_context(language)
        
        system_prompt = f"""Você é um assistente virtual de pré-atendimento para o Painel Definitivo Lineage (PDL), 
um sistema de gerenciamento para servidores privados de Lineage 2.

Sua função PRINCIPAL é responder perguntas usando as FAQs abaixo e resolver dúvidas simples.

INSTRUÇÕES IMPORTANTES:
1. Tente SEMPRE responder a pergunta do usuário usando as FAQs ou seu conhecimento
2. Seja útil, objetivo e resolva a dúvida quando possível
3. NÃO sugira criar solicitação a menos que seja realmente necessário
4. Só sugira criar solicitação quando:
   - A questão for muito complexa e não puder ser resolvida pelo chat
   - Envolver problemas técnicos que precisam de intervenção (bugs, erros críticos)
   - Envolver questões sensíveis (conta comprometida, segurança, pagamentos não processados)
   - O usuário explicitamente pedir ajuda humana ou reportar um problema
   - Não houver informação suficiente nas FAQs para ajudar adequadamente

5. NÃO sugira criar solicitação para:
   - Perguntas simples que você pode responder
   - Dúvidas sobre funcionalidades que estão nas FAQs
   - Questões que você conseguiu resolver ou explicar

FORMATO DE RESPOSTA:
- Responda diretamente à pergunta do usuário
- Se precisar sugerir uma solicitação, adicione no FINAL da resposta, de forma discreta:
  "Se precisar de ajuda adicional, posso ajudar você a criar uma solicitação de suporte."

Ao sugerir criar uma solicitação, use o formato JSON especial no final:
<suggestion>
{{
  "suggest": true,
  "category": "categoria_aqui",
  "priority": "prioridade_aqui",
  "reason": "breve justificativa"
}}
</suggestion>

FAQs Disponíveis:
{faq_context if faq_context else "Nenhuma FAQ disponível no momento."}

{self.get_solicitation_categories_context()}

Seja útil e objetivo. Priorize resolver a dúvida ao invés de direcionar para suporte."""
        
        return system_prompt

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        language: str = 'pt'
    ) -> Tuple[str, Dict]:
        """
        Gera uma resposta da IA baseada na mensagem do usuário
        
        Returns:
            Tuple[str, Dict]: (resposta_texto, metadados)
        """
        # Verificar se o cliente está disponível
        if self.provider == 'anthropic' and not self.anthropic_client:
            return (
                "Desculpe, o serviço de IA não está disponível no momento. "
                "Por favor, crie uma solicitação de suporte ou entre em contato com nossa equipe.",
                {"error": "IA service not available", "suggest_create_solicitation": True}
            )
        elif self.provider == 'gemini' and not self.gemini_client:
            return (
                "Desculpe, o serviço de IA não está disponível no momento. "
                "Por favor, crie uma solicitação de suporte ou entre em contato com nossa equipe.",
                {"error": "IA service not available", "suggest_create_solicitation": True}
            )
        elif self.provider == 'grok' and not self.grok_client:
            return (
                "Desculpe, o serviço de IA não está disponível no momento. "
                "Por favor, crie uma solicitação de suporte ou entre em contato com nossa equipe.",
                {"error": "IA service not available", "suggest_create_solicitation": True}
            )

        try:
            # Criar prompt do sistema
            system_prompt = self.create_system_prompt(language)

            # Chamar o método apropriado baseado no provedor
            if self.provider == 'anthropic':
                return self._generate_anthropic_response(
                    user_message, conversation_history, system_prompt
                )
            elif self.provider == 'gemini':
                return self._generate_gemini_response(
                    user_message, conversation_history, system_prompt
                )
            elif self.provider == 'grok':
                return self._generate_grok_response(
                    user_message, conversation_history, system_prompt
                )
            else:
                raise ValueError(f"Provedor desconhecido: {self.provider}")

        except Exception as e:
            # Log completo do erro para debug (não enviar ao usuário)
            error_details = str(e)
            logger.error(f"Erro ao gerar resposta da IA: {error_details}", exc_info=True)
            
            # Tratar erros específicos da API e retornar mensagem amigável SEM detalhes técnicos
            error_message_lower = error_details.lower()
            user_friendly_message = "Desculpe, ocorreu um erro ao processar sua mensagem."
            should_suggest = True
            
            if "credit balance is too low" in error_message_lower or "credits" in error_message_lower:
                user_friendly_message = (
                    "Desculpe, o serviço de IA está temporariamente indisponível. "
                    "Nossa equipe foi notificada e está trabalhando para resolver. "
                    "Por favor, crie uma solicitação de suporte para que possamos atendê-lo diretamente."
                )
                should_suggest = True
            elif "api key" in error_message_lower or "incorrect api key" in error_message_lower:
                user_friendly_message = (
                    "Desculpe, há um problema de configuração com o serviço de IA. "
                    "Nossa equipe foi notificada. Por favor, crie uma solicitação de suporte."
                )
                should_suggest = True
            elif "invalid_request_error" in error_message_lower or ("400" in error_message_lower and "api key" not in error_message_lower):
                user_friendly_message = (
                    "Desculpe, houve um problema ao processar sua solicitação. "
                    "Por favor, tente reformular sua pergunta ou crie uma solicitação de suporte."
                )
                should_suggest = True
            elif "401" in error_message_lower or "unauthorized" in error_message_lower:
                user_friendly_message = (
                    "Desculpe, há um problema de configuração com o serviço de IA. "
                    "Nossa equipe foi notificada. Por favor, crie uma solicitação de suporte."
                )
                should_suggest = True
            elif "429" in error_message_lower or "rate limit" in error_message_lower:
                user_friendly_message = (
                    "Desculpe, o serviço está temporariamente sobrecarregado. "
                    "Por favor, aguarde alguns instantes e tente novamente."
                )
                should_suggest = False  # Rate limit é temporário
            else:
                user_friendly_message = (
                    "Desculpe, ocorreu um erro inesperado ao processar sua mensagem. "
                    "Por favor, tente novamente ou crie uma solicitação de suporte."
                )
                should_suggest = True
            
            # Retornar apenas mensagem amigável (sem detalhes técnicos no conteúdo)
            # Detalhes técnicos ficam apenas nos logs e no metadata
            return (
                user_friendly_message,
                {
                    "error": True,  # Flag de erro (sem detalhes técnicos)
                    "error_type": "api_error",
                    "suggest_create_solicitation": should_suggest, 
                    "category_suggestion": "technical" if should_suggest else None, 
                    "priority_suggestion": "high" if should_suggest else None,
                    "tokens_used": 0
                }
            )

    def _extract_suggestion_from_message(self, message: str) -> Dict:
        """Extrai sugestão estruturada da mensagem usando formato XML-like"""
        # Procura por tag <suggestion>
        pattern = r'<suggestion>\s*(\{.*?\})\s*</suggestion>'
        match = re.search(pattern, message, re.DOTALL)
        
        if match:
            try:
                suggestion_json = json.loads(match.group(1))
                return suggestion_json
            except json.JSONDecodeError:
                pass
        
        return {"suggest": False}
    
    def _remove_suggestion_tag(self, message: str) -> str:
        """Remove a tag de sugestão da mensagem final"""
        pattern = r'<suggestion>.*?</suggestion>'
        cleaned = re.sub(pattern, '', message, flags=re.DOTALL)
        return cleaned.strip()
    
    def _should_suggest_solicitation(self, message: str) -> bool:
        """Verifica se a resposta sugere criar uma solicitação de forma natural"""
        # Palavras-chave mais específicas que indicam necessidade real de suporte
        strong_keywords = [
            "não consigo resolver", "preciso de ajuda adicional", 
            "não encontrei a solução", "problema técnico", "bug",
            "erro crítico", "conta comprometida", "segurança",
            "pagamento não processado", "perda de acesso"
        ]
        
        # Verificar se há contexto suficiente na mensagem
        message_lower = message.lower()
        
        # Se a mensagem é muito curta ou genérica, não sugerir
        if len(message.strip()) < 50:
            return False
        
        # Verificar keywords fortes
        has_strong_keyword = any(keyword in message_lower for keyword in strong_keywords)
        
        # Verificar se menciona explicitamente necessidade de suporte humano
        explicit_support = any(phrase in message_lower for phrase in [
            "criar uma solicitação", "abrir um ticket", "contatar o suporte",
            "equipe de suporte", "ajuda humana", "atendimento humano"
        ])
        
        return has_strong_keyword or explicit_support

    def _extract_category_suggestion(self, message: str) -> Optional[str]:
        """Extrai sugestão de categoria da resposta"""
        categories = dict(CATEGORY_CHOICES)
        message_lower = message.lower()
        
        for key, value in categories.items():
            if key.lower() in message_lower or value.lower() in message_lower:
                return key
        
        return None

    def _extract_priority_suggestion(self, message: str) -> Optional[str]:
        """Extrai sugestão de prioridade da resposta"""
        priorities = dict(PRIORITY_CHOICES)
        message_lower = message.lower()
        
        # Palavras-chave para prioridades
        priority_keywords = {
            'urgent': ['urgente', 'emergência', 'crítico'],
            'high': ['alta', 'importante', 'rapidamente'],
            'medium': ['média', 'normal'],
            'low': ['baixa', 'não urgente']
        }
        
        for key, keywords in priority_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return key
        
        return 'medium'  # Default

    def _generate_anthropic_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: str
    ) -> Tuple[str, Dict]:
        """Gera resposta usando Anthropic/Claude"""
        try:
            # Preparar histórico de conversa
            messages = []
            if conversation_history:
                # Converter histórico para formato Anthropic (últimas 20 mensagens)
                recent_history = conversation_history[-20:]
                for msg in recent_history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Adicionar mensagem atual
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Lista de modelos para tentar (do mais recente ao mais antigo)
            # Priorizar Sonnet (balanceado), depois Haiku (rápido), depois Opus (mais capaz)
            model_names = [
                'claude-sonnet-4-5-20250929',  # Mais recente Sonnet
                'claude-haiku-4-5-20251001',  # Mais recente Haiku
                'claude-opus-4-1-20250805',   # Mais recente Opus
                'claude-3-5-sonnet-20241022', # Versão anterior Sonnet
                'claude-3-5-haiku-20241022', # Versão anterior Haiku
                'claude-3-opus-20240229',    # Versão anterior Opus
                'claude-3-sonnet-20240229',  # Versão anterior Sonnet
                'claude-3-haiku-20240307',   # Versão anterior Haiku
            ]
            
            last_error = None
            response = None
            
            # Tentar cada modelo até encontrar um que funcione
            for model_name in model_names:
                try:
                    response = self.anthropic_client.messages.create(
                        model=model_name,
                        max_tokens=1024,
                        system=system_prompt,
                        messages=messages
                    )
                    logger.info(f"Usando modelo Anthropic: {model_name}")
                    break  # Sucesso, sair do loop
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    # Se for erro 404 (modelo não encontrado), tentar próximo
                    if '404' in error_str or 'not_found' in error_str:
                        logger.warning(f"Modelo {model_name} não disponível, tentando próximo...")
                        continue
                    else:
                        # Se for outro tipo de erro, re-lançar
                        raise e
            
            if response is None:
                raise Exception(f"Nenhum modelo Anthropic disponível. Último erro: {str(last_error)}")

            # Extrair resposta
            assistant_message = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Processar sugestões e metadados
            return self._process_response(assistant_message, tokens_used)

        except Exception as api_error:
            raise api_error

    def _generate_gemini_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: str
    ) -> Tuple[str, Dict]:
        """Gera resposta usando Google Gemini"""
        try:
            # Preparar histórico de conversa para Gemini
            # Gemini usa um formato diferente: lista de mensagens alternadas
            chat_history = []
            if conversation_history:
                recent_history = conversation_history[-20:]
                for msg in recent_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    # Gemini usa 'user' e 'model' ao invés de 'assistant'
                    if role == 'assistant':
                        role = 'model'
                    chat_history.append({
                        "role": role,
                        "parts": [content]
                    })
            
            # Criar modelo com system instruction (Gemini 1.5+ suporta)
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            # Primeiro, listar modelos disponíveis para garantir que usamos um que funciona
            model = None
            available_model_name = None
            
            try:
                # Listar todos os modelos disponíveis
                all_models = genai.list_models()
                # Filtrar modelos que suportam generateContent
                available_models = [
                    m for m in all_models 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                if not available_models:
                    raise Exception("Nenhum modelo Gemini disponível para generateContent")
                
                # Priorizar modelos flash (mais rápidos e baratos)
                preferred_models = ['flash', 'pro']
                selected_model = None
                
                for preferred in preferred_models:
                    for m in available_models:
                        model_name = m.name.split('/')[-1]  # Extrair apenas o nome
                        if preferred in model_name.lower():
                            selected_model = m
                            break
                    if selected_model:
                        break
                
                # Se não encontrou um preferido, usar o primeiro disponível
                if not selected_model:
                    selected_model = available_models[0]
                
                available_model_name = selected_model.name.split('/')[-1]
                logger.info(f"Usando modelo Gemini: {available_model_name}")
                
            except Exception as list_error:
                logger.warning(f"Erro ao listar modelos: {str(list_error)}. Tentando modelos padrão...")
                # Fallback: tentar modelos padrão
                model_names = [
                    'gemini-1.5-flash-latest',
                    'gemini-1.5-flash',
                    'gemini-1.0-pro-latest',
                    'gemini-pro',
                ]
                
                for model_name in model_names:
                    try:
                        # Testar se o modelo funciona
                        test_model = genai.GenerativeModel(model_name=model_name)
                        test_model.generate_content("test")
                        available_model_name = model_name
                        logger.info(f"Usando modelo padrão: {available_model_name}")
                        break
                    except Exception as e:
                        logger.warning(f"Modelo {model_name} não disponível: {str(e)}")
                        continue
                
                if not available_model_name:
                    raise Exception(f"Não foi possível encontrar um modelo Gemini disponível. Erro: {str(list_error)}")
            
            # Criar o modelo com o nome encontrado
            # Tentar com system_instruction primeiro, se falhar, tentar sem
            try:
                model = genai.GenerativeModel(
                    model_name=available_model_name,
                    system_instruction=system_prompt,
                    generation_config=generation_config
                )
            except Exception as e:
                # Se system_instruction não for suportado, criar sem ele
                logger.warning(f"Modelo não suporta system_instruction, usando prompt no início: {str(e)}")
                model = genai.GenerativeModel(
                    model_name=available_model_name,
                    generation_config=generation_config
                )
                # Incluir system prompt no início da mensagem
                user_message = f"{system_prompt}\n\n{user_message}"
            
            # Se há histórico, criar chat; senão, usar generate_content diretamente
            if chat_history:
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(user_message)
            else:
                response = model.generate_content(user_message)
            
            # Extrair resposta
            assistant_message = response.text
            
            # Tentar obter informações de uso de tokens se disponível
            if hasattr(response, 'usage_metadata'):
                tokens_used = (
                    response.usage_metadata.prompt_token_count + 
                    response.usage_metadata.candidates_token_count
                )
            else:
                # Estimativa: 1 token ≈ 4 caracteres
                full_prompt = f"{system_prompt}\n\n{user_message}"
                tokens_used = len(full_prompt) // 4 + len(assistant_message) // 4

            # Processar sugestões e metadados
            return self._process_response(assistant_message, tokens_used)

        except Exception as api_error:
            raise api_error

    def _generate_grok_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: str
    ) -> Tuple[str, Dict]:
        """Gera resposta usando xAI Grok"""
        try:
            # Preparar mensagens para Grok (formato OpenAI-compatible)
            messages = []
            
            # Adicionar system prompt
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Adicionar histórico de conversa (últimas 20 mensagens)
            if conversation_history:
                recent_history = conversation_history[-20:]
                for msg in recent_history:
                    role = msg.get("role", "user")
                    # Grok usa 'assistant' ao invés de 'model'
                    if role == 'model':
                        role = 'assistant'
                    messages.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
            
            # Adicionar mensagem atual
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Lista de modelos Grok para tentar (do mais recente ao mais antigo)
            model_names = [
                'grok-2-1212',  # Mais recente
                'grok-2-vision-1212',
                'grok-beta',
                'grok-2',
            ]
            
            last_error = None
            response = None
            
            # Tentar cada modelo até encontrar um que funcione
            for model_name in model_names:
                try:
                    response = self.grok_client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=1024,
                        temperature=0.7
                    )
                    logger.info(f"Usando modelo Grok: {model_name}")
                    break  # Sucesso, sair do loop
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    # Se for erro 404 (modelo não encontrado), tentar próximo
                    if '404' in error_str or 'not_found' in error_str or ('model' in error_str and 'not found' in error_str):
                        logger.warning(f"Modelo {model_name} não disponível, tentando próximo...")
                        continue
                    elif 'api key' in error_str or 'incorrect api key' in error_str or ('401' in error_str and 'api' in error_str):
                        # Erro de API key - não tentar outros modelos, retornar erro amigável
                        logger.error(f"API key do Grok inválida: {str(e)}")
                        return (
                            "Desculpe, há um problema de configuração com o serviço de IA. "
                            "Nossa equipe foi notificada. Por favor, crie uma solicitação de suporte.",
                            {
                                "error": True,
                                "error_type": "api_key_error",
                                "suggest_create_solicitation": True,
                                "category_suggestion": "technical",
                                "priority_suggestion": "high",
                                "tokens_used": 0
                            }
                        )
                    else:
                        # Se for outro tipo de erro, re-lançar
                        raise e
            
            if response is None:
                raise Exception(f"Nenhum modelo Grok disponível. Último erro: {str(last_error)}")
            
            # Extrair resposta
            assistant_message = response.choices[0].message.content
            
            # Obter informações de uso de tokens
            if hasattr(response, 'usage'):
                tokens_used = (
                    response.usage.prompt_tokens + 
                    response.usage.completion_tokens
                )
            else:
                # Estimativa: 1 token ≈ 4 caracteres
                full_prompt = system_prompt + "\n\n" + "\n".join([m["content"] for m in messages[1:]])
                tokens_used = len(full_prompt) // 4 + len(assistant_message) // 4

            # Processar sugestões e metadados
            return self._process_response(assistant_message, tokens_used)

        except Exception as api_error:
            raise api_error

    def _process_response(self, assistant_message: str, tokens_used: int) -> Tuple[str, Dict]:
        """Processa a resposta de qualquer provedor e extrai metadados"""
        # Verificar se há sugestão estruturada na resposta
        suggestion_data = self._extract_suggestion_from_message(assistant_message)
        
        # Se não houver sugestão estruturada, verificar se a mensagem indica sugestão naturalmente
        if not suggestion_data.get("suggest", False):
            suggestion_data = {
                "suggest": self._should_suggest_solicitation(assistant_message),
                "category": self._extract_category_suggestion(assistant_message),
                "priority": self._extract_priority_suggestion(assistant_message),
                "reason": None
            }
        
        # Remover tag de sugestão da mensagem final (se existir)
        cleaned_message = self._remove_suggestion_tag(assistant_message)
        
        metadata = {
            "tokens_used": tokens_used,
            "provider": self.provider,
            "suggest_create_solicitation": suggestion_data.get("suggest", False),
            "category_suggestion": suggestion_data.get("category"),
            "priority_suggestion": suggestion_data.get("priority"),
            "suggestion_reason": suggestion_data.get("reason"),
        }

        return cleaned_message, metadata
