"""Users app serializers."""

from rest_framework import serializers

from apps.users.models import User


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_slug = serializers.SlugField()
    first_name = serializers.CharField(max_length=150, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')
    risk_tolerance = serializers.IntegerField(min_value=1, max_value=5, default=3)
    is_accredited = serializers.BooleanField(default=False)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'risk_tolerance', 'is_accredited', 'tenant_name', 'tenant_slug',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class RiskProfileSerializer(serializers.Serializer):
    """Serializer for updating risk profile."""
    risk_tolerance = serializers.IntegerField(min_value=1, max_value=5, required=False)
    is_accredited = serializers.BooleanField(required=False)


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom auth serializer adding user flags."""
    def validate(self, attrs):
        data = super().validate(attrs)
        data['is_staff'] = self.user.is_staff
        data['is_superuser'] = self.user.is_superuser
        data['username'] = self.user.username
        return data
