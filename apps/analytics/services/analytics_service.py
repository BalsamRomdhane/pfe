"""Analytics service for compliance dashboards."""

from typing import Dict

from django.db import models

from apps.compliance.models import AuditResult, ATCNameValidation


class AnalyticsService:
    """Computes dashboard metrics for compliance analyses."""

    def get_dashboard(self) -> Dict:
        results = AuditResult.objects.select_related("standard").all()
        atc_violations = ATCNameValidation.objects.filter(status="NON_COMPLIANT").count()

        total_documents = results.values_list("document", flat=True).distinct().count()
        total_audits = results.count()
        agg = results.aggregate(avg_score=models.Avg("score"))
        average_score = float(agg.get("avg_score") or 0)

        violations_per_standard = {}
        risks_per_standard = {}

        for r in results:
            standard_name = r.standard.name if r.standard else "Unassigned"
            violations_per_standard.setdefault(standard_name, 0)
            risks_per_standard.setdefault(standard_name, 0)
            violations_per_standard[standard_name] += len(r.violations or [])
            risks_per_standard[standard_name] += len(r.risks or [])

        # Time series data (last 30 days)
        dates = (
            results
            .annotate(date=models.functions.TruncDate('created_at'))
            .values('date')
            .annotate(count=models.Count('id'), avg_score=models.Avg('score'))
            .order_by('date')
        )

        documents_over_time = [
            {'date': d['date'].isoformat(), 'count': d['count'], 'average_score': float(d['avg_score'] or 0)}
            for d in dates
        ]

        # Top violations per standard
        top_violations = sorted(
            violations_per_standard.items(), key=lambda item: item[1], reverse=True
        )[:5]

        # Recent audits
        recent_audits = [
            {
                "id": str(r.id),
                "document_name": r.document.file.name if (r.document and hasattr(r.document, "file") and r.document.file) else "Unknown",
                "standard_name": r.standard.name if r.standard else "-",
                "score": r.score,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results.select_related("document", "standard").order_by("-created_at")[:6]
        ]

        return {
            "total_documents": total_documents,
            "total_audits": total_audits,
            "average_score": average_score,
            "violations_per_standard": violations_per_standard,
            "risk_distribution": risks_per_standard,
            "documents_over_time": documents_over_time,
            "top_violations": [{"standard": k, "count": v} for k, v in top_violations],
            "atc_violations": atc_violations,
            "recent_audits": recent_audits,
        }
