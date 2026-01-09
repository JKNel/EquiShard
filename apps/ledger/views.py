"""Ledger app views (Command endpoints)."""

from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ledger.serializers import (
    FaucetSerializer,
    BalanceSerializer,
    TransactionLineSerializer,
)
from apps.ledger.services import LedgerService, LedgerError


class FaucetView(APIView):
    """Add funds to user's wallet (demo/testing endpoint)."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = FaucetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            entry = LedgerService.faucet(
                user=request.user,
                amount=Decimal(str(serializer.validated_data['amount'])),
                description=serializer.validated_data.get('description', 'Faucet credit')
            )

            new_balance = LedgerService.get_balance(request.user)

            return Response({
                'success': True,
                'reference': entry.reference,
                'amount': str(serializer.validated_data['amount']),
                'new_balance': str(new_balance),
            }, status=status.HTTP_201_CREATED)

        except LedgerError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BalanceView(APIView):
    """Get user's current wallet balance."""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        balance = LedgerService.get_balance(request.user)
        return Response(BalanceSerializer({
            'balance': balance,
            'currency': 'USD',
            'user_id': request.user.id
        }).data)


class TransactionHistoryView(APIView):
    """Get user's transaction history."""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        limit = int(request.query_params.get('limit', 50))
        transactions = LedgerService.get_transaction_history(
            request.user,
            limit=min(limit, 100)
        )
        return Response(TransactionLineSerializer(transactions, many=True).data)
