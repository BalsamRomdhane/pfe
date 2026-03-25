"""Audit reasoning engine.

This module provides higher-level reasoning to validate the consistency of
compliance decisions, detect hallucinations, and ensure explainability.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class AuditReasoningEngine:
    """Provides reasoning checks and adjustments for compliance evaluations."""

    def adjust_rule_evaluations(self, evaluations: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Run heuristic checks on rule evaluations to improve reliability."""
        updated = []
        for ev in evaluations:
            adjusted = ev.copy()
            status = ev.get("status")
            evidence = ev.get("evidence") or []

            # Ensure we can safely concatenate evidence text regardless of None or non-string values.
            evidence_text = "".join(
                [str(c.get("text", "")) if isinstance(c, dict) else str(c or "") for c in evidence]
            )

            # If LLM says compliant but evidence is extremely short, downgrade.
            if status == "compliant" and len(evidence_text) < 20:
                adjusted["status"] = "partially_compliant"
                adjusted["reason"] = (
                    "Evidence is too short to support full compliance; downgraded to partial."
                )

            # Detect contradictions: if evidence is labeled non-compliant but score is high.
            if status == "non_compliant" and ev.get("confidence", 0) > 0.9 and ev.get("score", 0) > 0.85:
                adjusted["reason"] = (
                    "High similarity evidence was found but LLM flagged non-compliance; review for potential contradictions."
                )

            updated.append(adjusted)

        return updated
