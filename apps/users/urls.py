"""Users app URL configuration."""

from django.urls import path

from apps.users.views import (
    RegisterView,
    UserProfileView,
    UserProfileView,
    UpdateRiskProfileView,
    LeaderboardView,
)


urlpatterns = [
    path('users/register/', RegisterView.as_view(), name='user_register'),
    path('users/profile/', UserProfileView.as_view(), name='user_profile'),
    path('users/risk-profile/', UpdateRiskProfileView.as_view(), name='update_risk_profile'),
    path('users/leaderboard/', LeaderboardView.as_view(), name='api_leaderboard'),
]
