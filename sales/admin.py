from django.contrib import admin
from .models import Category, Product, Sale, SaleItem, Payment


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Campos adaptados al modelo real: code, public_price y seller_price
    list_display = ('code', 'name', 'category', 'public_price', 'seller_price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('code', 'name')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'customer_name', 'sale_type', 'status', 'total_amount', 'balance_due', 'created_at')
    list_filter = ('sale_type', 'status', 'created_at')
    inlines = [SaleItemInline, PaymentInline]