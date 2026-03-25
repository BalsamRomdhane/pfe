"""Compliance rule engine.

This module defines rules and provides utilities to load and validate rules
against compliance standards.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ComplianceRule:
    id: str
    standard: str
    description: str
    severity: str
    keywords: List[str] = field(default_factory=list)
    expected_evidence: Optional[str] = None
    control_type: Optional[str] = None


class RuleEngine:
    """Loads and normalizes rules from standards."""

    def __init__(self):
        pass

    def rules_from_standard(self, standard: Any) -> List[ComplianceRule]:
        """Convert a Standard object into a list of ComplianceRule objects."""
        rules: List[ComplianceRule] = []

        for control in getattr(standard, "controls", []).all():
            keywords = []
            if getattr(control, "keywords", None):
                keywords = [k.strip() for k in control.keywords.split(",") if k.strip()]

            rules.append(
                ComplianceRule(
                    id=str(getattr(control, "identifier", None) or control.pk),
                    standard=str(getattr(standard, "name", "")),
                    description=getattr(control, "description", ""),
                    severity=getattr(control, "severity", "major"),
                    keywords=keywords,
                    expected_evidence=getattr(control, "example_evidence", ""),
                    control_type=getattr(control, "control_type", None) or "unknown",
                )
            )

        return rules
