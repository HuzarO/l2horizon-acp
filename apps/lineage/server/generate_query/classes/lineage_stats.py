"""Template da classe LineageStats - Rankings e Estatísticas"""

def get_lineage_stats_template(char_id: str, access_level: str, has_subclass: bool, 
                                subclass_char_id: str, clan_structure: dict, base_class_col: str = 'classid',
                                clan_id_col: str = 'clan_id', crest_col: str = None) -> str:
    """
    Gera o código da classe LineageStats
    
    Args:
        char_id: Nome da coluna de ID do personagem (obj_Id, charId, char_id)
        access_level: Nome da coluna de access level
        has_subclass: Se tem tabela character_subclasses
        subclass_char_id: Nome da coluna de ID na tabela de subclasses
        clan_structure: Dict com estrutura de clans
        base_class_col: Nome da coluna de classe base (classid, base_class)
        clan_id_col: Nome da coluna de ID do clan (clan_id, clanId, id)
        crest_col: Nome da coluna de crest (crest_id, crestId, crest) ou None se não existir
    """
    
    # Determinar JOIN com clan
    if clan_structure['clan_name_source'] == 'clan_data':
        # clan_name diretamente em clan_data
        clan_join = """
            LEFT JOIN clan_data D ON D.clan_id = C.clanid"""
        clan_name_field = "D.clan_name"
        ally_field = "D.ally_id"
    elif clan_structure['clan_name_source'] == 'clan_subpledges_simple':
        # clan_subpledges sem filtro (tabela simples)
        clan_join = """
            LEFT JOIN clan_subpledges D ON D.clan_id = C.clanid
            LEFT JOIN clan_data CD ON CD.clan_id = C.clanid"""
        clan_name_field = "D.name AS clan_name"
        ally_field = "CD.ally_id"
    else:
        # clan_subpledges com filtro (sub_pledge_id ou type)
        filter_col = clan_structure.get('subpledge_filter', 'sub_pledge_id')
        clan_join = f"""
            LEFT JOIN clan_subpledges D ON D.clan_id = C.clanid AND D.{filter_col} = 0
            LEFT JOIN clan_data CD ON CD.clan_id = C.clanid"""
        clan_name_field = "D.name AS clan_name"
        ally_field = "CD.ally_id"
    
    # Subclass JOIN
    subclass_join = ""
    level_source = "C.level"
    class_source = f"C.{base_class_col}"
    
    if has_subclass:
        subclass_join = f"""
            LEFT JOIN character_subclasses CS ON CS.{subclass_char_id} = C.{char_id} AND CS.isBase = '1'"""
        level_source = "CS.level"
        class_source = "CS.class_id"
    
    # Construir query de get_crests baseada nas colunas reais
    if crest_col:
        crests_select = f"{clan_id_col}, {crest_col}"
    else:
        # Se não tem coluna de crest, retornar apenas o ID do clan
        crests_select = clan_id_col
    
    return f'''class LineageStats:

    @staticmethod
    def _run_query(sql, params=None, use_cache=True):
        return LineageDB().select(sql, params=params, use_cache=use_cache)
    
    @staticmethod
    @cache_lineage_result(timeout=300)
    def get_crests(ids, type='clan'):
        if not ids:
            return []

        sql = f"""
            SELECT {crests_select}
            FROM clan_data
            WHERE {clan_id_col} IN :ids
        """
        return LineageStats._run_query(sql, {{"ids": tuple(ids)}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def players_online():
        sql = "SELECT COUNT(*) AS quant FROM characters WHERE online > 0 AND {access_level} = '0'"
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
                {level_source},
                {class_source} AS base,
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY pvpkills DESC, pkkills DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

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
                {level_source},
                {class_source} AS base,
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY pkkills DESC, pvpkills DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

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
                {level_source},
                {class_source} AS base,
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY onlinetime DESC, pvpkills DESC, pkkills DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

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
                {level_source},
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY {level_source} DESC, C.onlinetime DESC, C.char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def top_adena(limit=10, adn_billion_item=0, value_item=1000000):
        item_bonus_sql = ""
        if adn_billion_item != 0:
            item_bonus_sql = f"""
                IFNULL((SELECT SUM(I2.count) * :value_item
                        FROM items I2
                        WHERE I2.owner_id = C.{char_id} AND I2.item_id = :adn_billion_item
                        GROUP BY I2.owner_id), 0) +
            """
        sql = f"""
            SELECT 
                C.char_name, 
                C.online, 
                C.onlinetime, 
                {level_source}, 
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                (
                    {{{{item_bonus_sql}}}}
                    IFNULL((SELECT SUM(I1.count)
                            FROM items I1
                            WHERE I1.owner_id = C.{char_id} AND I1.item_id = '57'
                            GROUP BY I1.owner_id), 0)
                ) AS adenas
            FROM characters C{subclass_join}{clan_join}
            WHERE C.{access_level} = '0'
            ORDER BY adenas DESC, onlinetime DESC, char_name ASC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{
            "limit": limit,
            "adn_billion_item": adn_billion_item,
            "value_item": value_item
        }})

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
            LEFT JOIN characters P ON P.{char_id} = C.leader_id
            ORDER BY C.clan_level DESC, C.reputation_score DESC, membros DESC
            LIMIT :limit
        """
        return LineageStats._run_query(sql, {{"limit": limit}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def olympiad_ranking():
        sql = """
            SELECT 
                C.char_name, 
                C.online, 
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                {class_source} AS base, 
                O.olympiad_points
            FROM olympiad_nobles O
            LEFT JOIN characters C ON C.{char_id} = O.char_id{subclass_join}{clan_join}
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
                {clan_name_field}, 
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                {class_source} AS base, 
                H.count
            FROM heroes H
            LEFT JOIN characters C ON C.{char_id} = H.char_id{subclass_join}{clan_join}
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
                {clan_name_field},
                C.clanid AS clan_id,
                {ally_field} AS ally_id,
                {class_source} AS base
            FROM heroes H
            LEFT JOIN characters C ON C.{char_id} = H.char_id{subclass_join}{clan_join}
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
    def raidboss_status():
        sql = """
            SELECT 
                B.boss_id,
                B.respawn_time AS respawn,
                CASE 
                    WHEN B.respawn_time IS NULL OR B.respawn_time = 0 THEN 'Alive'
                    WHEN (
                        (B.respawn_time > 9999999999 AND B.respawn_time > UNIX_TIMESTAMP() * 1000) OR
                        (B.respawn_time <= 9999999999 AND B.respawn_time > UNIX_TIMESTAMP())
                    ) THEN 'Dead'
                    ELSE 'Alive'
                END AS status,
                CASE 
                    WHEN B.respawn_time IS NULL OR B.respawn_time = 0 THEN NULL
                    WHEN B.respawn_time > 9999999999 THEN FROM_UNIXTIME(B.respawn_time / 1000)
                    ELSE FROM_UNIXTIME(B.respawn_time)
                END AS respawn_human
            FROM raidboss_spawnlist B
            ORDER BY respawn DESC
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
            LEFT JOIN characters P ON P.{char_id} = C.leader_id
        """
        return LineageStats._run_query(sql)

    @staticmethod
    @cache_lineage_result(timeout=300)
    def siege_participants(castle_id):
        sql = """
            SELECT 
                S.type, 
                C.name AS clan_name,
                C.clan_id
            FROM siege_clans S
            LEFT JOIN clan_subpledges C ON C.clan_id = S.clan_id AND C.sub_pledge_id = 0
            WHERE S.castle_id = :castle_id
        """
        return LineageStats._run_query(sql, {{"castle_id": castle_id}})

    @staticmethod
    @cache_lineage_result(timeout=300)
    def boss_jewel_locations(boss_jewel_ids):
        bind_ids = [f":id{{i}}" for i in range(len(boss_jewel_ids))]
        placeholders = ", ".join(bind_ids)
        sql = f"""
            SELECT 
                I.owner_id, 
                I.item_id, 
                SUM(I.count) AS count,
                C.char_name,
                P.name AS clan_name,
                C.clanid AS clan_id,
                CD.ally_id
            FROM items I
            INNER JOIN characters C ON C.{char_id} = I.owner_id
            LEFT JOIN clan_subpledges P ON P.clan_id = C.clanid AND P.sub_pledge_id = 0
            LEFT JOIN clan_data CD ON CD.clan_id = C.clanid
            WHERE I.item_id IN ({{{{placeholders}}}})
            GROUP BY I.owner_id, C.char_name, P.name, I.item_id, C.clanid, CD.ally_id
            ORDER BY count DESC, C.char_name ASC
        """
        params = {{f"id{{i}}": item_id for i, item_id in enumerate(boss_jewel_ids)}}
        return LineageStats._run_query(sql, params)


'''

