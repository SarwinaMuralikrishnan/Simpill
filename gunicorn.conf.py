# Gunicorn production configuration file
import multiprocessing

# Bind to internal container port
bind = "0.0.0.0:5000"

# Adjust worker counts according to CPU cores
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2

# Worker type
worker_class = "gthread"

# Connection configurations
timeout = 120
keepalive = 5

# Logging setup
accesslog = "-"
errorlog = "-"
loglevel = "info"
