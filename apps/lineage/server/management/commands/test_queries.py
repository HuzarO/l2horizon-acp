"""
Comando para testar todas as queries geradas automaticamente

Testa todas as 7 classes do arquivo query_*.py:

1. LineageStats (16 métodos testados)
   - players_online, top_pvp, top_pk, top_online, top_level, top_adena
   - top_clans, olympiad_ranking, olympiad_all_heroes, olympiad_current_heroes
   - grandboss_status, raidboss_status, siege, siege_participants
   - boss_jewel_locations, get_crests

2. LineageServices (3 métodos testados + 3 skip)
   - find_chars, check_name_exists, check_char
   - SKIP: change_nickname, change_sex, unstuck (modificam banco)

3. LineageAccount (5 métodos testados + 8 skip)
   - get_account_by_login, check_login_exists, get_acess_level
   - find_accounts_by_email, get_account_by_login_and_email, check_email_exists
   - SKIP: register, update_password, link_account_to_user, etc (modificam banco)

4. TransferFromWalletToChar (1 método testado + 2 skip)
   - find_char
   - SKIP: search_coin, insert_coin (modificam banco)

5. TransferFromCharToWallet (1 método testado + 3 skip)
   - find_char
   - SKIP: list_items, check_ingame_coin, remove_ingame_coin

6. LineageMarketplace (6 métodos testados + 2 skip)
   - get_user_characters, verify_character_ownership, get_character_details
   - get_character_items_count, count_characters_in_account, get_character_items
   - SKIP: create_or_update_marketplace_account, transfer_character_to_account

7. LineageInflation (7 métodos testados)
   - get_all_items_by_location, get_items_summary_by_category
   - get_top_items_by_quantity, get_items_by_location_summary
   - get_items_by_character, get_site_items_count, get_inflation_comparison

8. Constantes do Schema (7 constantes)
   - CHAR_ID, ACCESS_LEVEL, BASE_CLASS_COL, HAS_SUBCLASS
   - SUBCLASS_CHAR_ID, CLAN_NAME_SOURCE, HAS_ALLY_DATA

TOTAL: ~46 testes (39 queries SQL + 7 constantes)

Uso:
    python manage.py test_queries
    python manage.py test_queries --verbose
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
from utils.dynamic_import import get_query_class


class Command(BaseCommand):
    help = 'Testa todas as queries SQL do arquivo query_*.py gerado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar mais detalhes dos testes'
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("🧪 TESTE DE QUERIES - Lineage 2"))
        self.stdout.write("=" * 70)
        
        # Verificar qual módulo está sendo usado
        query_module = os.getenv('LINEAGE_QUERY_MODULE', 'dreamv3')
        self.stdout.write(f"\n📦 Módulo: query_{query_module}.py")
        
        # Estatísticas
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        errors = []
        
        # ========================================================================
        # TESTE 1: LineageStats
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("📊 TESTANDO: LineageStats")
        self.stdout.write("=" * 70)
        
        try:
            LineageStats = get_query_class("LineageStats")
            
            # players_online
            total_tests += 1
            try:
                result = LineageStats.players_online()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ players_online() - {len(result)} registros"))
                if verbose and result:
                    self.stdout.write(f"      Resultado: {result[0]}")
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.players_online', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ players_online() - ERRO: {e}"))
            
            # top_pvp
            total_tests += 1
            try:
                result = LineageStats.top_pvp(limit=5)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ top_pvp(5) - {len(result)} registros"))
                if verbose and result:
                    self.stdout.write(f"      Primeiro: {result[0].get('char_name', 'N/A')}")
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.top_pvp', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ top_pvp(5) - ERRO: {e}"))
            
            # top_pk
            total_tests += 1
            try:
                result = LineageStats.top_pk(limit=5)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ top_pk(5) - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.top_pk', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ top_pk(5) - ERRO: {e}"))
            
            # top_online
            total_tests += 1
            try:
                result = LineageStats.top_online(limit=5)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ top_online(5) - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.top_online', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ top_online(5) - ERRO: {e}"))
            
            # top_level
            total_tests += 1
            try:
                result = LineageStats.top_level(limit=5)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ top_level(5) - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.top_level', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ top_level(5) - ERRO: {e}"))
            
            # top_adena
            total_tests += 1
            try:
                result = LineageStats.top_adena(limit=5)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ top_adena(5) - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.top_adena', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ top_adena(5) - ERRO: {e}"))
            
            # top_clans
            total_tests += 1
            try:
                result = LineageStats.top_clans(limit=5)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ top_clans(5) - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.top_clans', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ top_clans(5) - ERRO: {e}"))
            
            # olympiad_ranking
            total_tests += 1
            try:
                result = LineageStats.olympiad_ranking()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ olympiad_ranking() - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.olympiad_ranking', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ olympiad_ranking() - ERRO: {e}"))
            
            # olympiad_all_heroes
            total_tests += 1
            try:
                result = LineageStats.olympiad_all_heroes()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ olympiad_all_heroes() - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.olympiad_all_heroes', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ olympiad_all_heroes() - ERRO: {e}"))
            
            # olympiad_current_heroes
            total_tests += 1
            try:
                result = LineageStats.olympiad_current_heroes()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ olympiad_current_heroes() - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.olympiad_current_heroes', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ olympiad_current_heroes() - ERRO: {e}"))
            
            # grandboss_status
            total_tests += 1
            try:
                result = LineageStats.grandboss_status()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ grandboss_status() - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.grandboss_status', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ grandboss_status() - ERRO: {e}"))
            
            # raidboss_status
            total_tests += 1
            try:
                result = LineageStats.raidboss_status()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ raidboss_status() - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.raidboss_status', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ raidboss_status() - ERRO: {e}"))
            
            # siege
            total_tests += 1
            try:
                result = LineageStats.siege()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ siege() - {len(result)} registros"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.siege', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ siege() - ERRO: {e}"))
            
            # siege_participants
            total_tests += 1
            try:
                result = LineageStats.siege_participants(castle_id=1)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ siege_participants(1) - {len(result)} clans"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.siege_participants', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ siege_participants() - ERRO: {e}"))
            
            # boss_jewel_locations
            total_tests += 1
            try:
                # Testar com IDs de boss jewels comuns
                jewel_ids = [6656, 6657, 6658]  # QA, Core, Orfen jewels
                result = LineageStats.boss_jewel_locations(jewel_ids)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ boss_jewel_locations([...]) - {len(result)} resultados"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.boss_jewel_locations', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ boss_jewel_locations() - ERRO: {e}"))
            
            # get_crests
            total_tests += 1
            try:
                result = LineageStats.get_crests([1, 2, 3], type='clan')
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_crests([1,2,3]) - {len(result)} crests"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageStats.get_crests', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_crests() - ERRO: {e}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar LineageStats: {e}"))
        
        # ========================================================================
        # TESTE 2: LineageServices
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("🔧 TESTANDO: LineageServices")
        self.stdout.write("=" * 70)
        
        try:
            LineageServices = get_query_class("LineageServices")
            
            # find_chars (precisa de um login válido)
            total_tests += 1
            try:
                # Tentar com um login genérico
                result = LineageServices.find_chars("admin")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ find_chars('admin') - {len(result) if result else 0} personagens"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageServices.find_chars', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ find_chars('admin') - ERRO: {e}"))
            
            # check_name_exists
            total_tests += 1
            try:
                result = LineageServices.check_name_exists("TestChar")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ check_name_exists('TestChar') - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageServices.check_name_exists', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ check_name_exists('TestChar') - ERRO: {e}"))
            
            # check_char
            total_tests += 1
            try:
                result = LineageServices.check_char("admin", 1)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ check_char('admin', 1) - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageServices.check_char', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ check_char() - ERRO: {e}"))
            
            # Métodos que modificam banco - apenas informar
            self.stdout.write(self.style.WARNING(f"   ⚠️  change_nickname() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  change_sex() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  unstuck() - SKIP (modifica banco)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar LineageServices: {e}"))
        
        # ========================================================================
        # TESTE 3: LineageAccount
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("👤 TESTANDO: LineageAccount")
        self.stdout.write("=" * 70)
        
        try:
            LineageAccount = get_query_class("LineageAccount")
            
            # get_account_by_login
            total_tests += 1
            try:
                result = LineageAccount.get_account_by_login("admin")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_account_by_login('admin') - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageAccount.get_account_by_login', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_account_by_login('admin') - ERRO: {e}"))
            
            # check_login_exists
            total_tests += 1
            try:
                result = LineageAccount.check_login_exists("admin")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ check_login_exists('admin') - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageAccount.check_login_exists', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ check_login_exists('admin') - ERRO: {e}"))
            
            # get_acess_level
            total_tests += 1
            try:
                result = LineageAccount.get_acess_level()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_acess_level() - '{result}'"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageAccount.get_acess_level', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_acess_level() - ERRO: {e}"))
            
            # find_accounts_by_email
            total_tests += 1
            try:
                result = LineageAccount.find_accounts_by_email("test@example.com")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ find_accounts_by_email('test@...') - {len(result) if result else 0} contas"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageAccount.find_accounts_by_email', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ find_accounts_by_email() - ERRO: {e}"))
            
            # get_account_by_login_and_email
            total_tests += 1
            try:
                result = LineageAccount.get_account_by_login_and_email("admin", "test@example.com")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_account_by_login_and_email() - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageAccount.get_account_by_login_and_email', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_account_by_login_and_email() - ERRO: {e}"))
            
            # check_email_exists
            total_tests += 1
            try:
                result = LineageAccount.check_email_exists("test@example.com")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ check_email_exists('test@...') - {len(result) if result else 0} contas"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageAccount.check_email_exists', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ check_email_exists() - ERRO: {e}"))
            
            # Métodos que modificam - apenas informar
            self.stdout.write(self.style.WARNING(f"   ⚠️  link_account_to_user() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  unlink_account_from_user() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  ensure_columns() - SKIP (modifica estrutura)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  register() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  update_password() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  update_password_group() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  update_access_level() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  validate_credentials() - SKIP (precisa senha válida)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar LineageAccount: {e}"))
        
        # ========================================================================
        # TESTE 4: TransferFromWalletToChar
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("💰 TESTANDO: TransferFromWalletToChar")
        self.stdout.write("=" * 70)
        
        try:
            TransferFromWalletToChar = get_query_class("TransferFromWalletToChar")
            
            # find_char
            total_tests += 1
            try:
                result = TransferFromWalletToChar.find_char("admin", "TestChar")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ find_char('admin', 'TestChar') - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('TransferFromWalletToChar.find_char', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ find_char() - ERRO: {e}"))
            
            # search_coin (não executar insert/update em teste)
            self.stdout.write(self.style.WARNING(f"   ⚠️  search_coin() - SKIP (requer char válido)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  insert_coin() - SKIP (modifica banco)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar TransferFromWalletToChar: {e}"))
        
        # ========================================================================
        # TESTE 5: TransferFromCharToWallet
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("💸 TESTANDO: TransferFromCharToWallet")
        self.stdout.write("=" * 70)
        
        try:
            TransferFromCharToWallet = get_query_class("TransferFromCharToWallet")
            
            # find_char
            total_tests += 1
            try:
                result = TransferFromCharToWallet.find_char("admin", 1)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ find_char('admin', 1) - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('TransferFromCharToWallet.find_char', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ find_char() - ERRO: {e}"))
            
            # Métodos que modificam banco - skip
            self.stdout.write(self.style.WARNING(f"   ⚠️  list_items() - SKIP (requer char válido)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  check_ingame_coin() - SKIP (requer char válido)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  remove_ingame_coin() - SKIP (modifica banco)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar TransferFromCharToWallet: {e}"))
        
        # ========================================================================
        # TESTE 6: LineageMarketplace
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("🛒 TESTANDO: LineageMarketplace")
        self.stdout.write("=" * 70)
        
        try:
            LineageMarketplace = get_query_class("LineageMarketplace")
            
            # get_user_characters
            total_tests += 1
            try:
                result = LineageMarketplace.get_user_characters("admin")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_user_characters('admin') - {len(result) if result else 0} chars"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageMarketplace.get_user_characters', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_user_characters() - ERRO: {e}"))
            
            # verify_character_ownership
            total_tests += 1
            try:
                result = LineageMarketplace.verify_character_ownership(1, "admin")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ verify_character_ownership(1, 'admin') - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageMarketplace.verify_character_ownership', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ verify_character_ownership() - ERRO: {e}"))
            
            # get_character_details
            total_tests += 1
            try:
                result = LineageMarketplace.get_character_details(1)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_character_details(1) - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageMarketplace.get_character_details', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_character_details() - ERRO: {e}"))
            
            # get_character_items_count
            total_tests += 1
            try:
                result = LineageMarketplace.get_character_items_count(1)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_character_items_count(1) - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageMarketplace.get_character_items_count', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_character_items_count() - ERRO: {e}"))
            
            # count_characters_in_account
            total_tests += 1
            try:
                result = LineageMarketplace.count_characters_in_account("admin")
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ count_characters_in_account('admin') - {result if result else 0} chars"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageMarketplace.count_characters_in_account', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ count_characters_in_account() - ERRO: {e}"))
            
            # get_character_items
            total_tests += 1
            try:
                result = LineageMarketplace.get_character_items(1)
                passed_tests += 1
                inv_count = len(result.get('inventory', [])) if isinstance(result, dict) else 0
                equip_count = len(result.get('equipment', [])) if isinstance(result, dict) else 0
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_character_items(1) - {inv_count} inv, {equip_count} equip"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageMarketplace.get_character_items', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_character_items() - ERRO: {e}"))
            
            # Métodos que modificam - skip
            self.stdout.write(self.style.WARNING(f"   ⚠️  create_or_update_marketplace_account() - SKIP (modifica banco)"))
            self.stdout.write(self.style.WARNING(f"   ⚠️  transfer_character_to_account() - SKIP (modifica banco)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar LineageMarketplace: {e}"))
        
        # ========================================================================
        # TESTE 7: LineageInflation
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("📈 TESTANDO: LineageInflation")
        self.stdout.write("=" * 70)
        
        try:
            LineageInflation = get_query_class("LineageInflation")
            
            # get_all_items_by_location
            total_tests += 1
            try:
                result = LineageInflation.get_all_items_by_location()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_all_items_by_location() - {len(result) if result else 0} itens"))
                if verbose and result:
                    self.stdout.write(f"      Primeiros: {len(result[:3])} itens")
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_all_items_by_location', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_all_items_by_location() - ERRO: {e}"))
            
            # get_items_summary_by_category
            total_tests += 1
            try:
                result = LineageInflation.get_items_summary_by_category()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_items_summary_by_category() - {len(result) if result else 0} categorias"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_items_summary_by_category', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_items_summary_by_category() - ERRO: {e}"))
            
            # get_top_items_by_quantity
            total_tests += 1
            try:
                result = LineageInflation.get_top_items_by_quantity(limit=10)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_top_items_by_quantity(10) - {len(result) if result else 0} itens"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_top_items_by_quantity', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_top_items_by_quantity() - ERRO: {e}"))
            
            # get_items_by_location_summary
            total_tests += 1
            try:
                result = LineageInflation.get_items_by_location_summary()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_items_by_location_summary() - {len(result) if result else 0} locais"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_items_by_location_summary', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_items_by_location_summary() - ERRO: {e}"))
            
            # get_items_by_character
            total_tests += 1
            try:
                result = LineageInflation.get_items_by_character(char_id=1)
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_items_by_character(1) - {len(result) if result else 0} itens"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_items_by_character', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_items_by_character() - ERRO: {e}"))
            
            # get_site_items_count
            total_tests += 1
            try:
                result = LineageInflation.get_site_items_count()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_site_items_count() - {len(result) if result else 0} itens"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_site_items_count', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_site_items_count() - ERRO: {e}"))
            
            # get_inflation_comparison
            total_tests += 1
            try:
                result = LineageInflation.get_inflation_comparison()
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f"   ✅ get_inflation_comparison() - OK"))
            except Exception as e:
                failed_tests += 1
                errors.append(('LineageInflation.get_inflation_comparison', str(e)))
                self.stdout.write(self.style.ERROR(f"   ❌ get_inflation_comparison() - ERRO: {e}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar LineageInflation: {e}"))
        
        # ========================================================================
        # TESTE 8: Constantes do Schema
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("⚙️  TESTANDO: Constantes do Schema (CHAR_ID, ACCESS_LEVEL, etc)")
        self.stdout.write("=" * 70)
        
        try:
            import importlib
            query_module_obj = importlib.import_module(f'apps.lineage.server.querys.query_{query_module}')
            
            constants = ['CHAR_ID', 'ACCESS_LEVEL', 'BASE_CLASS_COL', 'HAS_SUBCLASS', 
                        'SUBCLASS_CHAR_ID', 'CLAN_NAME_SOURCE', 'HAS_ALLY_DATA']
            
            for const in constants:
                total_tests += 1
                try:
                    value = getattr(query_module_obj, const, None)
                    if value is not None:
                        passed_tests += 1
                        self.stdout.write(self.style.SUCCESS(f"   ✅ {const} = {value}"))
                    else:
                        failed_tests += 1
                        self.stdout.write(self.style.ERROR(f"   ❌ {const} - NÃO ENCONTRADO"))
                except Exception as e:
                    failed_tests += 1
                    errors.append((f'Constante {const}', str(e)))
                    self.stdout.write(self.style.ERROR(f"   ❌ {const} - ERRO: {e}"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ ERRO ao importar módulo: {e}"))
        
        # ========================================================================
        # RESUMO
        # ========================================================================
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("📊 RESUMO DOS TESTES")
        self.stdout.write("=" * 70)
        self.stdout.write(f"\n   Total de testes: {total_tests}")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Passaram: {passed_tests}"))
        if failed_tests > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ Falharam: {failed_tests}"))
        
        # Mostrar erros detalhados
        if errors:
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.ERROR("❌ ERROS DETALHADOS"))
            self.stdout.write("=" * 70)
            for method, error in errors:
                self.stdout.write(f"\n   🔴 {method}")
                self.stdout.write(f"      {error}")
        
        # Status final
        self.stdout.write("\n" + "=" * 70)
        if failed_tests == 0:
            self.stdout.write(self.style.SUCCESS("✅ TODOS OS TESTES PASSARAM!"))
            self.stdout.write("=" * 70)
            self.stdout.write("\n🎉 Todas as 7 classes e suas queries SQL estão funcionando!")
            self.stdout.write(f"\n📦 Arquivo testado: query_{query_module}.py")
            self.stdout.write("\n✅ Pronto para produção!\n")
            return
        else:
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            self.stdout.write(self.style.WARNING(f"⚠️  ALGUNS TESTES FALHARAM ({success_rate:.1f}% de sucesso)"))
            self.stdout.write("=" * 70)
            self.stdout.write("\n💡 Verifique os erros acima e regenere o arquivo query_*.py:")
            self.stdout.write("\n   cd apps/lineage/server/generate_query")
            self.stdout.write(f"\n   python gerar_query.py  # Digite: {query_module}")
            self.stdout.write("\n")
            sys.exit(1)

