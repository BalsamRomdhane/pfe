"""PDF report generation for audit results."""

import os

from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class ReportService:
    """Generate PDF audit reports."""

    def generate_pdf(self, audit_result):
        """Generate a PDF report for the given AuditResult or a structured result dict."""
        output_dir = os.path.join(settings.MEDIA_ROOT, "reports")
        os.makedirs(output_dir, exist_ok=True)

        # Support both AuditResult instances and plain dict results
        if isinstance(audit_result, dict):
            filename = f"audit_{audit_result.get('document', {}).get('id', 'unknown')}.pdf"
            report_data = audit_result
        else:
            filename = f"audit_{audit_result.id}.pdf"
            report_data = {
                "document": {"name": getattr(audit_result.document, "file", None) and audit_result.document.file.name},
                "standard": {"name": getattr(audit_result.standard, "name", None)},
                "score": audit_result.score,
                "status": audit_result.status,
                "violations": audit_result.violations or [],
                "recommendations": audit_result.recommendations or [],
            }

        output_path = os.path.join(output_dir, filename)

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        y = height - 72

        c.setFont("Helvetica-Bold", 18)
        c.drawString(72, y, "Compliance Audit Report")
        y -= 36

        c.setFont("Helvetica", 12)
        doc_name = report_data.get("document", {}).get("name") or "N/A"
        c.drawString(72, y, f"Document: {doc_name}")
        y -= 18
        standard_name = report_data.get("standard", {}).get("name") or "N/A"
        c.drawString(72, y, f"Standard: {standard_name}")
        y -= 18
        c.drawString(72, y, f"Score: {report_data.get('score', 'N/A')}")
        y -= 24

        def _draw_list(title, items):
            nonlocal y
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, y, title)
            y -= 18
            c.setFont("Helvetica", 11)
            if not items:
                c.drawString(90, y, "None")
                y -= 16
                return
            for item in items:
                c.drawString(90, y, f"- {item}")
                y -= 16
                if y < 72:
                    c.showPage()
                    y = height - 72

        _draw_list("Violations", report_data.get("violations", []))
        y -= 10
        _draw_list("Risks", report_data.get("risks", []))
        y -= 10
        _draw_list("Recommendations", report_data.get("recommendations", []))

        c.save()
        return output_path
