"""Admin configuration for compliance results."""

from django.contrib import admin

from .models import AuditResult


@admin.register(AuditResult)
class AuditResultAdmin(admin.ModelAdmin):
    list_display = ("document", "standard", "score", "created_at")
    list_filter = ("standard", "created_at")
    search_fields = ("document__file",)
