# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para usar el correo electrónico como identificador único.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El correo electrónico es obligatorio.'))
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role_primary', CustomUser.Role.DIRECTORA)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('El superusuario debe tener is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        DIRECTORA = 'DIRECTORA', _('Directora General')
        GERENTE = 'GERENTE', _('Gerente de Zona')
        COORDINADORA = 'COORDINADORA', _('Coordinadora de Equipo')
        VENDEDORA = 'VENDEDORA', _('Vendedora / Consultora')

    username = None
    email = models.EmailField(_('Correo Electrónico'), unique=True)
    phone = models.CharField(_('Teléfono / WhatsApp'), max_length=20, blank=True, null=True)

    first_name = models.CharField(_('Nombre(s)'), max_length=150)
    last_name = models.CharField(_('Apellidos'), max_length=150)

    # Estructura Jerárquica y Soporte de Rol Doble
    role_primary = models.CharField(
        _('Rol Principal'),
        max_length=20,
        choices=Role.choices,
        default=Role.VENDEDORA
    )
    role_secondary = models.CharField(
        _('Rol Secundario'),
        max_length=20,
        choices=Role.choices,
        blank=True,
        null=True,
        help_text=_('Utilizado para vendedoras con rol doble (ej. Coordinadora + Vendedora)')
    )

    zone_or_team = models.CharField(
        _('Zona / Equipo'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Ej. Zona Norte, Equipo Alpha, Centro')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios de la Red')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_primary_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()