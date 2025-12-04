"""
Templates das classes para geração de arquivos query
Cada arquivo contém o template de uma classe específica

Estrutura:
- Cada classe em seu próprio arquivo
- Funções recebem parâmetros do schema (char_id, access_level, etc)
- Retornam string com código Python formatado
"""

from .lineage_stats import get_lineage_stats_template
from .lineage_services import get_lineage_services_template
from .lineage_account import get_lineage_account_template
from .transfer_wallet_to_char import get_transfer_wallet_to_char_template
from .transfer_char_to_wallet import get_transfer_char_to_wallet_template
from .lineage_marketplace import get_lineage_marketplace_template
from .lineage_inflation import get_lineage_inflation_template

__all__ = [
    'get_lineage_stats_template',
    'get_lineage_services_template',
    'get_lineage_account_template',
    'get_transfer_wallet_to_char_template',
    'get_transfer_char_to_wallet_template',
    'get_lineage_marketplace_template',
    'get_lineage_inflation_template',
]


