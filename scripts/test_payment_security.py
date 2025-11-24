#!/usr/bin/env python3
"""
Script de Teste de Segurança de Pagamentos
Testa tentativas de falsificação de pagamentos do Stripe e Mercado Pago

AVISO: Este script é apenas para testes de segurança em ambiente de desenvolvimento.
NUNCA execute em produção sem autorização explícita.
"""

import os
import sys
import json
import hmac
import hashlib
import time
import requests
from decimal import Decimal
from pathlib import Path

# Configuração do Django - normaliza caminhos para evitar problemas de case no Windows
BASE_DIR = Path(__file__).resolve().parent.parent

# Normaliza e limpa sys.path para evitar duplicatas (problema comum no Windows)
normalized_paths = []
seen_lower = set()

# Adiciona o diretório base normalizado primeiro
base_path_str = str(BASE_DIR.resolve())
base_lower = base_path_str.lower()
if base_lower not in seen_lower:
    normalized_paths.append(base_path_str)
    seen_lower.add(base_lower)

# Adiciona outros caminhos do sys.path, normalizando e removendo duplicatas
for path in sys.path:
    if path:
        try:
            normalized = str(Path(path).resolve())
            path_lower = normalized.lower()
            if path_lower not in seen_lower:
                normalized_paths.append(normalized)
                seen_lower.add(path_lower)
        except (OSError, ValueError):
            # Se não conseguir normalizar, mantém o original se não estiver duplicado
            path_lower = path.lower()
            if path_lower not in seen_lower:
                normalized_paths.append(path)
                seen_lower.add(path_lower)

sys.path = normalized_paths

# Define o diretório de trabalho
os.chdir(BASE_DIR)

# Configura o módulo de settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Importa e configura Django
# Nota: A normalização de caminhos acima resolve o problema de "multiple filesystem locations"
# que ocorre no Windows quando o mesmo módulo é encontrado com case diferente (d: vs D:)
try:
    import django
    django.setup()
except ImportError as exc:
    raise ImportError(
        "Couldn't import Django. Are you sure it's installed and "
        "available on your PYTHONPATH environment variable? Did you "
        "forget to activate a virtual environment?"
    ) from exc
except Exception as e:
    if 'multiple filesystem locations' in str(e):
        print(f"Erro: {e}", file=sys.stderr)
        print("\nDica: Este erro geralmente ocorre no Windows devido a diferenças de case.", file=sys.stderr)
        print("Tente executar o script a partir do diretório raiz do projeto:", file=sys.stderr)
        print(f"  cd {BASE_DIR}", file=sys.stderr)
        print(f"  python scripts/test_payment_security.py", file=sys.stderr)
        sys.exit(1)
    raise

from django.conf import settings
from apps.lineage.payment.models import Pagamento, PedidoPagamento
from apps.lineage.wallet.models import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

# Cores para output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_test(name, description):
    print(f"{Colors.YELLOW}[TESTE]{Colors.RESET} {Colors.BOLD}{name}{Colors.RESET}")
    print(f"  {description}")

def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")

def print_failure(message):
    print(f"{Colors.RED}✗{Colors.RESET} {message}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


class StripeSecurityTester:
    """Testa segurança dos webhooks do Stripe"""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.webhook_url = f"{self.base_url}/app/payment/stripe/webhook/"
        self.success_url = f"{self.base_url}/app/payment/stripe/sucesso/"
        
    def test_1_no_signature(self):
        """Teste 1: Tentar enviar webhook sem assinatura"""
        print_test("Stripe - Sem Assinatura", 
                  "Tentando enviar webhook sem header Stripe-Signature")
        
        payload = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "amount_total": 10000,  # R$ 100.00
                    "metadata": {
                        "pagamento_id": "999"
                    }
                }
            }
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print_success("Webhook rejeitado corretamente (400)")
            return True
        else:
            print_failure(f"Webhook aceito indevidamente! Status: {response.status_code}")
            return False
    
    def test_2_fake_signature(self):
        """Teste 2: Tentar enviar webhook com assinatura falsa"""
        print_test("Stripe - Assinatura Falsa", 
                  "Tentando enviar webhook com assinatura inválida")
        
        payload = {
            "id": "evt_test_456",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_456",
                    "amount_total": 20000,
                    "metadata": {
                        "pagamento_id": "999"
                    }
                }
            }
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Stripe-Signature': 't=1234567890,v1=fake_signature_here'
            }
        )
        
        if response.status_code == 400:
            print_success("Webhook rejeitado corretamente (400)")
            return True
        else:
            print_failure(f"Webhook aceito indevidamente! Status: {response.status_code}")
            return False
    
    def test_3_modified_value(self):
        """Teste 3: Tentar modificar valor do pagamento (se passar validação)"""
        print_test("Stripe - Valor Modificado", 
                  "Tentando enviar webhook com valor diferente do pagamento original")
        
        # Primeiro, precisamos criar um pagamento real para testar
        try:
            user = User.objects.first()
            if not user:
                print_info("Nenhum usuário encontrado. Criando usuário de teste...")
                user = User.objects.create_user(
                    username='test_security',
                    email='test@test.com',
                    password='test123'
                )
            
            # Criar pedido e pagamento
            pedido = PedidoPagamento.objects.create(
                usuario=user,
                valor_pago=Decimal('50.00'),
                moedas_geradas=Decimal('50.00'),
                metodo='Stripe',
                status='PENDENTE'
            )
            
            pagamento = Pagamento.objects.create(
                usuario=user,
                valor=Decimal('50.00'),
                status='pending',
                pedido_pagamento=pedido,
                transaction_code='cs_test_modified'
            )
            
            # Tentar enviar webhook com valor maior
            payload = {
                "id": f"evt_test_{int(time.time())}",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_modified",
                        "amount_total": 50000,  # R$ 500.00 (10x o valor original)
                        "metadata": {
                            "pagamento_id": str(pagamento.id)
                        }
                    }
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Stripe-Signature': 't=1234567890,v1=fake_signature'
                }
            )
            
            if response.status_code == 400:
                print_success("Webhook rejeitado (assinatura inválida)")
                print_info("NOTA: Se a assinatura fosse válida, o sistema deveria validar o valor")
            else:
                print_failure(f"Webhook processado! Status: {response.status_code}")
            
            # Limpar
            pagamento.delete()
            pedido.delete()
            
            return response.status_code == 400
            
        except Exception as e:
            print_failure(f"Erro no teste: {e}")
            return False
    
    def test_4_fake_success_url(self):
        """Teste 4: Tentar acessar URL de sucesso com session_id falso"""
        print_test("Stripe - URL de Sucesso Falsa", 
                  "Tentando acessar endpoint de sucesso com session_id inválido")
        
        response = requests.get(
            self.success_url,
            params={'session_id': 'cs_fake_session_12345'},
            allow_redirects=False  # Não seguir redirecionamentos para ver o status real
        )
        
        # Deve redirecionar para erro (302) ou retornar erro (400, 404, 500)
        # Status 200 significa que renderizou a página de sucesso, o que é um problema de segurança
        if response.status_code == 302:
            # Verifica se redirecionou para a página de erro
            location = response.headers.get('Location', '')
            if 'erro' in location.lower() or 'error' in location.lower():
                print_success("Redirecionado para página de erro corretamente")
                return True
            else:
                print_failure(f"Redirecionou, mas não para página de erro. Location: {location}")
                return False
        elif response.status_code in [400, 404, 500]:
            print_success("Acesso negado corretamente")
            return True
        else:
            print_failure(f"Acesso permitido indevidamente! Status: {response.status_code}")
            print_info("NOTA: O endpoint deve validar o session_id com a API do Stripe antes de processar")
            return False
    
    def test_5_replay_attack(self):
        """Teste 5: Tentar replay attack (reenviar mesmo evento)"""
        print_test("Stripe - Replay Attack", 
                  "Tentando reenviar o mesmo evento webhook")
        
        event_id = f"evt_replay_{int(time.time())}"
        payload = {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_replay_test",
                    "amount_total": 10000,
                    "metadata": {
                        "pagamento_id": "999"
                    }
                }
            }
        }
        
        # Primeira requisição (será rejeitada por assinatura, mas testamos idempotência)
        response1 = requests.post(
            self.webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Stripe-Signature': 't=1234567890,v1=fake'
            }
        )
        
        # Segunda requisição (mesmo evento)
        response2 = requests.post(
            self.webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Stripe-Signature': 't=1234567890,v1=fake'
            }
        )
        
        print_info("Ambas as requisições devem ser rejeitadas por assinatura inválida")
        print_info("NOTA: O sistema usa WebhookLog para prevenir duplicação")
        
        return response1.status_code == 400 and response2.status_code == 400


class MercadoPagoSecurityTester:
    """Testa segurança dos webhooks do Mercado Pago"""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.webhook_url = f"{self.base_url}/app/payment/mercadopago/notificacao/"
        self.success_url = f"{self.base_url}/app/payment/mercadopago/sucesso/"
        
    def generate_fake_hmac(self, data_id, request_id, timestamp):
        """Gera HMAC falso para teste"""
        manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
        fake_secret = "fake_secret_key_for_testing"
        hmac_obj = hmac.new(fake_secret.encode(), manifest.encode(), hashlib.sha256)
        return hmac_obj.hexdigest()
    
    def generate_valid_hmac(self, data_id, request_id, timestamp):
        """Gera HMAC válido usando o secret real (apenas para comparação)"""
        try:
            secret = settings.MERCADO_PAGO_WEBHOOK_SECRET
            manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
            hmac_obj = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256)
            return hmac_obj.hexdigest()
        except:
            return None
    
    def test_1_no_signature(self):
        """Teste 1: Tentar enviar webhook sem assinatura HMAC"""
        print_test("Mercado Pago - Sem Assinatura", 
                  "Tentando enviar webhook sem headers x-signature e x-request-id")
        
        payload = {
            "type": "payment",
            "data": {
                "id": "123456789"
            }
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print_success("Webhook rejeitado corretamente (400)")
            return True
        else:
            print_failure(f"Webhook aceito indevidamente! Status: {response.status_code}")
            return False
    
    def test_2_fake_hmac(self):
        """Teste 2: Tentar enviar webhook com HMAC falso"""
        print_test("Mercado Pago - HMAC Falso", 
                  "Tentando enviar webhook com assinatura HMAC inválida")
        
        data_id = "123456789"
        request_id = "req_test_123"
        timestamp = str(int(time.time()))
        
        fake_v1 = self.generate_fake_hmac(data_id, request_id, timestamp)
        
        payload = {
            "type": "payment",
            "data": {
                "id": data_id
            }
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'x-signature': f'ts={timestamp},v1={fake_v1}',
                'x-request-id': request_id
            }
        )
        
        if response.status_code == 400:
            print_success("Webhook rejeitado corretamente (400)")
            return True
        else:
            print_failure(f"Webhook aceito indevidamente! Status: {response.status_code}")
            return False
    
    def test_3_modified_value(self):
        """Teste 3: Tentar modificar valor do pagamento"""
        print_test("Mercado Pago - Valor Modificado", 
                  "Tentando enviar webhook com valor diferente do pagamento original")
        
        try:
            user = User.objects.first()
            if not user:
                user = User.objects.create_user(
                    username='test_mp_security',
                    email='testmp@test.com',
                    password='test123'
                )
            
            # Criar pedido e pagamento
            pedido = PedidoPagamento.objects.create(
                usuario=user,
                valor_pago=Decimal('30.00'),
                moedas_geradas=Decimal('30.00'),
                metodo='MercadoPago',
                status='PENDENTE'
            )
            
            pagamento = Pagamento.objects.create(
                usuario=user,
                valor=Decimal('30.00'),
                status='pending',
                pedido_pagamento=pedido,
                transaction_code='123456789'
            )
            
            # Tentar enviar webhook com valor maior (será rejeitado por HMAC)
            data_id = "123456789"
            request_id = "req_test_modified"
            timestamp = str(int(time.time()))
            fake_v1 = self.generate_fake_hmac(data_id, request_id, timestamp)
            
            payload = {
                "type": "payment",
                "data": {
                    "id": data_id
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-signature': f'ts={timestamp},v1={fake_v1}',
                    'x-request-id': request_id
                }
            )
            
            if response.status_code == 400:
                print_success("Webhook rejeitado (HMAC inválido)")
                print_info("NOTA: O sistema valida o valor consultando a API do Mercado Pago")
            else:
                print_failure(f"Webhook processado! Status: {response.status_code}")
            
            # Limpar
            pagamento.delete()
            pedido.delete()
            
            return response.status_code == 400
            
        except Exception as e:
            print_failure(f"Erro no teste: {e}")
            return False
    
    def test_4_fake_success_url(self):
        """Teste 4: Tentar acessar URL de sucesso com payment_id falso"""
        print_test("Mercado Pago - URL de Sucesso Falsa", 
                  "Tentando acessar endpoint de sucesso com payment_id inválido")
        
        response = requests.get(
            self.success_url,
            params={
                'payment_id': '999999999999',
                'status': 'approved'
            },
            allow_redirects=False  # Não seguir redirecionamentos para ver o status real
        )
        
        # Deve redirecionar para erro (302) ou retornar erro (400, 404, 500)
        # Status 200 significa que renderizou a página de sucesso, o que é um problema de segurança
        if response.status_code == 302:
            # Verifica se redirecionou para a página de erro
            location = response.headers.get('Location', '')
            if 'erro' in location.lower() or 'error' in location.lower():
                print_success("Redirecionado para página de erro corretamente")
                return True
            else:
                print_failure(f"Redirecionou, mas não para página de erro. Location: {location}")
                return False
        elif response.status_code in [400, 404, 500]:
            print_success("Acesso negado corretamente")
            return True
        else:
            print_failure(f"Acesso permitido indevidamente! Status: {response.status_code}")
            print_info("NOTA: O endpoint deve validar o payment_id com a API do Mercado Pago antes de processar")
            return False
    
    def test_5_replay_attack(self):
        """Teste 5: Tentar replay attack"""
        print_test("Mercado Pago - Replay Attack", 
                  "Tentando reenviar o mesmo evento webhook")
        
        data_id = f"replay_{int(time.time())}"
        request_id = f"req_replay_{int(time.time())}"
        timestamp = str(int(time.time()))
        fake_v1 = self.generate_fake_hmac(data_id, request_id, timestamp)
        
        payload = {
            "type": "payment",
            "data": {
                "id": data_id
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'x-signature': f'ts={timestamp},v1={fake_v1}',
            'x-request-id': request_id
        }
        
        # Primeira requisição
        response1 = requests.post(self.webhook_url, json=payload, headers=headers)
        
        # Segunda requisição (mesmo evento)
        response2 = requests.post(self.webhook_url, json=payload, headers=headers)
        
        print_info("Ambas as requisições devem ser rejeitadas por HMAC inválido")
        print_info("NOTA: O sistema usa WebhookLog para prevenir duplicação")
        
        return response1.status_code == 400 and response2.status_code == 400
    
    def test_6_malformed_signature(self):
        """Teste 6: Tentar enviar assinatura malformada"""
        print_test("Mercado Pago - Assinatura Malformada", 
                  "Tentando enviar webhook com assinatura em formato inválido")
        
        payload = {
            "type": "payment",
            "data": {
                "id": "123456789"
            }
        }
        
        # Teste com assinatura malformada
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'x-signature': 'invalid_format',
                'x-request-id': 'req_test'
            }
        )
        
        if response.status_code == 400:
            print_success("Webhook rejeitado corretamente (400)")
            return True
        else:
            print_failure(f"Webhook aceito indevidamente! Status: {response.status_code}")
            return False


def main():
    """Executa todos os testes de segurança"""
    print_header("TESTE DE SEGURANÇA DE PAGAMENTOS")
    print_info("Este script testa tentativas de falsificação de pagamentos")
    print_info("AVISO: Execute apenas em ambiente de desenvolvimento/teste\n")
    
    # Obter URL base
    base_url = input("Digite a URL base do servidor (ex: http://localhost:6085): ").strip()
    if not base_url:
        base_url = "http://localhost:6085"
    
    print(f"\nUsando URL base: {base_url}\n")
    
    results = {
        'stripe': [],
        'mercadopago': []
    }
    
    # Testes Stripe
    print_header("TESTES STRIPE")
    stripe_tester = StripeSecurityTester(base_url)
    
    results['stripe'].append(("Sem Assinatura", stripe_tester.test_1_no_signature()))
    results['stripe'].append(("Assinatura Falsa", stripe_tester.test_2_fake_signature()))
    results['stripe'].append(("Valor Modificado", stripe_tester.test_3_modified_value()))
    results['stripe'].append(("URL Sucesso Falsa", stripe_tester.test_4_fake_success_url()))
    results['stripe'].append(("Replay Attack", stripe_tester.test_5_replay_attack()))
    
    # Testes Mercado Pago
    print_header("TESTES MERCADO PAGO")
    mp_tester = MercadoPagoSecurityTester(base_url)
    
    results['mercadopago'].append(("Sem Assinatura", mp_tester.test_1_no_signature()))
    results['mercadopago'].append(("HMAC Falso", mp_tester.test_2_fake_hmac()))
    results['mercadopago'].append(("Valor Modificado", mp_tester.test_3_modified_value()))
    results['mercadopago'].append(("URL Sucesso Falsa", mp_tester.test_4_fake_success_url()))
    results['mercadopago'].append(("Replay Attack", mp_tester.test_5_replay_attack()))
    results['mercadopago'].append(("Assinatura Malformada", mp_tester.test_6_malformed_signature()))
    
    # Resumo
    print_header("RESUMO DOS TESTES")
    
    print(f"\n{Colors.BOLD}STRIPE:{Colors.RESET}")
    for name, passed in results['stripe']:
        status = f"{Colors.GREEN}✓ PASSOU{Colors.RESET}" if passed else f"{Colors.RED}✗ FALHOU{Colors.RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{Colors.BOLD}MERCADO PAGO:{Colors.RESET}")
    for name, passed in results['mercadopago']:
        status = f"{Colors.GREEN}✓ PASSOU{Colors.RESET}" if passed else f"{Colors.RED}✗ FALHOU{Colors.RESET}"
        print(f"  {name}: {status}")
    
    # Estatísticas
    total_tests = len(results['stripe']) + len(results['mercadopago'])
    passed_tests = sum(1 for _, passed in results['stripe'] + results['mercadopago'] if passed)
    
    print(f"\n{Colors.BOLD}Total: {passed_tests}/{total_tests} testes passaram{Colors.RESET}\n")
    
    if passed_tests == total_tests:
        print_success("Todos os testes de segurança passaram! ✓")
    else:
        print_failure("Alguns testes falharam. Revise a implementação de segurança.")


if __name__ == '__main__':
    main()

