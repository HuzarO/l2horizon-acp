#!/usr/bin/env python3
"""
Script para verificar se as constantes dos arquivos query_*.py estão corretas
"""

import re
from pathlib import Path

querys_dir = Path(__file__).parent.parent / 'querys'

files = [
    'query_acis_v1.py',
    'query_acis_v2.py', 
    'query_ruacis.py',
    'query_classic.py',
    'query_lucerav2.py',
    'query_dreamv2.py',
    'query_dreamv3.py',
    'query_l2jpremium.py',
    'query_default.py'
]

print("=" * 100)
print("VERIFICAÇÃO DAS CONSTANTES - query_*.py")
print("=" * 100)
print()

for filename in files:
    filepath = querys_dir / filename
    
    if not filepath.exists():
        print(f"❌ {filename} - NÃO ENCONTRADO")
        continue
    
    content = filepath.read_text(encoding='utf-8')
    
    # Extrair constantes definidas
    char_id_defined = re.search(r"CHAR_ID = ['\"](\w+)['\"]", content)
    access_defined = re.search(r"ACCESS_LEVEL = ['\"](\w+)['\"]", content)
    clan_source_defined = re.search(r"CLAN_NAME_SOURCE = ['\"](\w+)['\"]", content)
    has_subclass_defined = re.search(r"HAS_SUBCLASS = (\w+)", content)
    
    # Detectar uso REAL nas queries
    uses_obj_id = bool(re.search(r"C\.obj_Id|O\.char_id.*C\.obj_Id", content))
    uses_charid = bool(re.search(r"C\.charId|O\.charId.*C\.charId", content))
    uses_char_id = bool(re.search(r"C\.char_id", content))
    
    uses_accesslevel = bool(re.search(r"C\.accesslevel", content))
    uses_accessLevel = bool(re.search(r"C\.accessLevel", content))
    uses_access_level = bool(re.search(r"C\.access_level", content))
    
    uses_subclass_join = bool(re.search(r"LEFT JOIN character_subclasses", content))
    uses_cs_level = bool(re.search(r"CS\.level", content))
    uses_c_level = bool(re.search(r"C\.level", content))
    
    uses_clan_data_name = bool(re.search(r"D\.clan_name|C\.clan_name", content))
    uses_clan_subpledges = bool(re.search(r"LEFT JOIN clan_subpledges.*D\.name AS clan_name", content, re.DOTALL))
    
    # Determinar valores corretos
    char_id_real = 'obj_Id' if uses_obj_id else ('charId' if uses_charid else 'char_id')
    access_real = 'accesslevel' if uses_accesslevel else ('accessLevel' if uses_accessLevel else 'access_level')
    clan_source_real = 'clan_data' if uses_clan_data_name else 'clan_subpledges'
    has_subclass_real = uses_subclass_join and uses_cs_level
    
    # Comparar
    print(f"📄 {filename}")
    print(f"   {'✅' if char_id_defined and char_id_defined.group(1) == char_id_real else '❌'} CHAR_ID: {char_id_defined.group(1) if char_id_defined else 'NÃO DEFINIDO'} (real: {char_id_real})")
    print(f"   {'✅' if access_defined and access_defined.group(1) == access_real else '❌'} ACCESS_LEVEL: {access_defined.group(1) if access_defined else 'NÃO DEFINIDO'} (real: {access_real})")
    print(f"   {'✅' if clan_source_defined and clan_source_defined.group(1) == clan_source_real else '❌'} CLAN_NAME_SOURCE: {clan_source_defined.group(1) if clan_source_defined else 'NÃO DEFINIDO'} (real: {clan_source_real})")
    print(f"   {'✅' if has_subclass_defined and has_subclass_defined.group(1) == str(has_subclass_real) else '❌'} HAS_SUBCLASS: {has_subclass_defined.group(1) if has_subclass_defined else 'NÃO DEFINIDO'} (real: {has_subclass_real})")
    
    # Detectar problemas
    problemas = []
    if char_id_defined and char_id_defined.group(1) != char_id_real:
        problemas.append(f"CHAR_ID deveria ser '{char_id_real}'")
    if access_defined and access_defined.group(1) != access_real:
        problemas.append(f"ACCESS_LEVEL deveria ser '{access_real}'")
    if clan_source_defined and clan_source_defined.group(1) != clan_source_real:
        problemas.append(f"CLAN_NAME_SOURCE deveria ser '{clan_source_real}'")
    if has_subclass_defined and has_subclass_defined.group(1) != str(has_subclass_real):
        problemas.append(f"HAS_SUBCLASS deveria ser {has_subclass_real}")
    
    if problemas:
        print(f"   ⚠️  PROBLEMAS:")
        for p in problemas:
            print(f"      - {p}")
    
    print()

print("=" * 100)
print("FIM DA VERIFICAÇÃO")
print("=" * 100)

