"""Models for document ingestion, chunking, and embedding storage."""

from django.db import models
from django.utils import timezone


class Document(models.Model):
    """Represents an uploaded document for compliance analysis."""

    file = models.FileField(upload_to="documents/%Y/%m/%d/")
    text = models.TextField(blank=True, default="")
    extracted_text = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    standard = models.ForeignKey(
        "standards.Standard",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )

    def __str__(self) -> str:
        return f"Document {self.id} ({self.file.name})"


