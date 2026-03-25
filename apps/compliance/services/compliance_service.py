"""Compliance service coordinating the audit pipeline."""

import logging
from typing import Dict, List

from apps.documents.models import Document
from apps.standards.models import Standard
from apps.compliance.services.report_service import ReportService
from apps.compliance.models import AuditResult

from services.audit_pipeline import AuditPipeline

logger = logging.getLogger(__name__)


class ComplianceService:
    """Runs a compliance audit pipeline over documents."""

    def __init__(self):
        self.pipeline = AuditPipeline()
        self.report_service = ReportService()

    def run_audit(self, document: Document, standard: Standard) -> AuditResult:
        """Run the full audit workflow for a single document."""
        result = self.pipeline.run(document, standard)

        # Persist the result in the database for later retrieval
        audit = AuditResult.objects.create(
            document=document,
            standard=standard,
            score=result.get("score", 0),
            status=result.get("status", "non_compliant"),
            violations=[v.get("rule_id") for v in result.get("violations", [])],
            violation_details=result.get("violations", []),
            risks=result.get("risks", []),
            recommendations=result.get("recommendations", []),
            missing_controls=[v.get("rule_id") for v in result.get("violations", [])],
            detected_keywords=result.get("detected_keywords", []),
            steps=result.get("steps", []),
        )

        try:
            self.report_service.generate_pdf(result)
        except Exception as ex:
            logger.warning("Failed to generate PDF report: %s", ex)

        return audit
