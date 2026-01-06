import os
import time
import threading
from typing import Any, Dict, Tuple, List, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine, Result
from urllib.parse import quote_plus

load_dotenv()

class LineageDB:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LineageDB, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.engine: Optional[Engine] = None
        self.cache: Dict[Tuple[str, Tuple[Any, ...]], Tuple[List[Dict], float]] = {}
        self.cache_ttl = 60  # segundos
        self.enabled = os.getenv("LINEAGE_DB_ENABLED", "false").lower() == "true"
        # Estado do healthcheck
        self._last_check_time: float = 0.0
        self._last_check_ok: bool = False
        self._check_cooldown_seconds: int = int(os.getenv("LINEAGE_DB_CHECK_COOLDOWN", "20"))
        self._ping_timeout_seconds: int = int(os.getenv("LINEAGE_DB_PING_TIMEOUT", "2"))
        
        # 🔥 NOVO: Controle de pool reset para evitar loop
        self._last_pool_reset_time: float = 0.0
        self._pool_reset_cooldown: int = int(os.getenv("LINEAGE_DB_POOL_RESET_COOLDOWN", "10"))  # 10 segundos entre resets
        self._consecutive_errors: int = 0
        self._max_consecutive_errors: int = int(os.getenv("LINEAGE_DB_MAX_CONSECUTIVE_ERRORS", "3"))
        self._error_window_start: float = 0.0
        self._error_window_duration: int = int(os.getenv("LINEAGE_DB_ERROR_WINDOW", "5"))  # 5 segundos
        
        if self.enabled:
            self._connect()
        else:
            print("ℹ️ Banco Lineage desativado via configuração")
            
        self._initialized = True

    def _connect(self):
        try:
            user = os.getenv("LINEAGE_DB_USER")
            password = os.getenv("LINEAGE_DB_PASSWORD")
            host = os.getenv("LINEAGE_DB_HOST")
            port = os.getenv("LINEAGE_DB_PORT", "3306")
            dbname = os.getenv("LINEAGE_DB_NAME")

            # 🔒 Codifica a senha pra evitar erro com caracteres especiais
            safe_password = quote_plus(password)

            url = f"mysql+pymysql://{user}:{safe_password}@{host}:{port}/{dbname}"

            # Timeouts para evitar travar o worker caso o DB esteja inacessível
            connect_timeout = int(os.getenv("LINEAGE_DB_CONNECT_TIMEOUT", "3"))
            read_timeout = int(os.getenv("LINEAGE_DB_READ_TIMEOUT", "3"))
            write_timeout = int(os.getenv("LINEAGE_DB_WRITE_TIMEOUT", "3"))
            pool_timeout = int(os.getenv("LINEAGE_DB_POOL_TIMEOUT", "3"))

            # Configuração de pool para evitar "Too many connections"
            # Com múltiplos workers do Gunicorn, cada um cria seu próprio pool
            pool_size = int(os.getenv("LINEAGE_DB_POOL_SIZE", "1"))
            max_overflow = int(os.getenv("LINEAGE_DB_MAX_OVERFLOW", "2"))
            
            self.engine = create_engine(
                url,
                echo=False,
                pool_pre_ping=True,              # Valida conexões antes de usar
                pool_recycle=180,                # Recicla conexões a cada 3 minutos
                pool_timeout=pool_timeout,       # Timeout ao aguardar conexão do pool
                pool_size=pool_size,             # Limite de conexões permanentes no pool
                max_overflow=max_overflow,       # Conexões extras permitidas além do pool_size
                pool_use_lifo=True,              # LIFO: usa conexões mais recentes primeiro
                connect_args={
                    "connect_timeout": connect_timeout,
                    "read_timeout": read_timeout,
                    "write_timeout": write_timeout,
                    # Timeout mais agressivo para ping (evita travar worker)
                    "init_command": "SET SESSION wait_timeout=60, interactive_timeout=60",
                    # Timeout para operações de leitura/escrita (evita travar)
                    "autocommit": False,
                },
            )

            pid = os.getpid()
            print(f"✅ Worker PID {pid} conectado ao {dbname} | Pool: {pool_size} + {max_overflow} overflow = {pool_size + max_overflow} conexões max")

        except Exception as e:
            print(f"❌ Falha ao conectar ao banco Lineage: {e}")
            self.engine = None

    def _normalize_params(self, query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        new_params = {}
        for key, val in params.items():
            if isinstance(val, list):
                placeholders = []
                for i, item in enumerate(val):
                    new_key = f"{key}_{i}"
                    placeholders.append(f":{new_key}")
                    new_params[new_key] = item
                query = query.replace(f":{key}", f"({', '.join(placeholders)})")
            else:
                new_params[key] = val
        return query, new_params

    def _get_cache(self, query: str, params: Tuple) -> Optional[List[Dict]]:
        key = (query, params)
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                print("⚡ Consulta retornada do cache")
                return data
            else:
                del self.cache[key]
        return None

    def _set_cache(self, query: str, params: Tuple, data: List[Dict]):
        self.cache[(query, params)] = (data, time.time())

    def _safe_execute_read(self, query: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Executa query de leitura e retorna os dados já processados.
        🔥 IMPORTANTE: Processa tudo DENTRO do 'with' para evitar vazamento de conexões.
        """
        if not self.enabled:
            return None
        if not self.engine:
            print("⚠️ Sem conexão com o banco")
            return None
        try:
            query, normalized_params = self._normalize_params(query, params)
            with self.engine.connect() as conn:
                stmt = text(query)
                result = conn.execute(stmt, normalized_params)
                # 🔥 PROCESSA TUDO AQUI DENTRO DO 'with' para liberar a conexão
                rows = result.mappings().all()
                result.close()  # Fecha o result explicitamente
                # 🎯 Resetar contador de erros em sucesso
                self._consecutive_errors = 0
                return rows
        except SQLAlchemyError as e:
            error_msg = str(e)
            # Se for erro de "too many connections", usar lógica inteligente de reset
            if "1040" in error_msg or "Too many connections" in error_msg:
                self._handle_connection_overload()
            else:
                print(f"❌ Erro SQL: {e}")
            return None
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return None

    def _safe_execute_write(self, query: str, params: Dict[str, Any]) -> Optional[int]:
        """
        Executa query de escrita e retorna o rowcount/lastrowid.
        🔥 IMPORTANTE: Processa tudo DENTRO do 'with' para evitar vazamento de conexões.
        """
        if not self.enabled:
            return None
        if not self.engine:
            print("⚠️ Sem conexão com o banco")
            return None
        try:
            query, normalized_params = self._normalize_params(query, params)
            with self.engine.begin() as conn:
                stmt = text(query)
                result = conn.execute(stmt, normalized_params)
                # 🔥 EXTRAI OS DADOS AQUI DENTRO DO 'with' para liberar a conexão
                rowcount = result.rowcount
                result.close()  # Fecha o result explicitamente
                # 🎯 Resetar contador de erros em sucesso
                self._consecutive_errors = 0
                return rowcount
        except SQLAlchemyError as e:
            error_msg = str(e)
            # Se for erro de "too many connections", usar lógica inteligente de reset
            if "1040" in error_msg or "Too many connections" in error_msg:
                self._handle_connection_overload()
            else:
                print(f"❌ Erro SQL: {e}")
            return None
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return None

    def is_connected(self) -> bool:
        if not self.enabled:
            return False
        if not self.engine:
            return False
        # Respeita cooldown quando último resultado foi negativo
        now = time.time()
        if not self._last_check_ok and (now - self._last_check_time) < self._check_cooldown_seconds:
            return False

        result_container = {"ok": False}
        done = threading.Event()

        def ping_db():
            try:
                # Usa timeout mais agressivo na conexão
                with self.engine.connect() as conn:
                    # Query simples com timeout implícito via connect_args
                    conn.execute(text("SELECT 1"))
                result_container["ok"] = True
            except Exception as e:
                error_msg = str(e)
                if "1040" not in error_msg and "Too many connections" not in error_msg:
                    # Só mostra erro se não for "too many connections" (já tratado em outro lugar)
                    if "timeout" not in error_msg.lower() and "timed out" not in error_msg.lower():
                        print(f"⚠️ Falha no healthcheck: {e}")
            finally:
                done.set()

        t = threading.Thread(target=ping_db, daemon=True)
        t.start()
        finished = done.wait(timeout=self._ping_timeout_seconds)

        if not finished:
            # Falha por timeout; descarta conexões do pool para evitar estados zumbis
            print(f"⏱️ Healthcheck timeout após {self._ping_timeout_seconds}s - descartando pool")
            try:
                if self.engine:
                    self.engine.dispose()
            except Exception:
                pass
            self._last_check_ok = False
            self._last_check_time = now
            return False

        self._last_check_ok = result_container["ok"]
        self._last_check_time = now
        return self._last_check_ok

    def select(self, query: str, params: Dict[str, Any] = {}, use_cache: bool = False) -> Optional[List[Dict]]:
        if not self.enabled:
            return []
        params = params or {}
        query_exp, params_exp = self._normalize_params(query, params)
        param_tuple = tuple(sorted(params_exp.items()))
        if use_cache:
            cached = self._get_cache(query_exp, param_tuple)
            if cached is not None:
                return cached

        # 🔥 Agora _safe_execute_read já retorna os rows processados
        rows = self._safe_execute_read(query, params)
        if rows is None:
            return []

        if use_cache:
            self._set_cache(query_exp, param_tuple, rows)
        return rows

    def insert(self, query: str, params: Dict[str, Any] = {}) -> Optional[int]:
        if not self.enabled:
            return None
        return self._safe_execute_insert(query, params)

    def update(self, query: str, params: Dict[str, Any] = {}) -> Optional[int]:
        if not self.enabled:
            return None
        return self._safe_execute_write(query, params)

    def delete(self, query: str, params: Dict[str, Any] = {}) -> Optional[int]:
        if not self.enabled:
            return None
        return self._safe_execute_write(query, params)

    def _safe_execute_insert(self, query: str, params: Dict[str, Any]) -> Optional[int]:
        """
        Executa query INSERT e retorna o lastrowid.
        🔥 IMPORTANTE: Processa tudo DENTRO do 'with' para evitar vazamento de conexões.
        """
        if not self.enabled:
            return None
        if not self.engine:
            print("⚠️ Sem conexão com o banco")
            return None
        try:
            query, normalized_params = self._normalize_params(query, params)
            # Usa timeout mais agressivo via connect_args (já configurado)
            # Se a conexão travar, o pool_pre_ping deve detectar e descartar
            with self.engine.begin() as conn:
                stmt = text(query)
                result = conn.execute(stmt, normalized_params)
                # 🔥 EXTRAI O LASTROWID AQUI DENTRO DO 'with' para liberar a conexão
                lastrowid = result.lastrowid
                result.close()  # Fecha o result explicitamente
                # 🎯 Resetar contador de erros em sucesso
                self._consecutive_errors = 0
                return lastrowid
        except SQLAlchemyError as e:
            error_msg = str(e)
            # Se for erro de "too many connections", usar lógica inteligente de reset
            if "1040" in error_msg or "Too many connections" in error_msg:
                self._handle_connection_overload()
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                print(f"⏱️ Timeout na operação INSERT: {e}")
                # Descarta conexões do pool para evitar estados zumbis
                try:
                    if self.engine:
                        self.engine.dispose()
                except Exception:
                    pass
            else:
                print(f"❌ Erro SQL: {e}")
            return None
        except Exception as e:
            error_msg = str(e).lower()
            # Detecta timeouts genéricos
            if "timeout" in error_msg or "timed out" in error_msg or "connection" in error_msg:
                print(f"⏱️ Timeout/Erro de conexão na operação INSERT: {e}")
                # Descarta conexões do pool para evitar estados zumbis
                try:
                    if self.engine:
                        self.engine.dispose()
                except Exception:
                    pass
            else:
                print(f"❌ Erro inesperado: {e}")
            return None

    def execute_raw(self, query: str, params: Dict[str, Any] = {}) -> bool:
        if not self.enabled:
            return False
        return self._safe_execute_write(query, params) is not None
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Retorna uma lista com os nomes das colunas da tabela.
        🔥 IMPORTANTE: Processa tudo DENTRO do 'with' para evitar vazamento de conexões.
        """
        if not self.enabled:
            return []
        if not self.engine:
            print("⚠️ Sem conexão com o banco")
            return []
        try:
            query = f"SHOW COLUMNS FROM `{table_name}`"
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                # 🔥 PROCESSA TUDO AQUI DENTRO DO 'with' para liberar a conexão
                columns = [row[0] for row in result.fetchall()]
                result.close()  # Fecha o result explicitamente
                return columns
        except SQLAlchemyError as e:
            error_msg = str(e)
            if "1040" in error_msg or "Too many connections" in error_msg:
                print(f"⚠️ Não foi possível verificar colunas da tabela '{table_name}' - MySQL sobrecarga")
                self._handle_connection_overload()
            else:
                print(f"❌ Erro ao buscar colunas da tabela '{table_name}': {e}")
            return []
        except Exception as e:
            print(f"❌ Erro inesperado ao buscar colunas '{table_name}': {e}")
            return []

    def clear_cache(self):
        self.cache.clear()
    
    def _handle_connection_overload(self):
        """
        Trata sobrecarga de conexões de forma inteligente, evitando loop de reset.
        Usa janela de tempo e cooldown para não resetar o pool repetidamente.
        """
        now = time.time()
        
        # Incrementar contador de erros consecutivos
        if now - self._error_window_start > self._error_window_duration:
            # Nova janela de erros
            self._error_window_start = now
            self._consecutive_errors = 1
        else:
            self._consecutive_errors += 1
        
        # Se está no cooldown, NÃO resetar o pool
        if now - self._last_pool_reset_time < self._pool_reset_cooldown:
            time_remaining = int(self._pool_reset_cooldown - (now - self._last_pool_reset_time))
            print(f"⏳ MySQL sobrecarga detectada [{self._consecutive_errors}x] - aguardando {time_remaining}s antes de resetar pool")
            return
        
        # Se ultrapassou o limite de erros consecutivos, resetar pool
        if self._consecutive_errors >= self._max_consecutive_errors:
            try:
                if self.engine:
                    self.engine.dispose()
                    self._last_pool_reset_time = now
                    print(f"♻️ Pool resetado após {self._consecutive_errors} erros consecutivos - próxima query criará novas conexões")
                    self._consecutive_errors = 0
            except Exception as e:
                print(f"❌ Falha ao resetar pool: {e}")
        else:
            print(f"⚠️ MySQL sobrecarga [{self._consecutive_errors}/{self._max_consecutive_errors}] - aguardando mais erros antes de resetar")
    
    def dispose_connections(self):
        """
        Descarta todas as conexões do pool.
        Útil quando há erros de "too many connections" ou conexões travadas.
        
        ⚠️ DEPRECATED: Use _handle_connection_overload() ao invés deste método
        para evitar loops de reset.
        """
        if self.engine:
            try:
                self.engine.dispose()
                self._last_pool_reset_time = time.time()
                print("♻️ Pool resetado manualmente - próxima query criará novas conexões")
            except Exception as e:
                print(f"❌ Falha ao resetar pool: {e}")
