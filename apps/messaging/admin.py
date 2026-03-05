from django.contrib import admin

from .models import MessageTemplate


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_type", "channel", "active", "version")
    list_filter = ("template_type", "channel", "active")
    search_fields = ("name", "subject", "body")
