URL_RATE_LIMITS_DICT = {
    # APIs DRF (versão atual)
    '/api/v1/server/players-online/':                 {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-pvp/':                        {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-pk/':                         {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-clan/':                       {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-rich/':                       {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-online/':                     {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/top-level/':                      {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/olympiad-ranking/':               {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/olympiad-heroes/':                {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/olympiad-current-heroes/':        {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/grandboss-status/':               {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/siege/':                          {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/siege-participants/':             {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    '/api/v1/server/boss-jewel-locations/':           {'rate': '120/m', 'key': 'ip', 'group': 'public-api'},
    
    # APIs de administração
    '/api/v1/admin/config/':                          {'rate': '60/m', 'key': 'user', 'group': 'admin-api'},
    
    # APIs de autenticação
    '/api/v1/auth/login/':                            {'rate': '20/m', 'key': 'ip', 'group': 'auth-api'},
    '/api/v1/auth/refresh/':                          {'rate': '60/m', 'key': 'user', 'group': 'auth-api'},
    '/api/v1/auth/logout/':                           {'rate': '60/m', 'key': 'user', 'group': 'auth-api'},
    
    # APIs de usuário
    '/api/v1/user/profile/':                          {'rate': '100/m', 'key': 'user', 'group': 'user-api'},
    '/api/v1/user/change-password/':                  {'rate': '20/m', 'key': 'user', 'group': 'user-api'},
    '/api/v1/user/dashboard/':                        {'rate': '100/m', 'key': 'user', 'group': 'user-api'},
    '/api/v1/user/stats/':                            {'rate': '100/m', 'key': 'user', 'group': 'user-api'},
    
    # APIs de busca
    '/api/v1/search/character/':                      {'rate': '120/m', 'key': 'ip', 'group': 'search-api'},
    '/api/v1/search/item/':                           {'rate': '120/m', 'key': 'ip', 'group': 'search-api'},
    
    # APIs de dados do jogo
    '/api/v1/clan/':                                  {'rate': '120/m', 'key': 'ip', 'group': 'game-api'},
    '/api/v1/auction/items/':                         {'rate': '120/m', 'key': 'ip', 'group': 'game-api'},
    
    # APIs de monitoramento
    '/api/v1/health/':                                {'rate': '300/m', 'key': 'ip', 'group': 'monitoring-api'},
    '/api/v1/metrics/':                               {'rate': '60/m', 'key': 'user', 'group': 'monitoring-api'},
    '/api/v1/cache/stats/':                           {'rate': '60/m', 'key': 'user', 'group': 'monitoring-api'},

    # =========================== WALLET / TRANSFERÊNCIAS ===========================
    # Proteção contra spam e cliques múltiplos em transferências
    '/app/wallet/transfer/server/':      {'rate': '1/m', 'key': 'user', 'group': 'wallet-transfers', 'method': 'POST'},
    '/app/wallet/transfer/from-server/': {'rate': '1/m', 'key': 'user', 'group': 'wallet-transfers', 'method': 'POST'},
    '/app/wallet/transfer/player/':      {'rate': '1/m', 'key': 'user', 'group': 'wallet-transfers', 'method': 'POST'},
    
    # API interna para transferências (mesmo limite rigoroso)
    '/app/wallet/api/internal/transfer/server/': {'rate': '1/m', 'key': 'user', 'group': 'wallet-transfers', 'method': 'POST'},
        
    # =========================== AUTENTICAÇÃO WEB ===========================
    # Rotas críticas de autenticação - limites aumentados mas ainda seguros
    '/accounts/login/':                {'rate': '30/m', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/register/':            {'rate': '10/m', 'key': 'ip', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/password-reset/':       {'rate': '20/h', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/password-change/':     {'rate': '20/m', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/password-reset-confirm/': {'rate': '20/h', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    '/verify/':                       {'rate': '30/h', 'key': 'user', 'group': 'auth-web'},
    '/resend-verify/':                {'rate': '20/h', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    '/accounts/2fa/':                 {'rate': '30/m', 'key': 'user', 'group': 'auth-web', 'method': 'POST'},
    
    # =========================== PAGAMENTOS ===========================
    # Rotas críticas de pagamento - limites aumentados moderadamente
    '/app/payment/new/':              {'rate': '30/m', 'key': 'user', 'group': 'payment', 'method': 'POST'},
    '/app/payment/order/':            {'rate': '60/m', 'key': 'user', 'group': 'payment'},
    '/app/payment/calcular-bonus/':   {'rate': '120/m', 'key': 'ip', 'group': 'payment'},
    '/app/payment/status-pagamento/': {'rate': '120/m', 'key': 'user', 'group': 'payment'},
    '/app/payment/cancel-order/':     {'rate': '20/m', 'key': 'user', 'group': 'payment', 'method': 'POST'},
    
    # =========================== WEBHOOKS DE PAGAMENTO ===========================
    # Rate limiting rigoroso para webhooks (proteção contra ataques)
    '/app/payment/stripe/webhook/':   {'rate': '100/h', 'key': 'ip', 'group': 'webhook-stripe', 'method': 'POST'},
    '/app/payment/mercadopago/notificacao/': {'rate': '100/h', 'key': 'ip', 'group': 'webhook-mercadopago', 'method': 'POST'},
    
    # =========================== UPLOAD DE ARQUIVOS ===========================
    # Proteção contra spam de uploads - limites aumentados
    '/app/media/upload/':             {'rate': '30/m', 'key': 'user', 'group': 'file-upload', 'method': 'POST'},
    '/app/media/ajax/upload/':        {'rate': '60/m', 'key': 'user', 'group': 'file-upload', 'method': 'POST'},
    '/app/media/bulk-upload/':        {'rate': '20/m', 'key': 'user', 'group': 'file-upload', 'method': 'POST'},
    
    # =========================== REDE SOCIAL ===========================
    # Proteção contra spam de posts e comentários - limites aumentados
    '/social/post/create/':           {'rate': '30/m', 'key': 'user', 'group': 'social-create', 'method': 'POST'},
    '/social/post/':                  {'rate': '120/m', 'key': 'user', 'group': 'social-interact'},
    '/social/comment/':               {'rate': '60/m', 'key': 'user', 'group': 'social-interact', 'method': 'POST'},
    '/social/report/':                {'rate': '20/h', 'key': 'user', 'group': 'social-report', 'method': 'POST'},
    
    # =========================== JOGOS ===========================
    # Rate limiting flexível para não gerar desconforto aos jogadores
    # Roulette
    '/app/game/roulette/spin-ajax/':  {'rate': '120/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Box
    '/app/game/box/open-ajax/':       {'rate': '100/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/box/buy/':             {'rate': '30/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/box/buy-and-open/':    {'rate': '30/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/box/reset/':           {'rate': '20/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Economy Game
    '/app/game/economy-game/fight/':  {'rate': '200/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/economy-game/enchant/': {'rate': '100/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Slot Machine
    '/app/game/slot-machine/spin/':   {'rate': '120/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Dice Game
    '/app/game/dice-game/play/':      {'rate': '120/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Fishing Game
    '/app/game/fishing/cast/':        {'rate': '120/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/fishing/buy-bait/':    {'rate': '30/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Daily Bonus
    '/app/game/daily-bonus/claim/':   {'rate': '10/h', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Battle Pass
    '/app/game/battle-pass/claim/':   {'rate': '60/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/battle-pass/buy-premium/': {'rate': '10/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/battle-pass/exchange/': {'rate': '30/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Bag
    '/app/game/bag/transfer/':        {'rate': '60/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    '/app/game/bag/empty/':           {'rate': '10/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # Tokens
    '/app/game/buy-tokens/':          {'rate': '30/m', 'key': 'user', 'group': 'games', 'method': 'POST'},
    
    # =========================== LEILÕES ===========================
    '/auction/create/':               {'rate': '30/m', 'key': 'user', 'group': 'auction', 'method': 'POST'},
    '/auction/bid/':                  {'rate': '120/m', 'key': 'user', 'group': 'auction', 'method': 'POST'},
}
