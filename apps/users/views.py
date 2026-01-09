"""Users app views (Command endpoints)."""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import Tenant
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    RiskProfileSerializer,
)
from apps.users.services import UserService


class RegisterView(APIView):
    """User registration endpoint."""
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or validate tenant
        tenant_slug = serializer.validated_data.pop('tenant_slug')
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Invalid tenant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = UserService.create_user(
            tenant=tenant,
            **serializer.validated_data
        )
        
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class UserProfileView(APIView):
    """Get current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserProfileSerializer(request.user).data)


class UpdateRiskProfileView(APIView):
    """Update user's risk profile (ABAC attributes)."""
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = RiskProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = UserService.update_risk_profile(
            request.user,
            **serializer.validated_data
        )
        
        return Response(UserProfileSerializer(user).data)


from rest_framework_simplejwt.views import TokenObtainPairView
from apps.users.serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom auth view returning user flags."""
    serializer_class = CustomTokenObtainPairSerializer
