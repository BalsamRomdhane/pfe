"""Admin configuration for document storage and embeddings."""

from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "standard")
    search_fields = ("file", "text")
    list_filter = ("uploaded_at",)
