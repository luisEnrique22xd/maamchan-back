from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser

class Campaign(models.Model):
    name = models.CharField(_('Nombre de la Campaña'), max_length=150) # Ej: Campaña 05 - Mayo
    code = models.CharField(_('Código de Campaña'), max_length=20, unique=True) # Ej: C-2026-05
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


class TargetByTeam(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='team_targets')
    coordinator = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='campaign_targets',
        limit_choices_to={'role_primary': 'COORDINADORA'}
    )
    target_amount = models.DecimalField(_('Meta del Equipo ($)'), max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ['campaign', 'coordinator']
        verbose_name = _('Meta por Coordinadora')
        verbose_name_plural = _('Metas por Coordinadora')