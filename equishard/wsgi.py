Klaa"""
WSGI config for EquiShard project.

It exposes the WSGI callable as a module-level variable named ``application``.
Note: Use ASGI (asgi.py) for production to support FastAPI.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equishard.settings')

application = get_wsgi_application()
