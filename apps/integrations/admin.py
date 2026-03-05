from django.contrib import admin

from .models import Integration


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ("name", "channel", "enabled")
    list_filter = ("channel", "enabled")
    search_fields = ("name", "channel")
