"""Data models for compliance standards and associated controls."""

from django.db import models


class Standard(models.Model):
    """Represents a compliance standard such as ISO9001, GDPR, or SOC2."""

    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Control(models.Model):
    """A control is a requirement or check within a standard."""

    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("major", "Major"),
        ("minor", "Minor"),
    ]

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name="controls",
    )
    identifier = models.CharField(max_length=128, blank=True)
    description = models.TextField()
    objective = models.TextField(blank=True, default="", help_text="The purpose or objective of this control.")
    keywords = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Comma-separated keywords that indicate evidence for this control.",
    )
    example_evidence = models.TextField(
        blank=True,
        default="",
        help_text="Example evidence text or document excerpts that demonstrate compliance.",
    )
    severity = models.CharField(
        max_length=16,
        choices=SEVERITY_CHOICES,
        default="major",
        help_text="Severity level of this control for scoring and violation prioritization.",
    )

    class Meta:
        verbose_name = "Control"
        verbose_name_plural = "Controls"

    def __str__(self) -> str:
        return f"{self.standard.name} - {self.identifier or 'Control'}"

