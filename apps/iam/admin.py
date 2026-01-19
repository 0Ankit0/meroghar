from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organization

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'organization', 'is_active')
    list_filter = ('role', 'organization', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Organization Info', {'fields': ('role', 'organization')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Organization Info', {'fields': ('role', 'organization')}),
    )

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
