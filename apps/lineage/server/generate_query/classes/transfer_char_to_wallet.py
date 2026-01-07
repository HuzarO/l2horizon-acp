"""Template da classe TransferFromCharToWallet - Personagem para Wallet"""

def get_transfer_char_to_wallet_template(char_id: str) -> str:
    """Gera o código da classe TransferFromCharToWallet"""
    
    return f'''class TransferFromCharToWallet:

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

        query_inve = """
            SELECT count AS amount, enchant_level AS enchant FROM items 
            WHERE owner_id = :char_id AND item_id = :coin_id AND loc = 'INVENTORY'
            LIMIT 1
        """
        result_inve = db.select(query_inve, {{"char_id": char_id, "coin_id": coin_id}})
        inINVE = result_inve[0]["amount"] if result_inve else 0
        enchant = result_inve[0]["enchant"] if result_inve else 0

        query_ware = """
            SELECT count AS amount FROM items 
            WHERE owner_id = :char_id AND item_id = :coin_id AND loc = 'WAREHOUSE'
            LIMIT 1
        """
        result_ware = db.select(query_ware, {{"char_id": char_id, "coin_id": coin_id}})
        inWARE = result_ware[0]["amount"] if result_ware else 0

        total = inINVE + inWARE
        return {{"total": total, "inventory": inINVE, "warehouse": inWARE, "enchant": enchant}}

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def remove_ingame_coin(coin_id, count, char_id):
        try:
            db = LineageDB()

            def delete_non_stackable(items, amount_to_remove):
                removed = 0
                for item in items:
                    if removed >= amount_to_remove:
                        break
                    db.update("DELETE FROM items WHERE object_id = :item_id", {{"item_id": item["object_id"]}})
                    removed += 1
                return removed

            query_inve = """
                SELECT * FROM items
                WHERE owner_id = :char_id AND item_id = :item_id AND loc = 'INVENTORY'
            """
            items_inve = db.select(query_inve, {{"char_id": char_id, "item_id": coin_id}})

            query_ware = """
                SELECT * FROM items
                WHERE owner_id = :char_id AND item_id = :item_id AND loc = 'WAREHOUSE'
            """
            items_ware = db.select(query_ware, {{"char_id": char_id, "item_id": coin_id}})

            total_amount = sum(item["count"] for item in items_inve + items_ware)
            if total_amount < count:
                return False

            is_stackable = len(items_inve + items_ware) == 1 and (items_inve + items_ware)[0]["count"] > 1

            if is_stackable:
                if items_inve:
                    item = items_inve[0]
                    if item["count"] <= count:
                        db.update("DELETE FROM items WHERE object_id = :item_id", {{"item_id": item["object_id"]}})
                        count -= item["count"]
                    else:
                        db.update(
                            "UPDATE items SET count = count - :count WHERE object_id = :item_id",
                            {{"count": count, "item_id": item["object_id"]}}
                        )
                        count = 0

                if count > 0 and items_ware:
                    item = items_ware[0]
                    if item["count"] <= count:
                        db.update("DELETE FROM items WHERE object_id = :item_id", {{"item_id": item["object_id"]}})
                    else:
                        db.update(
                            "UPDATE items SET count = count - :count WHERE object_id = :item_id",
                            {{"count": count, "item_id": item["object_id"]}}
                        )

            else:
                removed = delete_non_stackable(items_inve, count)
                if removed < count:
                    delete_non_stackable(items_ware, count - removed)

            return True

        except Exception as e:
            print(f"Erro ao remover coin do inventário/warehouse: {{e}}")
            return False

    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def check_offline_variable(char_id):
        """
        Verifica se o personagem tem a variável 'offline' ativa (loja offline ou atividade ativa).
        Retorna True se encontrar a variável, False caso contrário.
        """
        try:
            db = LineageDB()
            # Tenta com obj_id primeiro (minúsculo), depois obj_Id (maiúsculo)
            query = """
                SELECT * FROM character_variables 
                WHERE obj_id = :char_id AND type = 'user-var' AND name = 'offline'
                LIMIT 1
            """
            result = db.select(query, {{"char_id": char_id}})
            if result:
                return True
            
            # Se não encontrou, tenta com obj_Id (maiúsculo) para compatibilidade
            query_alt = """
                SELECT * FROM character_variables 
                WHERE obj_Id = :char_id AND type = 'user-var' AND name = 'offline'
                LIMIT 1
            """
            result_alt = db.select(query_alt, {{"char_id": char_id}})
            return bool(result_alt)
        except Exception as e:
            print(f"⚠️ Erro ao verificar variável offline: {{e}}")
            return False


'''

