import os
import time
import random
from utils.dynamic_import import get_query_class
from sqlalchemy.exc import SQLAlchemyError
from pymysql.err import OperationalError

# Verifica se o banco Lineage está habilitado
if os.getenv("LINEAGE_DB_ENABLED", "false").lower() == "true":
    try:
        # Adiciona um pequeno delay aleatório para evitar que todos os workers
        # tentem conectar ao banco exatamente ao mesmo tempo
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
        
        LineageAccount = get_query_class("LineageAccount")
        LineageAccount.ensure_columns()
    except (SQLAlchemyError, OperationalError) as e:
        error_msg = str(e)
        if "1040" in error_msg or "Too many connections" in error_msg:
            print(f"⚠️ AVISO: Muitas conexoes ao banco Lineage durante startup")
            print("INFO: O worker tentara novamente na proxima requisicao")
        else:
            print(f"AVISO: Nao foi possivel conectar ao banco do Lineage 2: {e}")
        print("INFO: O sistema continuara funcionando normalmente, mas algumas funcionalidades podem estar indisponiveis.")
    except Exception as e:
        print(f"AVISO: Erro inesperado ao verificar colunas do banco: {e}")
        print("INFO: O sistema continuara funcionando normalmente, mas algumas funcionalidades podem estar indisponiveis.")
else:
    print("INFO: Banco Lineage desativado via configuracao - pulando verificacao de colunas")
