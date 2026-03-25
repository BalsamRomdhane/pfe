"""Structured audit report generation.

This module generates structured audit reports containing scores, risk levels,
violations, evidence snippets, and recommendations.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates structured audit reports from pipeline results."""

    def generate(self, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Return a structured report dict suitable for UI and PDF generation."""
        # Build human-friendly violation details
        violations = audit_result.get("rule_evaluations", []) or []
        formatted_violations: List[Dict[str, Any]] = []
        for v in violations:
            formatted_violations.append(
                {
                    "rule_id": v.get("rule_id"),
                    "status": v.get("status"),
                    "severity": v.get("severity"),
                    "confidence": v.get("confidence"),
                    "evidence_strength": v.get("evidence_strength"),
                    "evidence_snippet": (v.get("evidence_used") or "")[:200],
                    "reason": v.get("reason"),
                }
            )

        return {
            "score": audit_result.get("score"),
            "risk_level": audit_result.get("risk_level"),
            "status": audit_result.get("status"),
            "violations": formatted_violations,
            "recommendations": audit_result.get("recommendations", []),
        }
