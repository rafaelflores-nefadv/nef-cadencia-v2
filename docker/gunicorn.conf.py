# ==============================================================================
# Gunicorn Configuration for NEF Cadência
# ==============================================================================
# Documentation: https://docs.gunicorn.org/en/stable/settings.html
# ==============================================================================

import multiprocessing
import os

# ------------------------------------------------------------------------------
# Server Socket
# ------------------------------------------------------------------------------
bind = "0.0.0.0:8000"
backlog = 2048

# ------------------------------------------------------------------------------
# Worker Processes
# ------------------------------------------------------------------------------
# Formula: (2 x $num_cores) + 1
# For 2 cores: (2 x 2) + 1 = 5 workers
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class
worker_class = "sync"  # Options: sync, gevent, eventlet, tornado

# Worker connections (for async workers)
worker_connections = 1000

# Maximum requests per worker (prevents memory leaks)
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Worker timeout (seconds)
timeout = int(os.getenv("GUNICORN_TIMEOUT", 30))

# Graceful timeout (seconds)
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))

# Keep alive (seconds)
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 2))

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
# Access log
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "/app/logs/gunicorn-access.log")

# Error log
errorlog = os.getenv("GUNICORN_ERROR_LOG", "/app/logs/gunicorn-error.log")

# Log level
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")  # debug, info, warning, error, critical

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Disable access log to stdout (already logging to file)
# Set to "-" to enable stdout logging
# accesslog = "-"

# ------------------------------------------------------------------------------
# Process Naming
# ------------------------------------------------------------------------------
proc_name = "nef-cadencia"

# ------------------------------------------------------------------------------
# Server Mechanics
# ------------------------------------------------------------------------------
# Daemon mode (run in background)
daemon = False

# PID file
pidfile = None

# User and group (if running as root)
user = None
group = None

# Temporary directory
tmp_upload_dir = None

# ------------------------------------------------------------------------------
# Security
# ------------------------------------------------------------------------------
# Limit request line size (prevents large header attacks)
limit_request_line = 4096

# Limit request header field size
limit_request_fields = 100
limit_request_field_size = 8190

# ------------------------------------------------------------------------------
# Server Hooks
# ------------------------------------------------------------------------------
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Gunicorn server")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Gunicorn server")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn server is ready. Spawning workers")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # Log slow requests
    worker.log.debug(f"{req.method} {req.path}")


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass


def child_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    server.log.info(f"Worker exited (pid: {worker.pid})")


def worker_exit(server, worker):
    """Called just after a worker has been exited, in the worker process."""
    pass


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Gunicorn server")

# ------------------------------------------------------------------------------
# SSL (if needed)
# ------------------------------------------------------------------------------
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = 2  # TLS
# cert_reqs = 0  # ssl.CERT_NONE
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = None

# ------------------------------------------------------------------------------
# Development Settings (Override in development)
# ------------------------------------------------------------------------------
if os.getenv("DJANGO_ENV") == "development":
    # Reload on code changes (development only)
    reload = True
    reload_extra_files = []
    
    # Reduce workers in development
    workers = 2
    
    # Enable access log to stdout
    accesslog = "-"
    errorlog = "-"
