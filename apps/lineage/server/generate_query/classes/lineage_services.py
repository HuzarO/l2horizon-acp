"""Template da classe LineageServices - Serviços de Personagens"""

def get_lineage_services_template(char_id: str, has_subclass: bool, subclass_char_id: str, base_class_col: str, clan_structure: dict) -> str:
    """
    Gera o código da classe LineageServices
    
    Args:
        char_id: Nome da coluna de ID do personagem
        has_subclass: Se tem tabela character_subclasses
        subclass_char_id: Nome da coluna de ID na tabela de subclasses
        base_class_col: Nome da coluna de classe base
        clan_structure: Estrutura de clans do banco
    """
    
    # Se tem subclass, busca as subclasses
    subclass_queries = ""
    if has_subclass:
        subclass_queries = f"""
                -- Subclass 1
                (SELECT S1.class_id FROM character_subclasses AS S1 
                WHERE S1.{subclass_char_id} = C.{char_id} AND S1.class_index > 0 
                LIMIT 0,1) AS subclass1,
                (SELECT S1.level FROM character_subclasses AS S1 
                WHERE S1.{subclass_char_id} = C.{char_id} AND S1.class_index > 0 
                LIMIT 0,1) AS subclass1_level,

                -- Subclass 2
                (SELECT S2.class_id FROM character_subclasses AS S2 
                WHERE S2.{subclass_char_id} = C.{char_id} AND S2.class_index > 0 
                LIMIT 1,1) AS subclass2,
                (SELECT S2.level FROM character_subclasses AS S2 
                WHERE S2.{subclass_char_id} = C.{char_id} AND S2.class_index > 0 
                LIMIT 1,1) AS subclass2_level,

                -- Subclass 3
                (SELECT S3.class_id FROM character_subclasses AS S3 
                WHERE S3.{subclass_char_id} = C.{char_id} AND S3.class_index > 0 
                LIMIT 2,1) AS subclass3,
                (SELECT S3.level FROM character_subclasses AS S3 
                WHERE S3.{subclass_char_id} = C.{char_id} AND S3.class_index > 0 
                LIMIT 2,1) AS subclass3_level,
"""
    
    # Estrutura de clan
    if clan_structure['clan_name_source'] == 'clan_data':
        clan_join = """
            LEFT JOIN clan_data CLAN ON CLAN.clan_id = C.clanid"""
        clan_name = "CLAN.clan_name"
    elif clan_structure['clan_name_source'] == 'clan_subpledges_simple':
        clan_join = """
            LEFT JOIN clan_subpledges CS ON CS.clan_id = C.clanid
            LEFT JOIN clan_data CLAN ON CLAN.clan_id = C.clanid"""
        clan_name = "CS.name AS clan_name"
    else:
        # clan_subpledges com filtro
        filter_col = clan_structure.get('subpledge_filter', 'sub_pledge_id')
        clan_join = f"""
            LEFT JOIN clan_subpledges CS ON CS.clan_id = C.clanid AND CS.{filter_col} = 0
            LEFT JOIN clan_data CLAN ON CLAN.clan_id = C.clanid"""
        clan_name = "CS.name AS clan_name"
    
    return f'''class LineageServices:

    @staticmethod
    @cache_lineage_result(timeout=300)
    def find_chars(login):
        sql = """
            SELECT
                C.*, 
                C.{base_class_col} AS base_class,
                C.level AS base_level,{subclass_queries}
                {clan_name},
                CLAN.ally_name
            FROM characters AS C{clan_join}
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

