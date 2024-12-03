import multiprocessing
import os 
bind = os.environ.get("GUNICORN_BIND",default="0.0.0.0:8000")
workers = multiprocessing.cpu_count() * 2 + 1
threads = int(os.environ.get("GUNICORN_THREADS",default=2))  # Number of worker threads per worker process
# worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT",default=120))
accesslog = os.environ.get("GUNICORN_ACCESS_LOGFILE",default="-")
errorlog  = os.environ.get("GUNICORN_ERROR_LOGFILE",default="-" )
