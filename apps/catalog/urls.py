"""Catalog app URL configuration."""

from django.urls import path

from apps.catalog.views import InvestView, DivestView


urlpatterns = [
    path('invest/', InvestView.as_view(), name='invest'),
    path('divest/', DivestView.as_view(), name='divest'),
]
