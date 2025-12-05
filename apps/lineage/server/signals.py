import os
import time
import fcntl
from pathlib import Path
from utils.dynamic_import import get_query_class
from sqlalchemy.exc import SQLAlchemyError
from pymysql.err import OperationalError

# Verifica se o banco Lineage está habilitado
if os.getenv("LINEAGE_DB_ENABLED", "false").lower() == "true":
    # Usa lock de arquivo para garantir que apenas UM worker verifica as colunas
    lock_file_path = Path("/tmp") / "lineage_ensure_columns.lock"
    lock_acquired = False
    lock_file = None
    
    try:
        # Tenta adquirir lock (non-blocking)
        lock_file = open(lock_file_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_acquired = True
        
        print("🔧 Verificando estrutura da tabela 'accounts'...")
        LineageAccount = get_query_class("LineageAccount")
        LineageAccount.ensure_columns()
        
    except BlockingIOError:
        # Outro worker já está verificando, este worker pula
        pass
        
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
        
    finally:
        # Libera o lock se foi adquirido
        if lock_acquired and lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                # Remove o arquivo de lock
                if lock_file_path.exists():
                    lock_file_path.unlink()
            except Exception:
                pass
                
else:
    print("ℹ️ Lineage DB desabilitado - funcionalidades L2 não estarão disponíveis")
