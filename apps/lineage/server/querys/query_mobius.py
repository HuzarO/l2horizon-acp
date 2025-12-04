"""
Query File: query_mobius.py
Generated automatically by Query Generator
Date: 2025-12-04 12:47:36
Database Type: mobius
"""

from apps.lineage.server.database import LineageDB
from apps.lineage.server.utils.cache import cache_lineage_result

import time
import base64
import hashlib


class LineageStats:

    @staticmethod
    def _run_query(sql, params=None, use_cache=True):
        return LineageDB().select(sql, params=params, use_cache=use_cache)
    
    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_crests(ids, type='clan'):
        if not ids:
            return []

        table = 'clan_data'
        id_column = 'clan_id'
        crest_column = 'crest_id'

        sql = f"""
            SELECT {id_column}, {crest_column}
            FROM {table}
            WHERE {id_column} IN :ids
        """
        return LineageStats._run_query(sql, {"ids": tuple(ids)})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def players_online():
        sql = "SELECT COUNT(*) AS quant FROM characters WHERE online > 0 AND accesslevel = '0'"
        return LineageStats._run_query(sql)
    
    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_pvp(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime,
                CS.level,
                C.classid AS base,
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id
            FROM characters C
            LEFT JOIN character_subclasses CS ON CS.charId = C.charId AND CS.class_index = 0
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE C.accesslevel = '0'
            ORDER BY pvpkills DESC, pkkills DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {"limit": limit})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_pk(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime,
                CS.level,
                C.classid AS base,
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id
            FROM characters C
            LEFT JOIN character_subclasses CS ON CS.charId = C.charId AND CS.class_index = 0
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE C.accesslevel = '0'
            ORDER BY pkkills DESC, pvpkills DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {"limit": limit})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_online(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime,
                CS.level,
                C.classid AS base,
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id
            FROM characters C
            LEFT JOIN character_subclasses CS ON CS.charId = C.charId AND CS.class_index = 0
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE C.accesslevel = '0'
            ORDER BY onlinetime DESC, pvpkills DESC, pkkills DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {"limit": limit})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_level(limit=10):
        sql = """
            SELECT 
                C.char_name, 
                C.pvpkills, 
                C.pkkills, 
                C.online, 
                C.onlinetime, 
                CS.level,
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id
            FROM characters C
            LEFT JOIN character_subclasses CS ON CS.charId = C.charId AND CS.class_index = 0
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE C.accesslevel = '0'
            ORDER BY CS.level DESC, C.onlinetime DESC, C.char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {"limit": limit})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_adena(limit=10, adn_billion_item=0, value_item=1000000):
        item_bonus_sql = ""
        if adn_billion_item != 0:
            item_bonus_sql = f"""
                IFNULL((SELECT SUM(I2.count) * :value_item
                        FROM items I2
                        WHERE I2.owner_id = C.charId AND I2.item_id = :adn_billion_item
                        GROUP BY I2.owner_id), 0) +
            """
        sql = f"""
            SELECT 
                C.char_name, 
                C.online, 
                C.onlinetime, 
                CS.level, 
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id,
                (
                    {item_bonus_sql}
                    IFNULL((SELECT SUM(I1.count)
                            FROM items I1
                            WHERE I1.owner_id = C.charId AND I1.item_id = '57'
                            GROUP BY I1.owner_id), 0)
                ) AS adenas
            FROM characters C
            LEFT JOIN character_subclasses CS ON CS.charId = C.charId AND CS.class_index = 0
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE C.accesslevel = '0'
            ORDER BY adenas DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {
            "limit": limit,
            "adn_billion_item": adn_billion_item,
            "value_item": value_item
        })

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_clans(limit=10):
        sql = """
            SELECT 
                C.clan_id, 
                C.clan_name, 
                C.clan_level, 
                C.reputation_score, 
                C.ally_name,
                C.ally_id,
                P.char_name, 
                (SELECT COUNT(*) FROM characters WHERE clanid = C.clan_id) AS membros
            FROM clan_data C
            LEFT JOIN characters P ON P.charId = C.leader_id
            ORDER BY C.clan_level DESC, C.reputation_score DESC, membros DESC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {"limit": limit})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_ranking():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id,
                C.classid AS base, 
                O.olympiad_points
            FROM olympiad_nobles O
            LEFT JOIN characters C ON C.charId = O.char_id
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            ORDER BY olympiad_points DESC, base ASC, char_name ASC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_all_heroes():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                D.clan_name, 
                C.clanid AS clan_id,
                D.ally_id AS ally_id,
                C.classid AS base, 
                H.count
            FROM heroes H
            LEFT JOIN characters C ON C.charId = H.char_id
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE H.played > 0 AND H.count > 0
            ORDER BY H.count DESC, base ASC, char_name ASC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_current_heroes():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                D.clan_name,
                C.clanid AS clan_id,
                D.ally_id AS ally_id,
                C.classid AS base
            FROM heroes H
            LEFT JOIN characters C ON C.charId = H.char_id
            LEFT JOIN clan_data D ON D.clan_id = C.clanid
            WHERE H.played > 0 AND H.count > 0
            ORDER BY base ASC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def grandboss_status():
        sql = """
            SELECT boss_id, respawn_time AS respawn
            FROM grandboss_data
            ORDER BY respawn_time DESC
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def siege():
        sql = """
            SELECT 
                W.id, 
                W.name, 
                W.siegeDate AS sdate, 
                W.treasury AS stax,
                P.char_name, 
                C.clan_name,
                C.clan_id,
                C.ally_id,
                C.ally_name
            FROM castle W
            LEFT JOIN clan_data C ON C.hasCastle = W.id
            LEFT JOIN characters P ON P.charId = C.leader_id
        """
        return LineageStats._run_query(sql)



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
            return LineageDB().select(sql, {"login": login})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def check_char(acc, cid):
        sql = "SELECT * FROM characters WHERE charId = :cid AND account_name = :acc LIMIT 1"
        try:
            return LineageDB().select(sql, {"acc": acc, "cid": cid})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def check_name_exists(name):
        sql = "SELECT * FROM characters WHERE char_name = :name LIMIT 1"
        try:
            return LineageDB().select(sql, {"name": name})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def change_nickname(acc, cid, name):
        try:
            sql = """
                UPDATE characters
                SET char_name = :name
                WHERE charId = :cid AND account_name = :acc
                LIMIT 1
            """
            return LineageDB().update(sql, {"name": name, "cid": cid, "acc": acc})
        except Exception as e:
            print(f"Erro ao trocar nickname: {e}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def change_sex(acc, cid, sex):
        try:
            sql = """
                UPDATE characters SET sex = :sex
                WHERE charId = :cid AND account_name = :acc
                LIMIT 1
            """
            return LineageDB().update(sql, {"sex": sex, "cid": cid, "acc": acc})
        except Exception as e:
            print(f"Erro ao trocar sexo: {e}")
            return None

    @staticmethod
    @cache_lineage_result(timeout=300)
    def unstuck(acc, cid, x, y, z):
        try:
            sql = """
                UPDATE characters SET x = :x, y = :y, z = :z
                WHERE charId = :cid AND account_name = :acc
                LIMIT 1
            """
            return LineageDB().update(sql, {"x": x, "y": y, "z": z, "cid": cid, "acc": acc})
        except Exception as e:
            print(f"Erro ao desbugar personagem: {e}")
            return None



class LineageAccount:
    _checked_columns = False

    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_acess_level():
        return 'accessLevel'

    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_account_by_login(login):
        sql = """
            SELECT *
            FROM accounts
            WHERE login = :login
            LIMIT 1
        """
        try:
            result = LineageDB().select(sql, {"login": login})
            return result[0] if result else None
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def register(login, password, access_level, email):
        try:
            hashed = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
            sql = """
                INSERT INTO accounts (login, password, accessLevel, email, created_time)
                VALUES (:login, :password, :access_level, :email, :created_time)
            """
            params = {
                "login": login,
                "password": hashed,
                "access_level": access_level,
                "email": email,
                "created_time": int(time.time())
            }
            LineageDB().insert(sql, params)
            return True
        except Exception as e:
            print(f"Erro ao registrar conta: {e}")
            return None



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
            return LineageDB().select(query, {"account": account, "char_name": char_name})
        except:
            return None

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def search_coin(char_name: str, coin_id: int):
        query = """
            SELECT i.* FROM items i
            JOIN characters c ON i.owner_id = c.charId
            WHERE c.char_name = :char_name AND i.item_id = :coin_id
        """
        return LineageDB().select(query, {"char_name": char_name, "coin_id": coin_id})

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def insert_coin(char_name: str, coin_id: int, amount: int, enchant: int = 0):
        db = LineageDB()

        char_query = "SELECT charId FROM characters WHERE char_name = :char_name"
        char_result = db.select(char_query, {"char_name": char_name})
        if not char_result:
            return None

        owner_id = char_result[0]["charId"]
        
        insert_query = """
            INSERT INTO items (
                owner_id, object_id, item_id, count,
                enchant_level, loc, loc_data
            ) VALUES (
                :owner_id, :object_id, :coin_id, :amount,
                :enchant, 'INVENTORY', 0
            )
        """
        result = db.insert(insert_query, {
            "owner_id": owner_id,
            "object_id": owner_id,
            "coin_id": coin_id,
            "amount": amount,
            "enchant": enchant
        })

        return result is not None



class TransferFromCharToWallet:

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def find_char(account, char_id):
        query = """
            SELECT online, char_name FROM characters 
            WHERE account_name = :account AND charId = :char_id
        """
        params = {"account": account, "char_id": char_id}
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
        params = {"char_id": char_id}
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
        result = db.select(query, {"char_id": char_id, "coin_id": coin_id})
        amount = result[0]["amount"] if result else 0
        enchant = result[0]["enchant"] if result else 0
        return {"total": amount, "inventory": amount, "warehouse": 0, "enchant": enchant}

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def remove_ingame_coin(coin_id, count, char_id):
        try:
            db = LineageDB()
            query = """
                SELECT * FROM items
                WHERE owner_id = :char_id AND item_id = :item_id AND loc = 'INVENTORY'
            """
            items = db.select(query, {"char_id": char_id, "item_id": coin_id})
            
            if not items or sum(item["count"] for item in items) < count:
                return False
                
            for item in items:
                if item["count"] <= count:
                    db.update("DELETE FROM items WHERE object_id = :item_id", {"item_id": item["object_id"]})
                    count -= item["count"]
                else:
                    db.update(
                        "UPDATE items SET count = count - :count WHERE object_id = :item_id",
                        {"count": count, "item_id": item["object_id"]}
                    )
                    count = 0
                    
                if count == 0:
                    break
                    
            return True
        except Exception as e:
            print(f"Erro ao remover coin: {e}")
            return False



class LineageMarketplace:
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def get_user_characters(account_name):
        """Busca todos os characters de uma conta do banco L2."""
        sql = """
            SELECT 
                c.charId as char_id,
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
        return LineageDB().select(sql, {"account_name": account_name})
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def verify_character_ownership(char_id, account_name):
        """Verifica se um character pertence a uma conta específica."""
        sql = """
            SELECT COUNT(*) as total
            FROM characters 
            WHERE charId = :char_id AND account_name = :account_name
        """
        result = LineageDB().select(sql, {"char_id": char_id, "account_name": account_name})
        return result[0]['total'] > 0 if result and len(result) > 0 else False
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def get_character_details(char_id):
        """Busca detalhes completos de um character do banco L2."""
        sql = """
            SELECT 
                c.charId as char_id,
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
            WHERE c.charId = :char_id
        """
        result = LineageDB().select(sql, {"char_id": char_id})
        return result[0] if result and len(result) > 0 else None
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def transfer_character_to_account(char_id, new_account):
        """Transfere um character para nova conta no banco L2."""
        sql = "UPDATE characters SET account_name = :new_account WHERE charId = :char_id"
        result = LineageDB().update(sql, {"new_account": new_account, "char_id": char_id})
        return result is not None and result > 0



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
            INNER JOIN characters c ON c.charId = i.owner_id
            WHERE c.accesslevel = '0'
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
            INNER JOIN characters c ON c.charId = i.owner_id
            WHERE c.accesslevel = '0'
            AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
            GROUP BY i.item_id
            ORDER BY total_quantity DESC
            LIMIT :limit
        """
        return LineageInflation._run_query(sql, {"limit": limit})

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
            INNER JOIN characters c ON c.charId = i.owner_id
            WHERE c.accesslevel = '0'
            AND i.loc IN ('INVENTORY', 'WAREHOUSE', 'PAPERDOLL', 'CLANWH')
            GROUP BY i.loc
            ORDER BY i.loc
        """
        return LineageInflation._run_query(sql)
