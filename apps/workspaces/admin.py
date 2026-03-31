"""
Admin para models de Workspace.
"""
from django.contrib import admin
from .models import Workspace, UserWorkspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """Admin para Workspace."""
    
    list_display = ['name', 'slug', 'is_active', 'get_members_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['name', 'slug', 'description']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_members_count(self, obj):
        """Retorna quantidade de membros."""
        return obj.get_members_count()
    get_members_count.short_description = 'Membros'


@admin.register(UserWorkspace)
class UserWorkspaceAdmin(admin.ModelAdmin):
    """Admin para UserWorkspace."""
    
    list_display = ['user', 'workspace', 'role', 'created_at']
    list_filter = ['role', 'workspace', 'created_at']
    search_fields = ['user__username', 'user__email', 'workspace__name']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Relacionamento', {
            'fields': ['user', 'workspace']
        }),
        ('Permissões', {
            'fields': ['role']
        }),
        ('Timestamps', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_queryset(self, request):
        """Otimizar queries."""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'workspace')
