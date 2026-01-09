"""
ASGI config for EquiShard project.

Mounts FastAPI (Query Layer) alongside Django (Command Layer).

Routes:
- /api/* -> FastAPI (Reads/Queries)
- Everything else -> Django (Writes/Commands)
"""

import os

from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equishard.settings')
django_asgi_app = get_asgi_application()

# Import FastAPI app after Django is initialized
from api.main import app as fastapi_app


async def application(scope: dict, receive, send) -> None:
    """
    ASGI application router.
    
    Routes requests based on path:
    - /api/* routes to FastAPI (Query Layer)
    - All other routes go to Django (Command Layer)
    """
    if scope['type'] == 'http':
        path = scope.get('path', '')
        
        if path.startswith('/api/'):
            await fastapi_app(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    else:
        # Websockets, lifespan, etc. go to Django
        await django_asgi_app(scope, receive, send)
