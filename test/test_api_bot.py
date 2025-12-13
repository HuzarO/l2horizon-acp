"""
Script de teste para verificar se a API está retornando dados
no formato esperado pelo bot Discord
"""

import requests
import json
from typing import Dict, Any, Optional

# Configurações
BASE_URL = "http://localhost:6085"  # Ajuste conforme necessário
API_BASE = f"{BASE_URL}/api/v1"

# Credenciais serão solicitadas durante a execução
TEST_USERNAME = None
TEST_PASSWORD = None

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def test_endpoint(
    method: str,
    endpoint: str,
    expected_keys: Optional[list] = None,
    is_list: bool = False,
    requires_auth: bool = False,
    token: Optional[str] = None,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None
) -> tuple[bool, Any]:
    """
    Testa um endpoint da API
    
    Returns:
        (success: bool, data: Any)
    """
    url = f"{API_BASE}{endpoint}"
    headers = {}
    
    if requires_auth and token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.upper() == 'POST':
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        else:
            print_error(f"Método {method} não suportado")
            return False, None
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                # Verifica se não está em wrapper
                if isinstance(result, dict) and 'success' in result and 'data' in result:
                    print_warning(f"Endpoint {endpoint} ainda retorna wrapper (success/data)")
                    result = result.get('data', result)
                
                # Verifica se é lista quando esperado
                if is_list:
                    if not isinstance(result, list):
                        print_error(f"Endpoint {endpoint} deveria retornar lista, mas retornou: {type(result)}")
                        return False, result
                    print_success(f"Endpoint {endpoint} retorna lista com {len(result)} itens")
                else:
                    if not isinstance(result, dict):
                        print_error(f"Endpoint {endpoint} deveria retornar dict, mas retornou: {type(result)}")
                        return False, result
                    print_success(f"Endpoint {endpoint} retorna dict")
                
                # Verifica chaves esperadas
                if expected_keys and isinstance(result, dict):
                    missing = [key for key in expected_keys if key not in result]
                    if missing:
                        print_warning(f"Endpoint {endpoint} está faltando chaves: {missing}")
                    else:
                        print_success(f"Endpoint {endpoint} tem todas as chaves esperadas")
                
                # Mostra amostra dos dados
                if isinstance(result, list) and len(result) > 0:
                    print_info(f"Primeiro item: {json.dumps(result[0], indent=2, default=str)[:200]}...")
                elif isinstance(result, dict):
                    print_info(f"Dados: {json.dumps(result, indent=2, default=str)[:300]}...")
                
                return True, result
            except json.JSONDecodeError:
                print_error(f"Endpoint {endpoint} retornou resposta inválida (não é JSON)")
                print_error(f"Resposta: {response.text[:200]}")
                return False, None
        else:
            print_error(f"Endpoint {endpoint} retornou status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Erro: {error_data}")
            except:
                print_error(f"Resposta: {response.text[:200]}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao conectar em {endpoint}: {e}")
        return False, None


def test_authentication() -> Optional[str]:
    """Testa autenticação e retorna token"""
    print_section("TESTE DE AUTENTICAÇÃO")
    
    # Solicita credenciais se não foram fornecidas
    global TEST_USERNAME, TEST_PASSWORD
    
    if not TEST_USERNAME:
        print_info("Digite suas credenciais para testar autenticação:")
        TEST_USERNAME = input("Username: ").strip()
        if not TEST_USERNAME:
            print_warning("Username vazio. Pulando teste de autenticação.")
            return None
    
    if not TEST_PASSWORD:
        import getpass
        TEST_PASSWORD = getpass.getpass("Password: ").strip()
        if not TEST_PASSWORD:
            print_warning("Password vazio. Pulando teste de autenticação.")
            return None
    
    print_info(f"Tentando fazer login com usuário: {TEST_USERNAME}")
    
    success, result = test_endpoint(
        'POST',
        '/auth/login/',
        data={
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD
        }
    )
    
    if success and isinstance(result, dict) and 'access' in result:
        token = result['access']
        print_success(f"Token obtido com sucesso: {token[:50]}...")
        return token
    else:
        print_error("Falha ao obter token de autenticação")
        return None


def test_public_endpoints():
    """Testa endpoints públicos"""
    print_section("TESTE DE ENDPOINTS PÚBLICOS")
    
    # Players Online
    test_endpoint(
        'GET',
        '/server/players-online/',
        expected_keys=['online_count'],
        is_list=False
    )
    
    # Top PvP
    test_endpoint(
        'GET',
        '/server/top-pvp/',
        params={'limit': 5},
        is_list=True
    )
    
    # Top PK
    test_endpoint(
        'GET',
        '/server/top-pk/',
        params={'limit': 5},
        is_list=True
    )
    
    # Top Level
    test_endpoint(
        'GET',
        '/server/top-level/',
        params={'limit': 5},
        is_list=True
    )
    
    # Top Clan
    test_endpoint(
        'GET',
        '/server/top-clan/',
        params={'limit': 5},
        is_list=True
    )
    
    # Top Rich
    test_endpoint(
        'GET',
        '/server/top-rich/',
        params={'limit': 5},
        is_list=True
    )
    
    # Top Online
    test_endpoint(
        'GET',
        '/server/top-online/',
        params={'limit': 5},
        is_list=True
    )
    
    # Grand Boss Status
    test_endpoint(
        'GET',
        '/server/grandboss-status/',
        is_list=True
    )
    
    # Olympiad Ranking
    test_endpoint(
        'GET',
        '/server/olympiad-ranking/',
        is_list=True
    )
    
    # Olympiad Current Heroes
    test_endpoint(
        'GET',
        '/server/olympiad-current-heroes/',
        is_list=True
    )
    
    # Siege Status
    test_endpoint(
        'GET',
        '/server/siege/',
        is_list=True
    )
    
    # Search Character (testa com 'name' e 'q')
    print_info("Digite o nome do personagem para buscar:")
    character_name = input("Nome do personagem: ").strip()
    if character_name:
        print_info("Testando busca de personagem com parâmetro 'name'")
        test_endpoint(
            'GET',
            '/search/character/',
            params={'name': character_name},
            is_list=True
        )
        
        print_info("Testando busca de personagem com parâmetro 'q'")
        test_endpoint(
            'GET',
            '/search/character/',
            params={'q': character_name},
            is_list=True
        )
    else:
        print_warning("Nome do personagem vazio. Pulando teste de busca de personagem.")
    
    # Search Item (testa com 'name' e 'q')
    print_info("Digite o nome do item para buscar:")
    item_name = input("Nome do item: ").strip()
    if item_name:
        print_info("Testando busca de item com parâmetro 'name'")
        test_endpoint(
            'GET',
            '/search/item/',
            params={'name': item_name},
            is_list=True
        )
        
        print_info("Testando busca de item com parâmetro 'q'")
        test_endpoint(
            'GET',
            '/search/item/',
            params={'q': item_name},
            is_list=True
        )
    else:
        print_warning("Nome do item vazio. Pulando teste de busca de item.")
    
    # Clan Detail
    print_info("Digite o nome do clã para testar:")
    clan_name = input("Nome do clã: ").strip()
    if clan_name:
        test_endpoint(
            'GET',
            f'/clan/{clan_name}/',
            expected_keys=['clan_name', 'leader_name'],
            is_list=False
        )
    else:
        print_warning("Nome do clã vazio. Pulando teste de detalhes do clã.")
    
    # Auction Items
    test_endpoint(
        'GET',
        '/auction/items/',
        params={'limit': 5},
        is_list=True
    )


def test_authenticated_endpoints(token: str):
    """Testa endpoints autenticados"""
    print_section("TESTE DE ENDPOINTS AUTENTICADOS")
    
    # User Profile
    print_info("Testando /user/profile/")
    success, profile = test_endpoint(
        'GET',
        '/user/profile/',
        expected_keys=['username', 'email'],
        requires_auth=True,
        token=token
    )
    
    if success:
        print_success("Perfil retornado corretamente!")
        if isinstance(profile, dict):
            print_info(f"Username: {profile.get('username')}")
            print_info(f"Email: {profile.get('email')}")
            print_info(f"Date Joined: {profile.get('date_joined')}")
            print_info(f"Last Login: {profile.get('last_login')}")
    
    # User Dashboard
    print_info("Testando /user/dashboard/")
    success, dashboard = test_endpoint(
        'GET',
        '/user/dashboard/',
        expected_keys=['username', 'email'],
        requires_auth=True,
        token=token
    )
    
    if success:
        print_success("Dashboard retornado corretamente!")
        if isinstance(dashboard, dict):
            print_info(f"Username: {dashboard.get('username')}")
            print_info(f"Server Online: {dashboard.get('server_online')}")
            print_info(f"Players Online: {dashboard.get('players_online')}")
    
    # User Stats
    print_info("Testando /user/stats/")
    success, stats = test_endpoint(
        'GET',
        '/user/stats/',
        requires_auth=True,
        token=token
    )
    
    if success:
        print_success("Stats retornado corretamente!")
        if isinstance(stats, dict):
            print_info(f"Stats keys: {list(stats.keys())}")


def main():
    """Função principal"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("TESTE DE API PARA BOT DISCORD")
    print("="*60)
    print(f"{Colors.RESET}\n")
    
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"API Base: {API_BASE}")
    if TEST_USERNAME:
        print_info(f"Test User: {TEST_USERNAME}")
    else:
        print_info("Test User: (será solicitado durante o teste)")
    print()
    
    # Testa conexão básica
    try:
        response = requests.get(f"{API_BASE}/health/", timeout=5)
        if response.status_code == 200:
            print_success("API está acessível")
        else:
            print_warning(f"API retornou status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print_error(f"Não foi possível conectar à API: {e}")
        print_error("Verifique se o servidor está rodando e a URL está correta")
        return
    
    # Testa endpoints públicos
    test_public_endpoints()
    
    # Testa autenticação
    token = test_authentication()
    
    # Testa endpoints autenticados
    if token:
        test_authenticated_endpoints(token)
    else:
        print_warning("Pulando testes de endpoints autenticados (token não obtido)")
    
    print_section("TESTE CONCLUÍDO")
    print_info("Revise os resultados acima para verificar se tudo está funcionando corretamente")
    print()


if __name__ == '__main__':
    main()

