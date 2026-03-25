"""Serializers for standards and controls."""

from rest_framework import serializers

from .models import Standard, Control


class ControlSerializer(serializers.ModelSerializer):
    standard = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Control
        fields = ["id", "standard", "identifier", "description"]


class StandardSerializer(serializers.ModelSerializer):
    controls = ControlSerializer(many=True, read_only=True)

    class Meta:
        model = Standard
        fields = ["id", "name", "description", "controls"]
