"""Catalog app views (Command endpoints)."""

from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Asset
from apps.catalog.serializers import InvestSerializer, DivestSerializer
from apps.catalog.services import (
    InvestService,
    CatalogError,
    InsufficientSharesError,
    PolicyViolationError,
)
from apps.ledger.services import InsufficientFundsError


class InvestView(APIView):
    """Execute an investment transaction."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = InvestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get asset
        try:
            asset = Asset.objects.get(
                id=serializer.validated_data['asset_id'],
                tenant=request.user.tenant,
                is_active=True
            )
        except Asset.DoesNotExist:
            return Response(
                {'error': 'Asset not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Execute investment
        invest_service = InvestService()
        
        try:
            result = invest_service.invest(
                user=request.user,
                asset=asset,
                shares=Decimal(str(serializer.validated_data['shares']))
            )
            return Response(result, status=status.HTTP_201_CREATED)

        except PolicyViolationError as e:
            return Response(
                {'error': str(e), 'code': 'POLICY_VIOLATION'},
                status=status.HTTP_403_FORBIDDEN
            )
        except InsufficientFundsError as e:
            return Response(
                {'error': str(e), 'code': 'INSUFFICIENT_FUNDS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except InsufficientSharesError as e:
            return Response(
                {'error': str(e), 'code': 'INSUFFICIENT_SHARES'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CatalogError as e:
            return Response(
                {'error': str(e), 'code': 'CATALOG_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DivestView(APIView):
    """Execute a divestment transaction."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = DivestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get asset
        try:
            asset = Asset.objects.get(
                id=serializer.validated_data['asset_id'],
                tenant=request.user.tenant,
                is_active=True
            )
        except Asset.DoesNotExist:
            return Response(
                {'error': 'Asset not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Execute divestment
        try:
            result = InvestService().sell(
                user=request.user,
                asset=asset,
                shares=Decimal(str(serializer.validated_data['shares']))
            )
            return Response(result, status=status.HTTP_200_OK)

        except InsufficientSharesError as e:
            return Response(
                {'error': str(e), 'code': 'INSUFFICIENT_SHARES'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CatalogError as e:
            return Response(
                {'error': str(e), 'code': 'CATALOG_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )
