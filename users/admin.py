# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role_primary', 'role_secondary', 'zone_or_team', 'is_active')
    list_filter = ('role_primary', 'zone_or_team', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'zone_or_team')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Estructura Comercial', {'fields': ('role_primary', 'role_secondary', 'zone_or_team')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'role_primary', 'zone_or_team', 'password1', 'password2'),
        }),
    )