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
            print("⚠️ MySQL sobrecarga no startup - colunas serão verificadas na próxima requisição")
        else:
            print(f"⚠️ Falha ao conectar ao Lineage DB: {str(e)[:100]}")
            print("ℹ️ Sistema continuará funcionando, mas funcionalidades L2 podem estar limitadas")
    except Exception as e:
        print(f"⚠️ Erro inesperado ao verificar colunas: {str(e)[:100]}")
        print("ℹ️ Sistema continuará funcionando, mas funcionalidades L2 podem estar limitadas")
else:
    print("ℹ️ Lineage DB desabilitado - funcionalidades L2 não estarão disponíveis")
