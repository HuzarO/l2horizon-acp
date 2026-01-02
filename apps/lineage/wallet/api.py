"""
API interna para processamento de transferências de wallet.
Esta API é chamada internamente para evitar timeouts no worker do Gunicorn.
"""
import logging
import hashlib
import time
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.throttling import UserRateThrottle
from apps.main.home.decorator import conditional_otp_required
from .models import Wallet, CoinConfig
from .signals import aplicar_transacao, aplicar_transacao_bonus
from apps.lineage.server.database import LineageDB
from apps.lineage.server.services.account_context import get_active_login
from apps.main.home.models import PerfilGamer
from utils.dynamic_import import get_query_class
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

TransferFromWalletToChar = get_query_class("TransferFromWalletToChar")


class WalletTransferThrottle(UserRateThrottle):
    """
    Throttle customizado para transferências de wallet.
    Limite: 1 requisição por minuto por usuário.
    """
    rate = '1/minute'
    scope = 'wallet_transfer'


class InternalTransferToServerAPI(APIView):
    """
    API interna para processar transferências de wallet para o servidor.
    Esta API é chamada internamente e pode ter timeout maior.
    Aceita autenticação via sessão ou JWT.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]  # Aceita autenticação via sessão
    throttle_classes = [WalletTransferThrottle]  # Rate limit: 1 requisição por minuto
    
    def dispatch(self, request, *args, **kwargs):
        # Garante que o usuário está autenticado via sessão
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticação necessária.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        """
        Processa transferência de wallet para o servidor.
        
        Parâmetros esperados:
        - personagem: nome do personagem
        - valor: valor em R$ (Decimal)
        - origem_saldo: 'normal' ou 'bonus'
        """
        try:
            # ========== FASE 1: VALIDAÇÃO E SANITIZAÇÃO DOS DADOS ==========
            nome_personagem = request.data.get('personagem', '').strip()
            valor_str = request.data.get('valor', '').strip()
            origem_saldo = request.data.get('origem_saldo', 'normal')

            if not nome_personagem:
                return Response(
                    {'error': 'Personagem não informado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                valor = Decimal(valor_str)
            except (ValueError, TypeError, InvalidOperation):
                logger.warning(f"Tentativa de transferência com valor inválido: {valor_str} (usuário: {request.user.username})")
                return Response(
                    {'error': 'Valor inválido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if valor < 1 or valor > 1000:
                return Response(
                    {'error': 'Só é permitido transferir entre R$1,00 e R$1.000,00.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ========== FASE 2: VALIDAÇÃO DE CONFIGURAÇÃO ==========
            config = CoinConfig.objects.filter(ativa=True).first()
            if not config:
                return Response(
                    {'error': 'Nenhuma moeda configurada está ativa no momento.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            COIN_ID = config.coin_id
            multiplicador = config.multiplicador

            if origem_saldo == 'bonus':
                if not getattr(config, 'habilitar_transferencia_com_bonus', False):
                    return Response(
                        {'error': 'Transferência usando saldo bônus está desabilitada.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            active_login = get_active_login(request)

            # ========== FASE 3: VALIDAÇÃO NO BANCO DO LINEAGE ==========
            db = LineageDB()
            if not db.is_connected():
                logger.error(f"Banco do Lineage desconectado durante transferência (usuário: {request.user.username})")
                return Response(
                    {'error': 'O banco do jogo está indisponível no momento. Tente novamente mais tarde.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Confirma se o personagem pertence à conta
            personagem = TransferFromWalletToChar.find_char(active_login, nome_personagem)
            if not personagem:
                logger.warning(f"Tentativa de transferência para personagem inválido: {nome_personagem} (usuário: {request.user.username})")
                return Response(
                    {'error': 'Personagem inválido ou não pertence a essa conta.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not TransferFromWalletToChar.items_delayed:
                if personagem[0].get('online', 0) != 0:
                    return Response(
                        {'error': 'O personagem precisa estar offline.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # ========== FASE 4: PROTEÇÃO CONTRA REQUISIÇÕES DUPLICADAS ==========
            request_hash_data = f"{request.user.id}:{nome_personagem}:{valor}:{origem_saldo}"
            request_hash = hashlib.md5(request_hash_data.encode()).hexdigest()
            cache_key = f"wallet_transfer_{request.user.id}_{request_hash}"
            cache_lock_key = f"wallet_transfer_lock_{request.user.id}_{request_hash}"

            # Verifica se esta requisição idêntica já está sendo processada
            cache_data = cache.get(cache_key)
            if cache_data:
                if isinstance(cache_data, dict) and cache_data.get('status') == 'processing':
                    elapsed = time.time() - cache_data.get('started_at', 0)
                    if elapsed < 300:  # 5 minutos
                        logger.info(f"Transferência duplicada bloqueada: {cache_key} (usuário: {request.user.username})")
                        return Response(
                            {'error': 'Esta transferência já está sendo processada. Aguarde alguns instantes.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                        )

            # Tenta adquirir lock
            lock_acquired = cache.add(cache_lock_key, True, timeout=10)
            if not lock_acquired:
                return Response(
                    {'error': 'Outra transferência está sendo processada. Aguarde alguns instantes.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            try:
                # Marca como em processamento
                cache.set(cache_key, {
                    'status': 'processing',
                    'started_at': time.time(),
                    'user_id': request.user.id,
                    'valor': str(valor),
                    'personagem': nome_personagem
                }, timeout=300)

                # ========== FASE 5: PROCESSAMENTO DA TRANSFERÊNCIA ==========
                quantidade_moedas = Decimal(valor) * Decimal(multiplicador)
                amount = int(round(quantidade_moedas))

                logger.info(f"Iniciando transferência via API: usuário={request.user.username}, personagem={nome_personagem}, valor={valor}, moedas={amount}")

                # Transação atômica para operações no banco Django
                with transaction.atomic():
                    wallet = Wallet.objects.select_for_update().get(usuario=request.user)

                    # Validação de saldo dentro da transação (com lock)
                    if origem_saldo == 'bonus':
                        if wallet.saldo_bonus < valor:
                            raise ValueError(_('Saldo bônus insuficiente.'))
                    else:
                        if wallet.saldo < valor:
                            raise ValueError(_('Saldo insuficiente.'))

                    # Registra a saída na carteira ANTES de inserir moedas no Lineage
                    if origem_saldo == 'bonus':
                        aplicar_transacao_bonus(
                            wallet=wallet,
                            tipo="SAIDA",
                            valor=valor,
                            descricao="Transferência para o servidor (bônus)",
                            origem=active_login,
                            destino=nome_personagem
                        )
                    else:
                        aplicar_transacao(
                            wallet=wallet,
                            tipo="SAIDA",
                            valor=valor,
                            descricao="Transferência para o servidor",
                            origem=active_login,
                            destino=nome_personagem
                        )

                # ========== FASE 6: INSERÇÃO NO BANCO DO LINEAGE ==========
                # Esta operação está FORA da transação do Django porque é outro banco
                try:
                    sucesso = TransferFromWalletToChar.insert_coin(
                        char_name=nome_personagem,
                        coin_id=COIN_ID,
                        amount=amount
                    )

                    if not sucesso:
                        # Reverte a transação da carteira
                        logger.error(f"Falha ao inserir moedas no Lineage: personagem={nome_personagem}, amount={amount}")
                        self._reverter_transacao(request.user, valor, origem_saldo, active_login, nome_personagem)
                        return Response(
                            {'error': 'Erro ao adicionar a moeda ao personagem. O valor foi revertido.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                except Exception as lineage_error:
                    # Se houver timeout ou erro no Lineage, reverte a carteira
                    logger.error(f"Erro ao inserir moedas no Lineage: {str(lineage_error)} (usuário: {request.user.username})")
                    self._reverter_transacao(request.user, valor, origem_saldo, active_login, nome_personagem)
                    return Response(
                        {'error': 'Erro ao adicionar a moeda ao personagem. O valor foi revertido automaticamente.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # ========== FASE 7: SUCESSO ==========
                cache.set(cache_key, {
                    'status': 'completed',
                    'completed_at': time.time(),
                    'user_id': request.user.id,
                    'valor': str(valor),
                    'personagem': nome_personagem
                }, timeout=300)

                # Adiciona XP
                perfil, created = PerfilGamer.objects.get_or_create(user=request.user)
                perfil.adicionar_xp(40)

                logger.info(f"Transferência concluída com sucesso via API: usuário={request.user.username}, personagem={nome_personagem}, valor={valor}")

                return Response({
                    'success': True,
                    'message': f"R${valor:.2f} transferidos com sucesso para o personagem {nome_personagem}." if origem_saldo == 'normal' else f"R${valor:.2f} do bônus transferidos com sucesso para o personagem {nome_personagem}.",
                    'valor': float(valor),
                    'personagem': nome_personagem,
                    'moedas': amount
                }, status=status.HTTP_200_OK)

            except ValueError as ve:
                logger.warning(f"Erro de validação na transferência: {str(ve)} (usuário: {request.user.username})")
                cache.delete(cache_key)
                return Response(
                    {'error': str(ve)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            except Exception as e:
                logger.error(f"Erro durante transferência: {str(e)} (usuário: {request.user.username}, personagem: {nome_personagem})", exc_info=True)
                cache.delete(cache_key)
                return Response(
                    {'error': f'Ocorreu um erro durante a transferência: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            finally:
                # Sempre libera o lock
                cache.delete(cache_lock_key)

        except Exception as e:
            logger.error(f"Erro crítico na API de transferência: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Erro interno do servidor. Tente novamente mais tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _reverter_transacao(self, user, valor, origem_saldo, active_login, nome_personagem):
        """Reverte uma transação em caso de erro no Lineage."""
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(usuario=user)
                if origem_saldo == 'bonus':
                    aplicar_transacao_bonus(
                        wallet=wallet,
                        tipo="ENTRADA",
                        valor=valor,
                        descricao="Reversão: Erro ao transferir para servidor (bônus)",
                        origem=nome_personagem,
                        destino=active_login
                    )
                else:
                    aplicar_transacao(
                        wallet=wallet,
                        tipo="ENTRADA",
                        valor=valor,
                        descricao="Reversão: Erro ao transferir para servidor",
                        origem=nome_personagem,
                        destino=active_login
                    )
        except Exception as revert_error:
            logger.critical(f"ERRO CRÍTICO: Falha ao reverter transação após erro no Lineage: {str(revert_error)} (usuário: {user.username}, valor: {valor})")
            # Marca no cache para investigação manual
            cache.set(f"wallet_revert_error_{user.id}_{int(time.time())}", {
                'user_id': user.id,
                'valor': str(valor),
                'personagem': nome_personagem,
                'origem_saldo': origem_saldo,
                'revert_error': str(revert_error),
                'timestamp': timezone.now().isoformat()
            }, timeout=86400)  # 24 horas
