URL_RATE_LIMITS_DICT = {
    # APIs DRF (versão atual)
    '/api/v1/server/players-online/':                 {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-pvp/':                        {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-pk/':                         {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-clan/':                       {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-rich/':                       {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-online/':                     {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-level/':                      {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/olympiad-ranking/':               {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/olympiad-heroes/':                {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/olympiad-current-heroes/':        {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/grandboss-status/':               {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/siege/':                          {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/siege-participants/':             {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/boss-jewel-locations/':           {'rate': '30/m', 'key': 'ip', 'group': 'public-api'},
    
    # APIs de administração
    '/api/v1/admin/config/':                          {'rate': '10/m', 'key': 'user', 'group': 'admin-api'},
    
    # APIs de autenticação
    '/api/v1/auth/login/':                            {'rate': '5/m', 'key': 'ip', 'group': 'auth-api'},
    '/api/v1/auth/refresh/':                          {'rate': '10/m', 'key': 'user', 'group': 'auth-api'},
    '/api/v1/auth/logout/':                           {'rate': '10/m', 'key': 'user', 'group': 'auth-api'},
    
    # APIs de usuário
    '/api/v1/user/profile/':                          {'rate': '20/m', 'key': 'user', 'group': 'user-api'},
    '/api/v1/user/change-password/':                  {'rate': '5/m', 'key': 'user', 'group': 'user-api'},
    '/api/v1/user/dashboard/':                        {'rate': '20/m', 'key': 'user', 'group': 'user-api'},
    '/api/v1/user/stats/':                            {'rate': '20/m', 'key': 'user', 'group': 'user-api'},
    
    # APIs de busca
    '/api/v1/search/character/':                      {'rate': '30/m', 'key': 'ip', 'group': 'search-api'},
    '/api/v1/search/item/':                           {'rate': '30/m', 'key': 'ip', 'group': 'search-api'},
    
    # APIs de dados do jogo
    '/api/v1/clan/':                                  {'rate': '30/m', 'key': 'ip', 'group': 'game-api'},
    '/api/v1/auction/items/':                         {'rate': '30/m', 'key': 'ip', 'group': 'game-api'},
    
    # APIs de monitoramento
    '/api/v1/health/':                                {'rate': '60/m', 'key': 'ip', 'group': 'monitoring-api'},
    '/api/v1/metrics/':                               {'rate': '10/m', 'key': 'user', 'group': 'monitoring-api'},
    '/api/v1/cache/stats/':                           {'rate': '10/m', 'key': 'user', 'group': 'monitoring-api'},

    # Outras APIs
    '/app/wallet/transfer/servidor/': {'rate': '5/m', 'key': 'user_or_ip', 'group': 'wallet-transfers'},
    '/app/wallet/transfer/jogador/':  {'rate': '5/m', 'key': 'user_or_ip', 'group': 'wallet-transfers'},
        
    # =========================== AUTENTICAÇÃO WEB ===========================
    # Rotas críticas de autenticação que precisam de rate limiting rigoroso
    '/accounts/login/':                {'rate': '5/m', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/register/':            {'rate': '3/h', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/password-reset/':       {'rate': '5/h', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/password-change/':     {'rate': '5/m', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/password-reset-confirm/': {'rate': '5/h', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    '/verify/':                       {'rate': '10/h', 'key': 'ip', 'group': 'auth-web'},
    '/resend-verify/':                {'rate': '5/h', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/2fa/':                 {'rate': '10/m', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    
    # =========================== PAGAMENTOS ===========================
    # Rotas críticas de pagamento que precisam de proteção
    '/app/payment/new/':              {'rate': '10/m', 'key': 'user', 'group': 'payment', 'method': 'POST'},
    '/app/payment/order/':            {'rate': '20/m', 'key': 'user', 'group': 'payment'},
    '/app/payment/calcular-bonus/':   {'rate': '30/m', 'key': 'ip', 'group': 'payment'},
    '/app/payment/status-pagamento/': {'rate': '30/m', 'key': 'user', 'group': 'payment'},
    '/app/payment/cancel-order/':     {'rate': '5/m', 'key': 'user', 'group': 'payment', 'method': 'POST'},
    
    # =========================== UPLOAD DE ARQUIVOS ===========================
    # Proteção contra spam de uploads
    '/app/media/upload/':             {'rate': '10/m', 'key': 'user', 'group': 'file-upload', 'method': 'POST'},
    '/app/media/ajax/upload/':        {'rate': '20/m', 'key': 'user', 'group': 'file-upload', 'method': 'POST'},
    '/app/media/bulk-upload/':        {'rate': '5/m', 'key': 'user', 'group': 'file-upload', 'method': 'POST'},
    
    # =========================== REDE SOCIAL ===========================
    # Proteção contra spam de posts e comentários
    '/social/post/create/':           {'rate': '10/m', 'key': 'user', 'group': 'social-create', 'method': 'POST'},
    '/social/post/':                  {'rate': '30/m', 'key': 'user', 'group': 'social-interact'},
    '/social/comment/':               {'rate': '20/m', 'key': 'user', 'group': 'social-interact', 'method': 'POST'},
    '/social/report/':                {'rate': '10/h', 'key': 'user', 'group': 'social-report', 'method': 'POST'},
    
    # =========================== JOGOS ===========================
    # Proteção contra abuso em jogos
    '/game/roulette/spin/':           {'rate': '30/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/game/box/open/':                {'rate': '20/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/game/monster/fight/':           {'rate': '60/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # =========================== LEILÕES ===========================
    '/auction/create/':               {'rate': '10/m', 'key': 'user', 'group': 'auction', 'method': 'POST'},
    '/auction/bid/':                  {'rate': '30/m', 'key': 'user', 'group': 'auction', 'method': 'POST'},
}
