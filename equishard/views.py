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


def asset_detail(request, asset_id):
    """Asset detail page."""
    return render(request, 'asset_detail.html', {'asset_id': asset_id})
