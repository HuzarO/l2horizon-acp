"""Template da classe LineageMarketplace - Sistema de Marketplace"""

def get_lineage_marketplace_template(char_id: str) -> str:
    """Gera o código da classe LineageMarketplace"""
    
    return f'''class LineageMarketplace:
    
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
    def get_character_items_count(char_id):
        """Conta quantos itens um character possui no banco L2."""
        sql = """
            SELECT COUNT(*) as total_items
            FROM items 
            WHERE owner_id = :char_id
            AND (loc = 'INVENTORY' OR loc = 'PAPERDOLL')
        """
        result = LineageDB().select(sql, {{"char_id": char_id}})
        return result[0]['total_items'] if result and len(result) > 0 else 0
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def get_character_items(char_id):
        """Busca todos os itens de um character do banco L2."""
        sql = """
            SELECT 
                i.object_id,
                i.item_id,
                i.count,
                i.enchant_level,
                i.loc,
                i.loc_data
            FROM items i
            WHERE i.owner_id = :char_id
            AND (i.loc = 'INVENTORY' OR i.loc = 'PAPERDOLL')
            ORDER BY i.loc, i.loc_data
        """
        result = LineageDB().select(sql, {{"char_id": char_id}})
        
        if result is None:
            return {{'inventory': [], 'equipment': []}}
        
        inventory_items = []
        equipment_items = []
        
        for item_data in result:
            if item_data['loc'] == 'INVENTORY':
                inventory_items.append(item_data)
            elif item_data['loc'] == 'PAPERDOLL':
                equipment_items.append(item_data)
        
        return {{
            'inventory': inventory_items,
            'equipment': equipment_items
        }}
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def count_characters_in_account(account_name):
        """Conta quantos personagens existem em uma conta."""
        sql = """
            SELECT COUNT(*) as total
            FROM characters 
            WHERE account_name = :account_name
        """
        result = LineageDB().select(sql, {{"account_name": account_name}})
        return result[0]['total'] if result and len(result) > 0 else 0
    
    @staticmethod
    def create_or_update_marketplace_account(account_name, password_hash):
        """Cria ou atualiza a conta mestre do marketplace no banco L2."""
        db = LineageDB()
        
        check_sql = "SELECT login FROM accounts WHERE login = :account_name"
        existing = db.select(check_sql, {{"account_name": account_name}})
        
        try:
            if existing and len(existing) > 0:
                update_sql = """
                    UPDATE accounts 
                    SET password = :password_hash,
                        accessLevel = 0,
                        lastactive = UNIX_TIMESTAMP()
                    WHERE login = :account_name
                """
                result = db.update(update_sql, {{
                    "password_hash": password_hash,
                    "account_name": account_name
                }})
                return result is not None and result > 0
            else:
                insert_sql = """
                    INSERT INTO accounts (login, password, accessLevel, lastactive)
                    VALUES (:account_name, :password_hash, 0, UNIX_TIMESTAMP())
                """
                result = db.insert(insert_sql, {{
                    "account_name": account_name,
                    "password_hash": password_hash
                }})
                return result is not None
        except Exception as e:
            print(f"❌ Erro ao criar/atualizar conta: {{e}}")
            return False
    
    @staticmethod
    @cache_lineage_result(timeout=300, use_cache=False)
    def transfer_character_to_account(char_id, new_account):
        """Transfere um character para nova conta no banco L2."""
        sql = "UPDATE characters SET account_name = :new_account WHERE {char_id} = :char_id"
        result = LineageDB().update(sql, {{"new_account": new_account, "char_id": char_id}})
        return result is not None and result > 0


'''

