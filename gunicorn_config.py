"""
Configuration Gunicorn pour la production.
"""

import multiprocessing
import os

# Nombre de workers (2x CPU cores + 1)
workers = int(os.environ.get('GUNICORN_WORKERS', 2))

# Nombre de threads par worker
threads = int(os.environ.get('GUNICORN_THREADS', 2))

# Timeout
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))

# Bind (utilise PORT de Railway)
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker class
worker_class = "gthread"

# Preload app
preload_app = True

# Max requests (recycle workers after N requests)
max_requests = 1000
max_requests_jitter = 50

