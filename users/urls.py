from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, DocumentUploadView, LogoutView, UserViewSet

router = DefaultRouter()
# Volvemos a poner 'users' aquí para que el router cree la ruta /users/
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('users/<int:pk>/upload-document/', DocumentUploadView.as_view()),
    # Endpoints del Router
    path('', include(router.urls)),
]