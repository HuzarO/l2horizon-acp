"""Template da classe TransferFromWalletToChar - Wallet para Personagem"""

def get_transfer_wallet_to_char_template(
    char_id: str,
    has_items_delayed: bool = False,
    items_delayed_cols: dict = None
) -> str:
    """Gera o código da classe TransferFromWalletToChar"""
    
    # Se tem items_delayed, gera código para usar essa tabela (dreamv3, aCis, etc)
    if has_items_delayed and items_delayed_cols:
        # Usar valores padrão se não foram detectados
        payment_id_col = items_delayed_cols.get('payment_id', 'payment_id')
        owner_id_col = items_delayed_cols.get('owner_id', 'owner_id')
        item_id_col = items_delayed_cols.get('item_id', 'item_id')
        count_col = items_delayed_cols.get('count', 'count')
        enchant_col = items_delayed_cols.get('enchant_level', 'enchant_level')
        desc_col = items_delayed_cols.get('description', 'description')
        
        return f'''class TransferFromWalletToChar:
    items_delayed = True

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

        # Buscar owner_id do personagem
        char_query = "SELECT {char_id} FROM characters WHERE char_name = :char_name"
        char_result = db.select(char_query, {{"char_name": char_name}})
        if not char_result:
            return None

        owner_id = char_result[0]["{char_id}"]

        # Inserir na tabela items_delayed para delivery no jogo
        insert_query = """
            INSERT INTO items_delayed (
                {payment_id_col}, {owner_id_col}, {item_id_col}, {count_col},
                {enchant_col}, variationId1, variationId2,
                flags, payment_status, {desc_col}
            )
            SELECT
                COALESCE(MAX({payment_id_col}), 0) + 1,
                :owner_id, :coin_id, :amount,
                :enchant, 0, 0,
                0, 0, 'DONATE WEB'
            FROM items_delayed
        """

        result = db.insert(insert_query, {{
            "owner_id": owner_id,
            "coin_id": coin_id,
            "amount": amount,
            "enchant": enchant
        }})

        return result is not None


'''
    
    # Se não tem items_delayed, insere direto na tabela items (Mobius, etc)
    else:
        return f'''class TransferFromWalletToChar:
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
        object_id = owner_id

        # Tentar atualizar item existente
        if object_id != 0:
            update_query = """
                UPDATE items SET count = count + :amount
                WHERE object_id = :object_id AND owner_id = :owner_id
            """
            db.update(update_query, {{
                "amount": amount,
                "object_id": object_id,
                "owner_id": owner_id
            }})
            return True

        # Gerar novo object_id
        last_object_query = """
            SELECT object_id FROM items 
            WHERE object_id LIKE '7%' 
            ORDER BY object_id DESC LIMIT 1
        """
        last_object_result = db.select(last_object_query)
        if not last_object_result:
            new_object_id = 700000000
        else:
            last_object_id = int(last_object_result[0]["object_id"])
            new_object_id = last_object_id + 1

        # Gerar novo loc_data
        last_loc_query = """
            SELECT loc_data FROM items 
            WHERE owner_id = :owner_id 
            ORDER BY loc_data DESC LIMIT 1
        """
        last_loc_result = db.select(last_loc_query, {{"owner_id": owner_id}})
        if not last_loc_result:
            new_loc_data = 0
        else:
            last_loc_data = int(last_loc_result[0]["loc_data"])
            new_loc_data = last_loc_data + 1

        # Inserir novo item diretamente na tabela items
        insert_query = """
            INSERT INTO items (
                owner_id, object_id, item_id, count,
                enchant_level, loc, loc_data
            ) VALUES (
                :owner_id, :object_id, :coin_id, :amount,
                :enchant, 'INVENTORY', :loc_data
            )
        """
        result = db.insert(insert_query, {{
            "owner_id": owner_id,
            "object_id": new_object_id,
            "coin_id": coin_id,
            "amount": amount,
            "enchant": enchant,
            "loc_data": new_loc_data
        }})

        return result is not None


'''

