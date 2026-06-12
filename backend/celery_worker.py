import sys
import os

# Add parent directory to path so python can import 'app' module
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.infrastructure.queue.celery_app import celery_app
