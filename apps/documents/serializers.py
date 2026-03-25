"""Serializers for document APIs."""

from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    standard_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "file",
            "file_name",
            "text",
            "extracted_text",
            "uploaded_at",
            "standard",
            "standard_name",
        ]

    def get_file_name(self, obj):
        return obj.file.name if obj.file else None

    def get_standard_name(self, obj):
        return obj.standard.name if obj.standard else None
