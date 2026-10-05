from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .serializers import CustomUserSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para administrar la Red de Vendedoras.
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        zone = self.request.query_params.get('zone')

        if role:
            queryset = queryset.filter(role_primary=role)
        if zone:
            queryset = queryset.filter(zone_or_team__icontains=zone)

        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Retorna la información de la usuaria que ha iniciado sesión (/api/users/me/).
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)