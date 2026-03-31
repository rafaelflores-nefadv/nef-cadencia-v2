from django.contrib import admin

from .models import SystemConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("config_key", "value_type", "updated_at")
    list_filter = ("value_type", "updated_at")
    search_fields = ("config_key", "description", "config_value")
