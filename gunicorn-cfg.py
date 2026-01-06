# -*- encoding: utf-8 -*-
"""
Gunicorn Configuration File
"""

import multiprocessing
import os

# Bind the server to all interfaces on port 8000
bind = '0.0.0.0:5005'

# Number of worker processes
# Fórmula antiga: (2 x CPUs) + 1 causava muitas conexões no banco
# Nova fórmula recomendada: 2-4 workers é suficiente para maioria dos casos
# Use GUNICORN_WORKERS no .env para customizar
default_workers = min(4, (multiprocessing.cpu_count() * 2 + 1))
workers = int(os.getenv('GUNICORN_WORKERS', default_workers))

# Worker class (sync is the default, gevent or uvicorn can be used for async)
worker_class = 'sync'

# Access log file location (stdout by default)
accesslog = '-'

# Error log file location (stdout by default)
errorlog = '-'

# Log level (debug, info, warning, error, critical)
loglevel = 'info'

# Capture output from print statements and errors
capture_output = True

# Graceful timeout for worker processes (in seconds)
# Aumentado para 60s para operações de wallet que podem demorar mais
# (transferências para servidor do jogo podem levar tempo devido a queries no banco L2)
timeout = int(os.getenv('GUNICORN_TIMEOUT', 60))

# Max requests a worker will process before restarting (helps manage memory leaks)
max_requests = 1000
max_requests_jitter = 50
