"""Admin models for standards management."""

from django.contrib import admin

from .models import Standard, Control


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ("identifier", "standard")
    search_fields = ("identifier", "description")
    list_filter = ("standard",)
