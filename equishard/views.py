"""
Frontend Views for EquiShard

Server-side rendered pages using Django templates with Bootstrap.
"""

from django.shortcuts import render
from django.http import JsonResponse


def home(request):
    """Landing page."""
    return render(request, 'home.html')


def marketplace(request):
    """Asset marketplace page."""
    return render(request, 'marketplace.html')


def dashboard(request):
    """User dashboard page."""
    return render(request, 'dashboard.html')


from django.conf import settings

def asset_detail(request, asset_id):
    """Asset detail page."""
    update_interval = settings.ASSET_UPDATE_INTERVAL
    context = {
        'asset_id': asset_id,
        'asset_update_interval': update_interval,
        'update_interval_minutes': round(update_interval / 60, 1) if update_interval % 60 != 0 else int(update_interval / 60)
    }
    return render(request, 'asset_detail.html', context)
