# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('Nombre de Categoría'), max_length=100, unique=True)
    description = models.TextField(_('Descripción'), blank=True, null=True)

    class Meta:
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(_('SKU / Código'), max_length=50, unique=True)
    name = models.CharField(_('Nombre del Producto'), max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(_('Descripción'), blank=True, null=True)
    
    price_retail = models.DecimalField(_('Precio Público (Catálogo)'), max_digits=10, decimal_places=2)
    price_wholesale = models.DecimalField(_('Precio Vendedora'), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_('Inventario Disponible'), default=0)
    
    is_active = models.BooleanField(_('Activo'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Producto')
        verbose_name_plural = _('Productos')

    def __str__(self):
        return f"[{self.sku}] {self.name}"


class Sale(models.Model):
    class SaleType(models.TextChoices):
        CONTADO = 'CONTADO', _('Contado')
        CREDITO = 'CREDITO', _('Crédito')
        ANTICIPO = 'ANTICIPO', _('Anticipo / Apartado')

    class Status(models.TextChoices):
        PENDIENTE = 'PENDIENTE', _('Pendiente de Pago')
        PAGADO = 'PAGADO', _('Pagado Completamente')
        CANCELADO = 'CANCELADO', _('Cancelado')

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name=_('Vendedora / Responsable')
    )
    customer_name = models.CharField(_('Cliente Final'), max_length=150, blank=True, null=True)
    sale_type = models.CharField(_('Tipo de Venta'), max_length=20, choices=SaleType.choices, default=SaleType.CONTADO)
    status = models.CharField(_('Estado'), max_length=20, choices=Status.choices, default=Status.PENDIENTE)

    total_amount = models.DecimalField(_('Monto Total'), max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(_('Monto Pagado/Abonado'), max_digits=10, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(_('Saldo Pendiente'), max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Venta')
        verbose_name_plural = _('Ventas y Transacciones')
        ordering = ['-created_at']

    def __str__(self):
        return f"Venta #{self.id} - {self.seller.full_name} (${self.total_amount})"

    def update_totals(self):
        """ Recalcula el total de la venta y ajusta el saldo restante. """
        items_total = sum(item.subtotal for item in self.items.all())
        self.total_amount = items_total
        self.balance_due = self.total_amount - self.paid_amount
        if self.balance_due <= 0 and self.total_amount > 0:
            self.status = self.Status.PAGADO
        self.save()


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        EFECTIVO = 'EFECTIVO', _('Efectivo')
        TRANSFERENCIA = 'TRANSFERENCIA', _('Transferencia (SPEI)')
        TARJETA = 'TARJETA', _('Tarjeta de Débito/Crédito')

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_('Monto Abonado'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_('Método de Pago'), max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.EFECTIVO)
    reference = models.CharField(_('Referencia / Folio'), max_length=100, blank=True, null=True)
    notes = models.TextField(_('Notas'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Abono / Pago')
        verbose_name_plural = _('Historial de Abonos')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar acumulado abonado en la Venta
        total_paid = sum(p.amount for p in self.sale.payments.all())
        self.sale.paid_amount = total_paid
        self.sale.update_totals()