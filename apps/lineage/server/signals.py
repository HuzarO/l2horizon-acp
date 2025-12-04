import os
from utils.dynamic_import import get_query_class
from sqlalchemy.exc import SQLAlchemyError
from pymysql.err import OperationalError

# Verifica se o banco Lineage está habilitado
if os.getenv("LINEAGE_DB_ENABLED", "false").lower() == "true":
    try:
        LineageAccount = get_query_class("LineageAccount")
        LineageAccount.ensure_columns()
    except (SQLAlchemyError, OperationalError) as e:
        print(f"AVISO: Nao foi possivel conectar ao banco do Lineage 2: {e}")
        print("INFO: O sistema continuara funcionando normalmente, mas algumas funcionalidades podem estar indisponiveis.")
    except Exception as e:
        print(f"AVISO: Erro inesperado ao verificar colunas do banco: {e}")
        print("INFO: O sistema continuara funcionando normalmente, mas algumas funcionalidades podem estar indisponiveis.")
else:
    print("INFO: Banco Lineage desativado via configuracao - pulando verificacao de colunas")
