"""Serializers used in the compliance application."""

from rest_framework import serializers

from .models import AuditResult


class AuditResultSerializer(serializers.ModelSerializer):
    document_name = serializers.SerializerMethodField()
    standard_name = serializers.SerializerMethodField()
    violation_summaries = serializers.SerializerMethodField()
    detected_keywords = serializers.SerializerMethodField()

    steps = serializers.JSONField(read_only=True)

    class Meta:
        model = AuditResult
        fields = [
            "id",
            "document",
            "document_name",
            "standard",
            "standard_name",
            "score",
            "status",
            "violations",
            "detected_keywords",
            "violation_details",
            "violation_summaries",
            "risks",
            "recommendations",
            "missing_controls",
            "steps",
            "created_at",
        ]

    def get_document_name(self, obj):
        try:
            if obj.document and obj.document.file:
                return obj.document.file.name
        except Exception:
            pass
        return None

    def get_standard_name(self, obj):
        try:
            if obj.standard:
                return obj.standard.name
        except Exception:
            pass
        return None

    def get_violation_summaries(self, obj):
        details = obj.violation_details or []
        summaries = []
        for item in details:
            if isinstance(item, dict):
                rid = item.get("rule_id") or item.get("rule", {}).get("id")
                status = item.get("status")
                confidence = item.get("confidence")
                reason = item.get("reason") or item.get("evidence_used")
                snippet = item.get("evidence_used") or ""
                if snippet and len(snippet) > 100:
                    snippet = snippet[:100] + "..."
                summaries.append(
                    {
                        "rule_id": rid,
                        "status": status,
                        "confidence": confidence,
                        "snippet": snippet,
                        "reason": reason,
                    }
                )
            else:
                summaries.append({"text": str(item)})
        return summaries

    def get_detected_keywords(self, obj):
        details = obj.violation_details or []
        keywords = set()
        for item in details:
            if isinstance(item, dict):
                for kw in item.get("detected_keywords", []) or []:
                    keywords.add(kw)
        return sorted(keywords)
