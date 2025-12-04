"""Template da classe LineageInflation - Análise de Inflação"""

def get_lineage_inflation_template(char_id: str, access_level: str) -> str:
    """Gera o código da classe LineageInflation"""
    
    return f'''class LineageInflation:
    """Classe para análise de inflação de itens no servidor."""

    @staticmethod
    def _run_query(sql, params=None, use_cache=False):
        return LineageDB().select(sql, params=params, use_cache=use_cache)

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_all_items_by_location():
        """Busca todos os itens de todos os personagens, agrupados por localização."""
        sql = """
            SELECT 
                i.item_id AS item_id,
                i.count AS quantity,
                i.loc AS location,
                i.owner_id,
                c.char_name,
                c.account_name,
                CONCAT('Item ', i.item_id) AS item_name,
                NULL AS item_category,
                NULL AS crystal_type,
                i.enchant_level AS enchant
            FROM items i
            INNER JOIN characters c ON c.{char_id} = i.owner_id
            WHERE c.{access_level} = '0'
            AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
            ORDER BY i.loc, i.item_id, c.char_name
        """
        return LineageInflation._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_items_summary_by_category():
        """Resumo de itens agrupados por categoria e localização."""
        sql = """
            SELECT 
                i.item_id AS item_id,
                CONCAT('Item ', i.item_id) AS item_name,
                NULL AS item_category,
                NULL AS crystal_type,
                i.loc AS location,
                COUNT(*) AS total_instances,
                SUM(i.count) AS total_quantity,
                COUNT(DISTINCT i.owner_id) AS unique_owners,
                MIN(i.enchant_level) AS min_enchant,
                MAX(i.enchant_level) AS max_enchant,
                AVG(i.enchant_level) AS avg_enchant
            FROM items i
            INNER JOIN characters c ON c.{char_id} = i.owner_id
            WHERE c.{access_level} = '0'
            AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
            GROUP BY i.item_id, i.loc
            ORDER BY total_quantity DESC, item_id ASC
        """
        return LineageInflation._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_items_by_character(char_id=None):
        """Busca todos os itens de um personagem específico ou de todos."""
        if char_id:
            sql = """
                SELECT 
                    i.item_id AS item_id,
                    i.count AS quantity,
                    i.loc AS location,
                    i.owner_id,
                    c.char_name,
                    c.account_name,
                    CONCAT('Item ', i.item_id) AS item_name,
                    i.enchant_level AS enchant
                FROM items i
                INNER JOIN characters c ON c.{char_id} = i.owner_id
                WHERE i.owner_id = :char_id
                AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
                ORDER BY i.loc, i.item_id
            """
            return LineageInflation._run_query(sql, {{"char_id": char_id}})
        else:
            return LineageInflation.get_all_items_by_location()

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_top_items_by_quantity(limit=100):
        """Retorna os itens mais comuns no servidor."""
        sql = """
            SELECT 
                i.item_id AS item_id,
                CONCAT('Item ', i.item_id) AS item_name,
                SUM(i.count) AS total_quantity,
                COUNT(DISTINCT i.owner_id) AS unique_owners,
                COUNT(*) AS total_instances
            FROM items i
            INNER JOIN characters c ON c.{char_id} = i.owner_id
            WHERE c.{access_level} = '0'
            AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
            GROUP BY i.item_id
            ORDER BY total_quantity DESC
            LIMIT :limit
        """
        return LineageInflation._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_items_by_location_summary():
        """Resumo de itens por localização."""
        sql = """
            SELECT 
                i.loc AS location,
                COUNT(DISTINCT i.item_id) AS unique_item_types,
                COUNT(*) AS total_instances,
                SUM(i.count) AS total_quantity,
                COUNT(DISTINCT i.owner_id) AS unique_owners
            FROM items i
            INNER JOIN characters c ON c.{char_id} = i.owner_id
            WHERE c.{access_level} = '0'
            AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
            GROUP BY i.loc
            ORDER BY i.loc
        """
        return LineageInflation._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_site_items_count():
        """Conta itens armazenados no site."""
        return []

    @staticmethod
    @cache_lineage_result(timeout=60, use_cache=False)
    def get_inflation_comparison(date_from=None, date_to=None):
        """Compara a quantidade de itens entre duas datas."""
        return {{
            "date_from": date_from,
            "date_to": date_to,
            "items": []
        }}
'''

