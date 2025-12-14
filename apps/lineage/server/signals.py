import os
import sys
import time
from pathlib import Path
from utils.dynamic_import import get_query_class
from sqlalchemy.exc import SQLAlchemyError
from pymysql.err import OperationalError

# Imports condicionais para file locking (Unix vs Windows)
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl

def acquire_lock(lock_file):
    """Adquire lock de arquivo de forma compatível com Windows e Unix"""
    if sys.platform == 'win32':
        # Windows: usa msvcrt
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    else:
        # Unix/Linux: usa fcntl
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False

def release_lock(lock_file):
    """Libera lock de arquivo de forma compatível com Windows e Unix"""
    if sys.platform == 'win32':
        # Windows: usa msvcrt
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
    else:
        # Unix/Linux: usa fcntl
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass

def ensure_lineage_columns():
    """
    Verifica e cria colunas necessárias no banco Lineage.
    Esta função é chamada de forma lazy para evitar acesso ao banco durante inicialização.
    """
    # Verifica se o banco Lineage está habilitado
    if os.getenv("LINEAGE_DB_ENABLED", "false").lower() != "true":
        print("ℹ️ Lineage DB desabilitado - funcionalidades L2 não estarão disponíveis")
        return
    
    # Usa lock de arquivo para garantir que apenas UM worker verifica as colunas
    # Caminho compatível com Windows e Unix
    if sys.platform == 'win32':
        lock_dir = Path(os.getenv('TEMP', 'C:\\Windows\\Temp'))
    else:
        lock_dir = Path("/tmp")
    
    lock_file_path = lock_dir / "lineage_ensure_columns.lock"
    lock_acquired = False
    lock_file = None
    
    try:
        # 🔥 NOVO: Delay baseado no PID para evitar sobrecarga no startup
        import random
        startup_delay = random.uniform(0.5, 2.0)  # 0.5 a 2 segundos
        time.sleep(startup_delay)
        
        # Tenta adquirir lock (non-blocking)
        lock_file = open(lock_file_path, 'w')
        lock_acquired = acquire_lock(lock_file)
        
        if lock_acquired:
            print("🔧 Verificando estrutura da tabela 'accounts'...")
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
        print("ℹ️ Sistema continuará funcionando, mas funcionalidades L2 não estarão disponíveis")
        
    finally:
        # Libera o lock se foi adquirido
        if lock_acquired and lock_file:
            try:
                release_lock(lock_file)
                lock_file.close()
                # Remove o arquivo de lock
                if lock_file_path.exists():
                    lock_file_path.unlink()
            except Exception:
                pass
