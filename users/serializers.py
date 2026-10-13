# serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name_paternal', 'last_name_maternal', 
            'full_name', 'phone', 'street', 'neighborhood', 'municipality', 'state',
            'nexen_user', 'role_primary', 'role_secondary', 'rank', 'zone_or_team',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # Oipuru CustomUserManager omohenda hag̃ua la contraseña cifrada
        password = validated_data.pop('password', None)
        user = CustomUser.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': self.user.full_name,
            'role_primary': self.user.role_primary,
            'role_secondary': self.user.role_secondary,
            'rank': self.user.rank,
            'nexen_user': self.user.nexen_user,
            'zone_or_team': self.user.zone_or_team,
        }

        return data