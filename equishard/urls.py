"""
URL configuration for EquiShard project (Command Layer).

The Query Layer (FastAPI) is mounted via ASGI at /api/*.
These URLs handle Django admin and REST endpoints for Commands.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from equishard.views import home, marketplace, dashboard, asset_detail
from apps.users.views import CustomTokenObtainPairView


def health_check(request) -> JsonResponse:
    """Health check endpoint for container orchestration."""
    return JsonResponse({'status': 'healthy', 'service': 'equishard'})


urlpatterns = [
    # Frontend pages
    path('', home, name='home'),
    path('marketplace/', marketplace, name='marketplace'),
    path('dashboard/', dashboard, name='dashboard'),
    path('asset/<int:asset_id>/', asset_detail, name='asset_detail'),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # JWT Authentication (Command layer auth)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Command endpoints (Django REST Framework)
    path('commands/', include('apps.users.urls')),
    path('commands/', include('apps.ledger.urls')),
    path('commands/', include('apps.catalog.urls')),
]

