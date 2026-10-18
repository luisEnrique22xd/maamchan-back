# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
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

    class Rank(models.TextChoices):
        BRILLANTE = 'BRILLANTE', _('Brillante')
        ZAFIRO = 'ZAFIRO', _('Zafiro')
        ORO = 'ORO', _('Oro')
        PLATINO = 'PLATINO', _('Platino')

    username = None
    email = models.EmailField(_('Correo Electrónico'), unique=True)
    phone = models.CharField(_('Teléfono / WhatsApp'), max_length=20, blank=True, null=True)

    # Datos Personales
    first_name = models.CharField(_('Nombre(s)'), max_length=150)
    last_name_paternal = models.CharField(_('Apellido Paterno'), max_length=150, null=True, blank=True)
    last_name_maternal = models.CharField(_('Apellido Materno'), max_length=150, blank=True, null=True)

    # Dirección
    street = models.CharField(_('Calle y Número'), max_length=255, blank=True, null=True)
    neighborhood = models.CharField(_('Colonia / Localidad'), max_length=150, blank=True, null=True)
    municipality = models.CharField(_('Municipio / Alcaldía'), max_length=150, blank=True, null=True)
    state = models.CharField(_('Estado'), max_length=150, blank=True, null=True)

    # Identificador Nexen
    nexen_user = models.CharField(_('Usuario Nexen'), max_length=100, unique=True, blank=True, null=True)

    # Jerarquía ha Clasificación
    role_primary = models.CharField(
        _('Rol Principal / Nivel'),
        max_length=20,
        choices=Role.choices,
        default=Role.VENDEDORA
    )
    role_secondary = models.CharField(
        _('Rol Secundario'),
        max_length=20,
        choices=Role.choices,
        blank=True,
        null=True
    )
    rank = models.CharField(
        _('Tipo / Rango'),
        max_length=20,
        choices=Rank.choices,
        default=Rank.BRILLANTE
    )

    zone_or_team = models.CharField(
        _('Zona / Equipo'),
        max_length=100,
        blank=True,
        null=True
    )
    # AGREGAR ESTE CAMPO: Relación jerárquica autorreferencial
    coordinadora = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendedoras_a_cargo',
        verbose_name=_('Coordinadora Asignada')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name_paternal']

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios de la Red')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_primary_display()})"

    @property
    def full_name(self):
        maternal = f" {self.last_name_maternal}" if self.last_name_maternal else ""
        return f"{self.first_name} {self.last_name_paternal}{maternal}".strip()