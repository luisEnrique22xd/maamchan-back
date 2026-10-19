from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser

class Campaign(models.Model):
    name = models.CharField(_('Nombre de la Campaña'), max_length=150)
    code = models.CharField(_('Código de Campaña'), max_length=20, unique=True)
    start_date = models.DateField(_('Fecha de Inicio'))
    end_date = models.DateField(_('Fecha de Cierre'))
    global_target = models.DecimalField(_('Meta Global ($)'), max_digits=12, decimal_places=2)
    is_active = models.BooleanField(_('Campaña Activa'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Campaña')
        verbose_name_plural = _('Campañas')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.code} - {self.name}"


class LevelConfig(models.Model):
    """Configuración de niveles basada en la Tabla de Ganancias Nivel Bronce"""
    class LevelName(models.TextChoices):
        BRILLANTE = 'BRILLANTE', 'Coor. Brillante'
        ZAFIRO = 'ZAFIRO', 'Coor. Zafiro'
        ORO = 'ORO', 'Coor. Oro'
        PLATINO = 'PLATINO', 'Ger. zona Platino'
        ESMERALDA = 'ESMERALDA', 'Esmeralda'
        DIAMANTE = 'DIAMANTE', 'Diamante Black'

    name = models.CharField(max_length=50, choices=LevelName.choices, unique=True)
    required_orders = models.PositiveIntegerField(_('Pedidos Requeridos'))
    earnings_per_order = models.DecimalField(_('Ganas por Pedido ($)'), max_digits=10, decimal_places=2)
    cash_bonus = models.DecimalField(_('Ganas en Dinero ($)'), max_digits=10, decimal_places=2, default=0.00)
    free_product_bonus = models.DecimalField(_('Ganas en Producto Gratis ($)'), max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.get_name_display()} ({self.required_orders} pedidos)"


class TargetByTeam(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='team_targets')
    coordinator = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='campaign_targets',
        limit_choices_to={'role_primary': 'COORDINADORA'}
    )
    target_orders = models.PositiveIntegerField(_('Meta de Pedidos'), default=5)
    target_amount = models.DecimalField(_('Meta del Equipo ($)'), max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ['campaign', 'coordinator']
        verbose_name = _('Meta por Coordinadora')
        verbose_name_plural = _('Metas por Coordinadora')