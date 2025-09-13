import os
from celery import Celery

# Default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "supermarket.settings")

app = Celery("supermarket")

# Load config from Django settings with CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each app (e.g., payment/tasks.py)
app.autodiscover_tasks()

