# Correção: "Too many connections" MySQL

## 🔴 Problema Identificado

Seu servidor estava apresentando o erro `(pymysql.err.OperationalError) (1040, 'Too many connections')` devido a:

1. **4 workers do Gunicorn** executando simultaneamente
2. Cada worker criando um **pool de 5 conexões** (2 permanentes + 3 overflow)
3. **Total potencial: 20 conexões** sendo abertas
4. Conexões não sendo liberadas corretamente em casos de erro
5. Método `get_table_columns()` sendo chamado por todos os workers ao mesmo tempo no startup

## ✅ Correções Aplicadas

### 1. Redução do Pool de Conexões

**Antes:**
```python
pool_size = 2
max_overflow = 3
# Total: 5 conexões por worker × 4 workers = 20 conexões
```

**Depois:**
```python
pool_size = 1
max_overflow = 2
# Total: 3 conexões por worker × 4 workers = 12 conexões
```

### 2. Melhor Gerenciamento de Conexões

#### Adicionado `pool_use_lifo=True`
- Usa conexões mais recentes primeiro (LIFO - Last In First Out)
- Mantém conexões mais "quentes" e válidas
- Permite que conexões antigas sejam recicladas naturalmente

#### Tratamento de Erro "Too many connections"
```python
if "1040" in error_msg or "Too many connections" in error_msg:
    print("⚠️ Detectado 'Too many connections' - descartando pool")
    self.dispose_connections()
```

### 3. Fechamento Explícito de Resultados

No método `get_table_columns()`:
```python
result = conn.execute(text(query))
columns = [row[0] for row in result.fetchall()]
result.close()  # ⬅️ Libera conexão mais rápido
return columns
```

### 4. Novo Método para Descartar Pool

```python
def dispose_connections(self):
    """
    Descarta todas as conexões do pool.
    Útil quando há erros de "too many connections".
    """
    if self.engine:
        self.engine.dispose()
```

### 5. Melhor Tratamento de Exceções

Adicionado tratamento para exceções genéricas além de `SQLAlchemyError`:
- Previne crashes silenciosos
- Garante que conexões sejam liberadas mesmo em erros inesperados

## 📊 Comparação: Antes vs Depois

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Conexões por worker | 5 | 3 | -40% |
| Total de conexões (4 workers) | 20 | 12 | -40% |
| Gestão de erros | Básica | Avançada | ✅ |
| Auto-recuperação | ❌ | ✅ | ✅ |
| Liberação de conexões | Implícita | Explícita | ✅ |

## 🚀 Como Aplicar em Produção

### Opção 1: Atualizar e Reiniciar (RECOMENDADO)

1. **Faça backup do código atual:**
```bash
cd /var/pdl/lineage
git add .
git commit -m "backup antes de fix too many connections"
```

2. **Atualize os arquivos:**
```bash
# Pull das alterações ou copie os arquivos manualmente
```

3. **Atualize o arquivo `.env` (se necessário):**
```bash
nano .env
```

Certifique-se de ter:
```bash
LINEAGE_DB_POOL_SIZE=1
LINEAGE_DB_MAX_OVERFLOW=2
```

4. **Reconstrua e reinicie o container:**
```bash
docker-compose down
docker-compose build site_http
docker-compose up -d
```

5. **Monitore os logs:**
```bash
docker logs -f site_http
```

Você deve ver:
- ✅ Conectado ao banco Lineage com SQLAlchemy (4 vezes, uma por worker)
- ❌ Não deve mais aparecer "Too many connections"

### Opção 2: Hot Fix (Sem Rebuild)

Se não puder fazer rebuild agora, ajuste temporariamente no `.env`:

```bash
# Reduza para 2 workers temporariamente
GUNICORN_WORKERS=2
```

```bash
docker-compose restart site_http
```

Isso reduzirá o número de conexões para:
- 2 workers × 5 conexões = 10 conexões (com configuração antiga)

## 🔍 Como Monitorar

### 1. Ver conexões ativas no MySQL

Conecte ao MySQL e execute:

```sql
-- Total de conexões ativas
SHOW STATUS LIKE 'Threads_connected';

-- Limite máximo de conexões
SHOW VARIABLES LIKE 'max_connections';

-- Conexões por usuário
SELECT user, host, db, command, time, state
FROM information_schema.processlist
WHERE user = 'seu_usuario_lineage'
ORDER BY time DESC;
```

### 2. Ver logs do container

```bash
# Logs em tempo real
docker logs -f site_http

# Últimas 100 linhas
docker logs --tail 100 site_http

# Buscar erros específicos
docker logs site_http 2>&1 | grep -i "too many connections"
```

### 3. Ver workers ativos

```bash
# Dentro do container
docker exec -it site_http ps aux | grep gunicorn

# Contar workers
docker exec -it site_http ps aux | grep "gunicorn" | grep -v grep | wc -l
```

## 🎯 Configurações Recomendadas por Tamanho de Servidor

| Servidor | RAM | CPUs | Workers | Pool Size | Max Overflow | Total Conexões |
|----------|-----|------|---------|-----------|--------------|----------------|
| Pequeno  | 2GB | 2    | 2       | 1         | 2            | 6              |
| Médio    | 4GB | 4    | 4       | 1         | 2            | 12             |
| Grande   | 8GB | 8    | 6       | 1         | 2            | 18             |

**Seu caso atual:** Médio (4 workers × 3 conexões = 12 conexões)

## ⚠️ Se o Problema Persistir

### 1. Verifique o limite de conexões do MySQL

```sql
SHOW VARIABLES LIKE 'max_connections';
```

Se for muito baixo (ex: 50), aumente:

```sql
SET GLOBAL max_connections = 200;
```

Ou no arquivo de configuração do MySQL (`my.cnf`):
```ini
[mysqld]
max_connections = 200
```

### 2. Verifique outras aplicações conectadas

Outros servidores ou aplicações podem estar consumindo conexões:

```sql
SELECT 
    user, 
    host, 
    COUNT(*) as conexoes
FROM information_schema.processlist
GROUP BY user, host
ORDER BY conexoes DESC;
```

### 3. Considere usar ProxySQL

Para servidores muito grandes ou com múltiplas aplicações, use ProxySQL:

```yaml
# docker-compose.yml
services:
  proxysql:
    image: proxysql/proxysql:latest
    ports:
      - "6033:6033"
    volumes:
      - ./proxysql.cnf:/etc/proxysql.cnf
```

Veja mais em: [docs/DATABASE_CONNECTION_POOLING.md](./DATABASE_CONNECTION_POOLING.md)

## 📝 Arquivos Modificados

1. ✅ `apps/lineage/server/database.py` - Lógica de conexão
2. ✅ `env.sample` - Valores padrão
3. ✅ `docs/DATABASE_CONNECTION_POOLING.md` - Documentação atualizada
4. ✅ `docs/FIX_TOO_MANY_CONNECTIONS.md` - Este arquivo

## 🧪 Teste de Validação

Execute este teste para verificar se está funcionando:

```bash
# Entre no container
docker exec -it site_http bash

# Execute o Python
python3 << 'EOF'
from apps.lineage.server.database import LineageDB
import time

db = LineageDB()

# Tenta fazer 10 consultas simultâneas
for i in range(10):
    result = db.select("SELECT 1 as test")
    print(f"Query {i+1}: {'✅' if result else '❌'}")
    time.sleep(0.1)

print("\n✅ Teste completo! Se não houver erros, está funcionando.")
EOF
```

## 📞 Suporte

Se precisar de ajuda adicional:
1. Verifique os logs: `docker logs site_http 2>&1 | grep -i error`
2. Revise a configuração do `.env`
3. Consulte a documentação completa: [DATABASE_CONNECTION_POOLING.md](./DATABASE_CONNECTION_POOLING.md)

