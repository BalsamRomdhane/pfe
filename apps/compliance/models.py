"""Models for storing audit results and risk assessments."""

from django.db import models


class AuditResult(models.Model):
    """Stores the results of a compliance audit run."""

    STATUS_CHOICES = [
        ('compliant', 'Conforme'),
        ('partially_compliant', 'Partiellement Conforme'),
        ('non_compliant', 'Non Conforme'),
    ]

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="audit_results",
    )
    standard = models.ForeignKey(
        "standards.Standard",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_results",
    )

    score = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='non_compliant',
        help_text="Statut de conformité du document"
    )
    violations = models.JSONField(default=list, blank=True)
    violation_details = models.JSONField(default=list, blank=True, help_text="Structured violations with severity and evidence.")
    risks = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    steps = models.JSONField(default=list, blank=True, help_text="Liste des étapes de l'audit.")
    missing_controls = models.JSONField(default=list, blank=True, help_text="Liste des contrôles manquants.")
    detected_keywords = models.JSONField(default=list, blank=True, help_text="List of keywords successfully detected.")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"AuditResult {self.id} (score={self.score}, status={self.status})"

class ATCNameValidation(models.Model):
    """Stores results of ATC document filename validations."""

    STATUS_CHOICES = [
        ('COMPLIANT', 'Compliant'),
        ('NON_COMPLIANT', 'Non compliant'),
    ]

    filename = models.CharField(max_length=512)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"ATCNameValidation({self.filename}) {self.status}"