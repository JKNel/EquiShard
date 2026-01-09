"""Ledger app URL configuration."""

from django.urls import path

from apps.ledger.views import FaucetView, BalanceView, TransactionHistoryView


urlpatterns = [
    path('ledger/faucet/', FaucetView.as_view(), name='faucet'),
    path('ledger/balance/', BalanceView.as_view(), name='balance'),
    path('ledger/transactions/', TransactionHistoryView.as_view(), name='transactions'),
]
