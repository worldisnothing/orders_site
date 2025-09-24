from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'name', 'status', 'created_date', 'ready_date']
    list_filter = ['status', 'volume_type', 'created_date']
    search_fields = ['name', 'user__username']
    readonly_fields = ['order_number', 'created_date', 'ready_date']


# Расширение UserAdmin для редактирования пользователей
admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'is_superuser']
    # Копируем fieldsets из UserAdmin и модифицируем только нужное
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )