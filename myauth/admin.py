from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration untuk custom User model
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'show_password', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser', 'show_password')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informasi Tambahan', {'fields': ('role', 'show_password')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informasi Tambahan', {'fields': ('role', 'show_password')}),
    )
