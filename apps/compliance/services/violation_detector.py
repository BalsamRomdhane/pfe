"""Violation detection engine for strict compliance scoring.

Identifies violations, missing critical controls, and non-compliant patterns.
Violations significantly reduce compliance scores to ensure accurate classification
of non-compliant documents.
"""

import re
from typing import Dict, List, Optional, Tuple
from apps.compliance.services.evidence_detector import EvidenceDetector
from apps.compliance.services.language_analyzer import LanguageAnalyzer


class ViolationDetector:
    """Detects compliance violations and critical control issues."""

    # Violation patterns that indicate non-compliance
    VIOLATION_PATTERNS = {
        "missing_procedure": {
            "pattern": r"\b(no procedure|lack of procedure|without procedure|not implemented)\b",
            "severity": "critical",
            "weight": 25,
        },
        "missing_responsibility": {
            "pattern": r"\b(no one|no owner|unassigned|owner not defined)\b",
            "severity": "critical",
            "weight": 25,
        },
        "no_enforcement": {
            "pattern": r"\b(not enforced|lack of enforcement|no enforcement|not monitored)\b",
            "severity": "critical",
            "weight": 25,
        },
        "missing_approval": {
            "pattern": r"\b(no approval|not approved|unapproved|no authorization)\b",
            "severity": "high",
            "weight": 15,
        },
        "missing_review": {
            "pattern": r"\b(never reviewed|not reviewed|no review|review missing)\b",
            "severity": "high",
            "weight": 15,
        },
        "incomplete_implementation": {
            "pattern": r"\b(partial|incomplete|partially implemented|work in progress)\b",
            "severity": "medium",
            "weight": 10,
        },
        "conflicting_statements": {
            "pattern": r"\b(but|however|on the other hand|contradicts)\b.*\b(not required|not needed|not applicable)\b",
            "severity": "high",
            "weight": 15,
        },
    }

    # Evidence keywords that MUST be present for compliance
    REQUIRED_EVIDENCE_KEYWORDS = [
        "must", "shall", "required", "mandatory",
        "procedure", "process", "policy",
        "owner", "responsible", "accountability",
        "review", "audit", "monitoring",
        "approval", "authorization", "verification",
        "evidence", "documented", "recorded",
    ]

    # Weak language patterns that reduce confidence
    WEAK_LANGUAGE_PATTERNS = {
        "weak_recommendation": r"\b(should|recommended|suggest|consider|may)\b",
        "optional": r"\b(optional|optional feature|may be|if needed)\b",
        "vague": r"\b(might|could|perhaps|possibly|generally)\b",
    }

    def __init__(self):
        self.evidence_detector = EvidenceDetector()
        self.language_analyzer = LanguageAnalyzer()

    def detect_violations(
        self,
        document_text: str,
        control_description: str,
        is_critical_control: bool = False
    ) -> Dict[str, any]:
        """Detect violations for a specific control.

        Args:
            document_text: Document being evaluated
            control_description: Control requirement
            is_critical_control: Whether this is a critical control

        Returns:
            Dictionary with violations, severity, penalty, and recommendations
        """
        violations = []
        violation_patterns_found = []
        weak_language_found = []
        evidence_gaps = []

        # Check for explicit violation patterns
        for pattern_name, pattern_config in self.VIOLATION_PATTERNS.items():
            matches = re.findall(
                pattern_config["pattern"],
                document_text,
                re.IGNORECASE
            )
            if matches:
                violation_patterns_found.append({
                    "type": pattern_name,
                    "severity": pattern_config["severity"],
                    "weight": pattern_config["weight"],
                    "matches": len(matches),
                    "examples": matches[:2]
                })
                violations.append(pattern_name)

        # Check for weak language
        for weakness_type, pattern in self.WEAK_LANGUAGE_PATTERNS.items():
            weak_matches = re.findall(pattern, document_text, re.IGNORECASE)
            if weak_matches:
                weak_language_found.append({
                    "type": weakness_type,
                    "count": len(weak_matches),
                    "examples": weak_matches[:2]
                })

        # Check for evidence gaps
        evidence = self.evidence_detector.extract_evidence(
            document_text,
            control_description
        )

        # Check if required keywords are present
        missing_keywords = []
        for keyword in self.REQUIRED_EVIDENCE_KEYWORDS:
            if keyword.lower() not in document_text.lower():
                missing_keywords.append(keyword)

        # If many required keywords missing, it's a gap
        if len(missing_keywords) > len(self.REQUIRED_EVIDENCE_KEYWORDS) * 0.5:
            evidence_gaps.append({
                "type": "missing_required_keywords",
                "count": len(missing_keywords),
                "keywords": missing_keywords[:5],
                "severity": "high"
            })

        # Check if evidence was found
        if evidence["evidence_type"] == "none":
            evidence_gaps.append({
                "type": "no_evidence_found",
                "severity": "critical",
                "explanation": "No supporting evidence detected in document"
            })

        # Check for conflicting statements
        conflicting = self._detect_conflicting_statements(document_text)
        if conflicting:
            evidence_gaps.append({
                "type": "conflicting_statements",
                "conflicts": conflicting,
                "severity": "high"
            })

        # Calculate violation count and severity score
        violation_count = len(violations) + len(evidence_gaps)
        critical_violation_count = sum(
            1 for v in violation_patterns_found
            if v["severity"] == "critical"
        ) + sum(
            1 for gap in evidence_gaps
            if gap.get("severity") == "critical"
        )

        # Calculate penalty
        base_penalty = violation_count * 15
        critical_penalty = critical_violation_count * 25
        weak_language_penalty = len(weak_language_found) * 10

        # Critical controls have higher penalties
        if is_critical_control:
            base_penalty *= 1.5
            critical_penalty *= 1.5

        total_penalty = base_penalty + critical_penalty + weak_language_penalty

        # Determine violation status
        violation_status = "none"
        if critical_violation_count >= 1:
            violation_status = "critical"
        elif violation_count >= 2:
            violation_status = "major"
        elif violation_count >= 1:
            violation_status = "minor"

        return {
            "has_violations": len(violations) > 0 or len(evidence_gaps) > 0,
            "violation_count": violation_count,
            "critical_violation_count": critical_violation_count,
            "violation_status": violation_status,
            "violations": violations,
            "violation_patterns": violation_patterns_found,
            "evidence_gaps": evidence_gaps,
            "weak_language": weak_language_found,
            "penalty": int(total_penalty),
            "critical_control_flag": is_critical_control,
            "recommendations": self._generate_violation_recommendations(
                violations, evidence_gaps, violation_patterns_found
            )
        }

    def check_critical_control_compliance(
        self,
        missing_controls: List[str],
        document_text: str,
        standard_id: Optional[str] = None
    ) -> Dict[str, any]:
        """Check for missing critical controls.

        Args:
            missing_controls: List of missing or non-compliant controls
            document_text: Document text
            standard_id: Optional standard identifier

        Returns:
            Dictionary with critical control information and penalties
        """
        # Typical critical controls that must be present
        critical_control_keywords = {
            "access_control": [
                "access control", "user access", "authentication",
                "authorization", "privilege", "role-based"
            ],
            "authentication": [
                "authentication", "password", "mfa", "multi-factor",
                "credential", "identity verification"
            ],
            "encryption": [
                "encryption", "encrypted", "encrypt", "ssl", "tls",
                "cryptographic", "secret key"
            ],
            "audit_logging": [
                "audit log", "logging", "audit trail", "log",
                "system log", "activity log", "event log"
            ],
            "incident_response": [
                "incident response", "incident management", "breach",
                "incident handling", "escalation", "notification"
            ],
            "change_management": [
                "change management", "change control", "change request",
                "approval workflow", "testing", "deployment"
            ],
            "data_protection": [
                "data protection", "data security", "sensitive data",
                "pii", "confidential", "data classification"
            ],
            "vulnerability_management": [
                "vulnerability", "vulnerability assessment",
                "penetration test", "patch management", "updates"
            ],
        }

        missing_critical_controls = []
        for control_name, keywords in critical_control_keywords.items():
            is_present = any(
                keyword.lower() in document_text.lower()
                for keyword in keywords
            )
            is_missing = any(
                keyword.lower() in missing_control.lower()
                for missing_control in missing_controls
                for keyword in keywords
            )

            if is_missing or not is_present:
                missing_critical_controls.append(control_name)

        critical_count = len(missing_critical_controls)
        penalty = critical_count * 25

        return {
            "missing_critical_controls": missing_critical_controls,
            "critical_control_count": critical_count,
            "penalty": penalty,
            "is_critical_issue": critical_count >= 3,
            "recommendations": [
                f"Implement {control.replace('_', ' ').title()} control"
                for control in missing_critical_controls
            ]
        }

    def detect_automatic_non_compliant_triggers(
        self,
        violations_summary: Dict[str, any],
        missing_controls: List[str],
        evidence_score: float,
        control_count: int = 0
    ) -> Dict[str, any]:
        """Check if document should be automatically classified as non-compliant.

        Args:
            violations_summary: Violation detection result
            missing_controls: List of missing controls
            evidence_score: Overall evidence detection score (0-1)
            control_count: Total number of controls being evaluated

        Returns:
            Dictionary with auto-classification decision and reasons
        """
        reasons = []
        triggers = []

        # Trigger 1: 3+ violations
        if violations_summary["violation_count"] >= 3:
            triggers.append("violation_threshold")
            reasons.append(
                f"Too many violations detected ({violations_summary['violation_count']})"
            )

        # Trigger 2: 1+ critical violations
        if violations_summary["critical_violation_count"] >= 1:
            triggers.append("critical_violation_present")
            reasons.append("Critical violation(s) detected")

        # Trigger 3: Evidence score < 0.4 (40%)
        if evidence_score < 0.4:
            triggers.append("insufficient_evidence")
            reasons.append(f"Insufficient evidence score ({evidence_score:.0%})")

        # Trigger 4: More than 2 critical controls missing (from missing_controls list)
        critical_missing = len([c for c in missing_controls
                               if any(critical in c.lower()
                                     for critical in ["access", "auth", "encrypt", "audit"])])
        if critical_missing >= 3:
            triggers.append("too_many_critical_missing")
            reasons.append(f"{critical_missing} critical controls missing")

        # Trigger 5: More than 70% of controls are non-compliant
        if control_count > 0 and len(missing_controls) > control_count * 0.7:
            triggers.append("majority_non_compliant")
            reasons.append(f"Majority of controls are non-compliant")

        should_auto_classify = len(triggers) > 0

        return {
            "auto_classify_non_compliant": should_auto_classify,
            "triggers": triggers,
            "reasons": reasons,
            "trigger_count": len(triggers)
        }

    def calculate_adjusted_score(
        self,
        base_score: int,
        violations: Dict[str, any],
        missing_critical_controls: Dict[str, any],
        evidence_score: float
    ) -> Tuple[int, str]:
        """Calculate final score after applying all violation penalties.

        Args:
            base_score: Initial compliance score (0-100)
            violations: Violation detection result
            missing_critical_controls: Missing critical controls result
            evidence_score: Evidence detection score (0-1)

        Returns:
            Tuple of (adjusted_score, final_status)
        """
        adjusted_score = base_score

        # Apply violation penalties
        adjusted_score -= violations.get("penalty", 0)

        # Apply critical control penalties
        adjusted_score -= missing_critical_controls.get("penalty", 0)

        # Apply evidence-based reduction
        if evidence_score < 0.3:
            adjusted_score -= 40
        elif evidence_score < 0.5:
            adjusted_score -= 25

        # Ensure score stays in bounds
        adjusted_score = max(0, min(100, adjusted_score))

        # Determine status based on strict thresholds
        if adjusted_score >= 80:
            status = "compliant"
        elif adjusted_score >= 50:
            status = "partially_compliant"
        else:
            status = "non_compliant"

        # Override with auto-classification if needed
        auto_check = self.detect_automatic_non_compliant_triggers(
            violations, [], evidence_score
        )
        if auto_check["auto_classify_non_compliant"]:
            status = "non_compliant"
            if adjusted_score > 50:
                adjusted_score = min(adjusted_score, 45)

        return adjusted_score, status

    def _detect_conflicting_statements(self, document_text: str) -> List[Dict[str, any]]:
        """Detect conflicting or contradictory statements in document."""
        conflicts = []
        sentences = re.split(r'\. ', document_text)

        conflict_indicators = [
            ("however", "contradicts"),
            ("but", "contradicts"),
            ("although", "contradicts"),
            ("despite", "contradicts"),
            ("on the other hand", "contradicts"),
            ("conversely", "contradicts"),
        ]

        for i, sentence in enumerate(sentences):
            for indicator1, indicator2 in conflict_indicators:
                if indicator1.lower() in sentence.lower():
                    # Check if there's a negation in the same sentence or next sentence
                    if i + 1 < len(sentences):
                        next_sentence = sentences[i + 1]
                        if any(word in next_sentence.lower()
                               for word in ["not", "no ", "without", "lack", "missing"]):
                            conflicts.append({
                                "sentence1": sentence[:100],
                                "sentence2": next_sentence[:100],
                                "indicator": indicator1
                            })

        return conflicts

    def _generate_violation_recommendations(
        self,
        violations: List[str],
        evidence_gaps: List[Dict[str, any]],
        violation_patterns: List[Dict[str, any]]
    ) -> List[str]:
        """Generate recommendations based on detected violations."""
        recommendations = []

        for violation in violations:
            if "missing_procedure" in violation:
                recommendations.append("Define and document required procedures")
            elif "missing_responsibility" in violation:
                recommendations.append("Assign clear ownership and accountability")
            elif "no_enforcement" in violation:
                recommendations.append("Establish enforcement and monitoring mechanisms")
            elif "missing_approval" in violation:
                recommendations.append("Implement approval workflows and authorizations")
            elif "missing_review" in violation:
                recommendations.append("Schedule regular reviews of policies and procedures")

        for gap in evidence_gaps:
            if gap.get("type") == "no_evidence_found":
                recommendations.append("Provide evidence supporting this control")
            elif gap.get("type") == "missing_required_keywords":
                keywords = gap.get("keywords", [])
                recommendations.append(
                    f"Document requirements using keywords: {', '.join(keywords[:3])}"
                )

        return list(set(recommendations))

    def generate_violation_report(
        self,
        control_id: str,
        violations: Dict[str, any],
        score_before: int,
        score_after: int
    ) -> Dict[str, any]:
        """Generate detailed violation report for a control.

        Returns:
            Comprehensive violation analysis
        """
        return {
            "control_id": control_id,
            "violation_detected": violations["has_violations"],
            "violation_count": violations["violation_count"],
            "violation_status": violations["violation_status"],
            "critical_violations": violations["critical_violation_count"],
            "violation_details": {
                "patterns_found": violations.get("violation_patterns", []),
                "evidence_gaps": violations.get("evidence_gaps", []),
                "weak_language": violations.get("weak_language", [])
            },
            "scoring_impact": {
                "score_before_penalty": score_before,
                "penalty_applied": violations.get("penalty", 0),
                "score_after_penalty": score_after,
                "penalty_type": "violation_based"
            },
            "recommendations": violations.get("recommendations", []),
            "timestamp": ""
        }
