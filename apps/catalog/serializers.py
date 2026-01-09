"""Catalog app serializers."""

from rest_framework import serializers


class InvestSerializer(serializers.Serializer):
    """Serializer for investment request."""
    asset_id = serializers.IntegerField()
    shares = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=0.00000001)


class DivestSerializer(serializers.Serializer):
    """Serializer for divestment request."""
    asset_id = serializers.IntegerField()
    shares = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=0.00000001)
