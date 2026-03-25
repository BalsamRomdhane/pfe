"""Helper for generating PDF reports for audits."""

from apps.compliance.services.report_service import ReportService


def generate_audit_report(audit_result):
    """Generate a PDF for a given audit result."""
    service = ReportService()
    return service.generate_pdf(audit_result)
