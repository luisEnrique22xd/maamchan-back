# Register your models here.
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
    list_display = ('sku', 'name', 'category', 'price_retail', 'price_wholesale', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('sku', 'name')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'customer_name', 'sale_type', 'status', 'total_amount', 'balance_due', 'created_at')
    list_filter = ('sale_type', 'status', 'created_at')
    inlines = [SaleItemInline, PaymentInline]