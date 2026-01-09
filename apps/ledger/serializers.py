"""Ledger app serializers."""

from rest_framework import serializers


class FaucetSerializer(serializers.Serializer):
    """Serializer for faucet request."""
    amount = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Faucet credit')


class BalanceSerializer(serializers.Serializer):
    """Serializer for balance response."""
    balance = serializers.DecimalField(max_digits=20, decimal_places=8)
    currency = serializers.CharField()
    user_id = serializers.IntegerField()


class TransactionLineSerializer(serializers.Serializer):
    """Serializer for transaction line history."""
    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=8)
    balance_snapshot = serializers.DecimalField(max_digits=20, decimal_places=8)
    memo = serializers.CharField()
    created_at = serializers.DateTimeField()
    
    journal_reference = serializers.CharField(source='journal_entry.reference')
    journal_description = serializers.CharField(source='journal_entry.description')
    journal_type = serializers.CharField(source='journal_entry.entry_type')
