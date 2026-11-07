from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
import os
from supabase import create_client

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
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist() # Invalida el token en la base de datos
            return Response({"detail": "Sesión cerrada exitosamente."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
        

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan las credenciales de SupABASE en las variables de entorno de Railway.")

# Instancia oficial y limpia
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)


class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_obj = request.FILES.get('file')
        doc_type = request.data.get('doc_type') # 'ine' o 'address'

        if not file_obj or not doc_type:
            return Response({"error": "Faltan datos o archivo"}, status=400)

        # Ruta limpia en el bucket privado
        file_path = f"vendedoras/user_{pk}/{doc_type}_{file_obj.name}"

        try:
            # Usamos supabase_client (la instancia validada)
            supabase_client.storage.from_("expedientes-privados").upload(
                path=file_path,
                file=file_obj.read(),
                file_options={"content-type": file_obj.content_type}
            )

            # Obtener URL firmada temporal para visualizarlo de forma segura (válida por 1 hora)
            signed_url_res = supabase_client.storage.from_("expedientes-privados").create_signed_url(file_path, 3600)
            file_url = signed_url_res.get('signedUrl')

            return Response({"message": "Subido con éxito", "url": file_url}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)