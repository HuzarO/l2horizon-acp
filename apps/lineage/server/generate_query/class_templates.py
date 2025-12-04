"""
Templates das classes que serão copiadas para o arquivo query gerado
Estas são as 5 classes que faltam no gerador
"""

def get_lineage_services_template(char_id: str) -> str:
    """Retorna o template da classe LineageServices"""
    return f'''
class LineageServices:

    @staticmethod
    @cache_lineage_result(timeout=300)
    def find_chars(login):
        sql = """
            SELECT
                C.*, 
                C.classid AS base_class,
                C.level AS base_level,
                CS.name AS clan_name,
                CLAN.ally_name
            FROM characters AS C
            LEFT JOIN clan_data AS CLAN ON CLAN.clan_id = C.clanid
            LEFT JOIN clan_subpledges AS CS ON CS.clan_id = CLAN.clan_id AND CS.sub_pledge_id = 0
            WHERE C.account_name = :login
            LIMIT 7;
        """
        try:
            return LineageDB().select(sql, {{"login": login}})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def check_char(acc, cid):
        sql = "SELECT * FROM characters WHERE {char_id} = :cid AND account_name = :acc LIMIT 1"
        try:
            return LineageDB().select(sql, {{"acc": acc, "cid": cid}})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def check_name_exists(name):
        sql = "SELECT * FROM characters WHERE char_name = :name LIMIT 1"
        try:
            return LineageDB().select(sql, {{"name": name}})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def change_nickname(acc, cid, name):
        try:
            sql = """
                UPDATE characters
                SET char_name = :name
                WHERE {char_id} = :cid AND account_name = :acc
                LIMIT 1
            """
            return LineageDB().update(sql, {{"name": name, "cid": cid, "acc": acc}})
        except Exception as e:
            print(f"Erro ao trocar nickname: {{e}}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def change_sex(acc, cid, sex):
        try:
            sql = """
                UPDATE characters SET sex = :sex
                WHERE {char_id} = :cid AND account_name = :acc
                LIMIT 1
            """
            return LineageDB().update(sql, {{"sex": sex, "cid": cid, "acc": acc}})
        except Exception as e:
            print(f"Erro ao trocar sexo: {{e}}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def unstuck(acc, cid, x, y, z):
        try:
            sql = """
                UPDATE characters SET x = :x, y = :y, z = :z
                WHERE {char_id} = :cid AND account_name = :acc
                LIMIT 1
            """
            return LineageDB().update(sql, {{"x": x, "y": y, "z": z, "cid": cid, "acc": acc}})
        except Exception as e:
            print(f"Erro ao desbugar personagem: {{e}}")
            return None


'''

def get_transfer_wallet_to_char_template(char_id: str) -> str:
    """Retorna o template da classe TransferFromWalletToChar"""
    return f'''
class TransferFromWalletToChar:
    items_delayed = False

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def find_char(account: str, char_name: str):
        query = """
            SELECT * FROM characters 
            WHERE account_name = :account AND char_name = :char_name 
            LIMIT 1
        """
        try:
            return LineageDB().select(query, {{"account": account, "char_name": char_name}})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def search_coin(char_name: str, coin_id: int):
        query = """
            SELECT i.* FROM items i
            JOIN characters c ON i.owner_id = c.{char_id}
            WHERE c.char_name = :char_name AND i.item_id = :coin_id
        """
        return LineageDB().select(query, {{"char_name": char_name, "coin_id": coin_id}})

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def insert_coin(char_name: str, coin_id: int, amount: int, enchant: int = 0):
        db = LineageDB()

        char_query = "SELECT {char_id} FROM characters WHERE char_name = :char_name"
        char_result = db.select(char_query, {{"char_name": char_name}})
        if not char_result:
            return None

        owner_id = char_result[0]["{char_id}"]
        
        insert_query = """
            INSERT INTO items (
                owner_id, object_id, item_id, count,
                enchant_level, loc, loc_data
            ) VALUES (
                :owner_id, :object_id, :coin_id, :amount,
                :enchant, 'INVENTORY', 0
            )
        """
        result = db.insert(insert_query, {{
            "owner_id": owner_id,
            "object_id": owner_id,
            "coin_id": coin_id,
            "amount": amount,
            "enchant": enchant
        }})

        return result is not None


'''

def get_transfer_char_to_wallet_template(char_id: str) -> str:
    """Retorna o template da classe TransferFromCharToWallet"""
    return f'''
class TransferFromCharToWallet:

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def find_char(account, char_id):
        query = """
            SELECT online, char_name FROM characters 
            WHERE account_name = :account AND {char_id} = :char_id
        """
        params = {{"account": account, "char_id": char_id}}
        return LineageDB().select(query, params)

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def list_items(char_id):
        query = """
            SELECT object_id AS item_id, item_id AS item_type, count AS amount, loc AS location, enchant_level AS enchant
            FROM items
            WHERE owner_id = :char_id
            AND loc IN ('INVENTORY', 'WAREHOUSE')
            ORDER BY loc, item_id
        """
        params = {{"char_id": char_id}}
        results = LineageDB().select(query, params)
        return results

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def check_ingame_coin(coin_id, char_id):
        db = LineageDB()
        query = """
            SELECT count AS amount, enchant_level AS enchant FROM items 
            WHERE owner_id = :char_id AND item_id = :coin_id AND loc = 'INVENTORY'
            LIMIT 1
        """
        result = db.select(query, {{"char_id": char_id, "coin_id": coin_id}})
        amount = result[0]["amount"] if result else 0
        enchant = result[0]["enchant"] if result else 0
        return {{"total": amount, "inventory": amount, "warehouse": 0, "enchant": enchant}}

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def remove_ingame_coin(coin_id, count, char_id):
        try:
            db = LineageDB()
            query = """
                SELECT * FROM items
                WHERE owner_id = :char_id AND item_id = :item_id AND loc = 'INVENTORY'
            """
            items = db.select(query, {{"char_id": char_id, "item_id": coin_id}})
            
            if not items or sum(item["count"] for item in items) < count:
                return False
                
            for item in items:
                if item["count"] <= count:
                    db.update("DELETE FROM items WHERE object_id = :item_id", {{"item_id": item["object_id"]}})
                    count -= item["count"]
                else:
                    db.update(
                        "UPDATE items SET count = count - :count WHERE object_id = :item_id",
                        {{"count": count, "item_id": item["object_id"]}}
                    )
                    count = 0
                    
                if count == 0:
                    break
                    
            return True
        except Exception as e:
            print(f"Erro ao remover coin: {{e}}")
            return False


'''

def get_lineage_marketplace_template(char_id: str) -> str:
    """Retorna o template da classe LineageMarketplace"""
    return f'''
class LineageMarketplace:
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def get_user_characters(account_name):
        """Busca todos os characters de uma conta do banco L2."""
        sql = """
            SELECT 
                c.{char_id} as char_id,
                c.char_name,
                c.level,
                c.classid,
                c.pvpkills as pvp_kills,
                c.pkkills as pk_count,
                c.clanid,
                COALESCE(cs.name, '') as clan_name,
                c.accesslevel,
                c.online,
                c.lastAccess,
                c.account_name
            FROM characters c
            LEFT JOIN clan_data cd ON c.clanid = cd.clan_id
            LEFT JOIN clan_subpledges cs ON cs.clan_id = cd.clan_id AND cs.sub_pledge_id = 0
            WHERE c.account_name = :account_name
            ORDER BY c.level DESC, c.char_name ASC
        """
        return LineageDB().select(sql, {{"account_name": account_name}})
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def verify_character_ownership(char_id, account_name):
        """Verifica se um character pertence a uma conta específica."""
        sql = """
            SELECT COUNT(*) as total
            FROM characters 
            WHERE {char_id} = :char_id AND account_name = :account_name
        """
        result = LineageDB().select(sql, {{"char_id": char_id, "account_name": account_name}})
        return result[0]['total'] > 0 if result and len(result) > 0 else False
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def get_character_details(char_id):
        """Busca detalhes completos de um character do banco L2."""
        sql = """
            SELECT 
                c.{char_id} as char_id,
                c.char_name,
                c.level,
                c.classid,
                c.pvpkills as pvp_kills,
                c.pkkills as pk_count,
                c.clanid,
                COALESCE(cs.name, '') as clan_name,
                c.accesslevel,
                c.online,
                c.lastAccess,
                c.account_name
            FROM characters c
            LEFT JOIN clan_data cd ON c.clanid = cd.clan_id
            LEFT JOIN clan_subpledges cs ON cs.clan_id = cd.clan_id AND cs.sub_pledge_id = 0
            WHERE c.{char_id} = :char_id
        """
        result = LineageDB().select(sql, {{"char_id": char_id}})
        return result[0] if result and len(result) > 0 else None
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def transfer_character_to_account(char_id, new_account):
        """Transfere um character para nova conta no banco L2."""
        sql = "UPDATE characters SET account_name = :new_account WHERE {char_id} = :char_id"
        result = LineageDB().update(sql, {{"new_account": new_account, "char_id": char_id}})
        return result is not None and result > 0


'''

def get_lineage_inflation_template(char_id: str, access_level: str) -> str:
    """Retorna o template da classe LineageInflation"""
    return f'''
class LineageInflation:
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
'''

