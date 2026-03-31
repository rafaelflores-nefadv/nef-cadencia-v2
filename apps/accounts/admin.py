"""
Admin para models de User customizado.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin customizado para User."""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'default_workspace', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'default_workspace']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ['phone', 'avatar', 'bio', 'default_workspace']
        }),
        ('Timestamps', {
            'fields': ['updated_at'],
            'classes': ['collapse']
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'updated_at']
    
    def get_queryset(self, request):
        """Otimizar queries."""
        qs = super().get_queryset(request)
        return qs.select_related('default_workspace')
