"""Result formatter for explainable compliance output.

Transforms raw compliance assessment data into a user-friendly,
highly explainable format that shows evidence, reasoning, and scoring.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class ComplianceResultFormatter:
    """Formats compliance results into explainable structures."""

    def format_control_assessment(
        self,
        control_id: str,
        control_description: str,
        score: int,
        status: str,
        confidence: float,
        evidence: List[str],
        missing_elements: List[str],
        factor_breakdown: Dict[str, int],
        violations: Optional[Dict[str, Any]] = None,
        reasoning: str = "",
        auditor_notes: str = ""
    ) -> Dict[str, Any]:
        """Format a single control assessment result with violation details.
        
        Returns:
            Explainable control assessment with violations
        """
        violation_info = {
            "has_violations": False,
            "violation_count": 0,
            "critical_violations": 0,
            "details": []
        }
        
        if violations and violations.get("has_violations"):
            violation_info = {
                "has_violations": True,
                "violation_count": violations.get("violation_count", 0),
                "critical_violations": violations.get("critical_violation_count", 0),
                "violation_status": violations.get("violation_status", "none"),
                "details": violations.get("violation_patterns", [])[:3],
                "evidence_gaps": violations.get("evidence_gaps", [])[:2],
                "recommendations": violations.get("recommendations", [])
            }
        
        # Normalize evidence entries so downstream consumers always receive a
        # consistent structure (dicts with sentence + score), while still
        # supporting legacy string-only lists.
        normalized_evidence: List[Dict[str, Any]] = []
        for item in evidence or []:
            if isinstance(item, str):
                normalized_evidence.append({"sentence": item, "score": None})
            elif isinstance(item, dict):
                sentence = (
                    item.get("sentence")
                    or item.get("text")
                    or item.get("chunk_text")
                    or item.get("evidence_used")
                    or ""
                )
                normalized_evidence.append({"sentence": sentence, "score": item.get("score")})
            else:
                normalized_evidence.append({"sentence": str(item), "score": None})

        examples = [e.get("sentence") for e in normalized_evidence[:3] if e.get("sentence")]

        return {
            "control_id": control_id,
            "control_description": control_description,
            "score": score,
            "score_out_of_100": f"{score}/100",
            "status": status.upper(),
            "status_label": self._get_status_label(status),
            "confidence": confidence,
            "confidence_percentage": f"{int(confidence * 100)}%",
            "violations": violation_info,
            "evidence": {
                "found": len(normalized_evidence) > 0,
                "count": len(normalized_evidence),
                "examples": examples,
                "items": normalized_evidence,
            },
            "gaps": {
                "missing_elements": missing_elements,
                "missing_count": len(missing_elements),
                "has_gaps": len(missing_elements) > 0
            },
            "scoring_breakdown": {
                "factors": factor_breakdown,
                "methodology": "Weighted average of 5 independent factors with violation penalties"
            },
            "reasoning": reasoning if reasoning else "Assessment based on evidence, structure, and violation analysis",
            "auditor_notes": auditor_notes,
            "recommendations": self._get_recommendations(status, score, missing_elements),
            "timestamp": datetime.now().isoformat()
        }

    def format_document_assessment(
        self,
        document_id: str,
        standard_id: str,
        overall_score: int,
        overall_status: str,
        confidence: float,
        controls: List[Dict[str, Any]],
        document_structure_score: int,
        language_quality_score: int,
        document_language: str = "unknown",
        violations_summary: Optional[Dict[str, Any]] = None,
        missing_controls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Format complete document assessment result with violation data.
        
        Returns:
            Comprehensive document compliance report with violations
        """
        compliant_controls = [c for c in controls if c["status"] == "compliant"]
        partial_controls = [c for c in controls if c["status"] == "partially_compliant"]
        non_compliant = [c for c in controls if c["status"] == "non_compliant"]

        compliance_summary = {
            "total_controls": len(controls),
            "compliant": len(compliant_controls),
            "partially_compliant": len(partial_controls),
            "non_compliant": len(non_compliant),
            "compliance_percentage": f"{int(len(compliant_controls) / len(controls) * 100)}%" if controls else "0%"
        }
        
        # Aggregate violation information
        total_violations = sum(c.get("violations", {}).get("violation_count", 0) for c in controls)
        critical_violations = sum(c.get("violations", {}).get("critical_violation_count", 0) for c in controls)
        
        if missing_controls is None:
            missing_controls = []

        return {
            "document_id": document_id,
            "standard_id": standard_id,
            "document_language": document_language,
            "assessment_date": datetime.now().isoformat(),
            "overall_assessment": {
                "score": overall_score,
                "score_out_of_100": f"{overall_score}/100",
                "status": overall_status.upper(),
                "status_label": self._get_status_label(overall_status),
                "confidence": confidence,
                "confidence_percentage": f"{int(confidence * 100)}%"
            },
            "violation_summary": {
                "total_violations_detected": total_violations,
                "critical_violations": critical_violations,
                "violation_auto_classification": total_violations >= 3 or critical_violations >= 1,
                "auto_classification_reason": self._get_violation_classification_reason(
                    total_violations, critical_violations, len(non_compliant), len(controls)
                )
            },
            "compliance_summary": compliance_summary,
            "missing_controls": {
                "list": missing_controls,
                "count": len(missing_controls),
                "has_missing": len(missing_controls) > 0
            },
            "quality_metrics": {
                "document_structure_score": document_structure_score,
                "language_quality_score": language_quality_score,
                "overall_quality": f"{int((document_structure_score + language_quality_score) / 2)}/100"
            },
            "control_details": {
                "compliant": [self._summarize_control(c) for c in compliant_controls],
                "partially_compliant": [self._summarize_control(c) for c in partial_controls],
                "non_compliant": [self._summarize_control(c) for c in non_compliant]
            },
            "priority_actions": self._generate_priority_actions(
                overall_score,
                non_compliant,
                partial_controls,
                missing_controls
            ),
            "executive_summary": self._generate_executive_summary(
                overall_score,
                overall_status,
                compliance_summary,
                total_violations
            ),
            "next_steps": self._generate_next_steps(overall_status),
            "critical_findings": self._extract_critical_findings(controls)
        }

    def format_audit_result(
        self,
        audit_result_id: str,
        document_assessment: Dict[str, Any],
        audit_verification: Dict[str, Any],
        pdf_report_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format final audit result with all details and verification.
        
        Returns:
            Complete audit result with verification status
        """
        return {
            "audit_result_id": audit_result_id,
            "assessment": document_assessment,
            "auditor_verification": {
                "verdict": audit_verification.get("audit_verdict", "pending"),
                "inconsistencies": audit_verification.get("inconsistencies", []),
                "findings": audit_verification.get("auditor_findings", []),
                "confidence_adjustment": f"{int(audit_verification.get('confidence_adjustment', 0))}",
                "adjusted_score": audit_verification.get("adjusted_score"),
                "adjusted_status": audit_verification.get("adjusted_status")
            },
            "report_url": pdf_report_url,
            "exportable_formats": {
                "json": True,
                "pdf": pdf_report_url is not None,
                "csv": True
            },
            "generated_at": datetime.now().isoformat()
        }

    def format_controls_comparison(
        self,
        standard_id: str,
        controls_assessment: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format comparison view of all controls for a standard.
        
        Useful for dashboard and reporting.
        """
        # Sort by score
        sorted_controls = sorted(
            controls_assessment,
            key=lambda c: c.get("score", 0),
            reverse=True
        )

        return {
            "standard_id": standard_id,
            "total_controls": len(controls_assessment),
            "controls_ranked": [
                {
                    "rank": idx + 1,
                    "control_id": c.get("control_id"),
                    "score": c.get("score"),
                    "status": c.get("status"),
                    "confidence": c.get("confidence"),
                    "evidence_count": len(c.get("evidence", {}).get("examples", []))
                }
                for idx, c in enumerate(sorted_controls)
            ],
            "statistics": self._calculate_statistics(controls_assessment)
        }

    # Private helper methods

    def _get_violation_classification_reason(
        self,
        total_violations: int,
        critical_violations: int,
        non_compliant_count: int,
        total_controls: int
    ) -> str:
        """Get reason for violation-based auto-classification."""
        if critical_violations >= 1:
            return f"{critical_violations} critical violation(s) detected - automatic non-compliance"
        elif total_violations >= 3:
            return f"{total_violations} violations detected - meets auto-classify threshold"
        elif non_compliant_count > total_controls * 0.5:
            return f"{non_compliant_count}/{total_controls} controls non-compliant"
        return ""

    def _extract_critical_findings(self, controls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract critical findings from control assessments."""
        critical = []
        
        for control in controls:
            violations = control.get("violations", {})
            if violations.get("critical_violation_count", 0) > 0:
                critical.append({
                    "control_id": control.get("control_id", "Unknown"),
                    "severity": "CRITICAL",
                    "finding": f"Critical violation(s) in {control.get('control_id')}",
                    "action_required": "Immediate remediation required"
                })
            elif control.get("status") == "non_compliant":
                critical.append({
                    "control_id": control.get("control_id", "Unknown"),
                    "severity": "HIGH",
                    "finding": f"Non-compliant control: {control.get('control_id')}",
                    "action_required": "Implement missing elements"
                })
        
        return critical

    def _get_status_label(self, status: str) -> str:
        """Get human-friendly status label."""
        labels = {
            "compliant": "✓ Compliant",
            "partially_compliant": "⚠ Partially Compliant",
            "non_compliant": "✗ Non-Compliant",
            "fully_compliant": "✓ Fully Compliant",
            "mostly_compliant": "✓ Mostly Compliant"
        }
        return labels.get(status.lower(), status)

    def _summarize_control(self, control: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a control for list view."""
        return {
            "control_id": control.get("control_id"),
            "score": control.get("score"),
            "status": control.get("status"),
            "confidence": control.get("confidence"),
            "key_finding": self._extract_key_finding(control)
        }

    def _extract_key_finding(self, control: Dict[str, Any]) -> str:
        """Extract key finding from control."""
        evidence = control.get("evidence", {})
        if evidence.get("found"):
            return f"Evidence found: {evidence.get('count')} sentence(s)"
        
        gaps = control.get("gaps", {})
        if gaps.get("missing_elements"):
            return f"Missing: {', '.join(gaps['missing_elements'][:2])}"
        
        return "No issues identified"

    def _get_recommendations(
        self,
        status: str,
        score: int,
        missing_elements: List[str]
    ) -> List[str]:
        """Generate recommendations based on control status."""
        recommendations = []

        if status == "non_compliant":
            recommendations.append("Implement controls immediately to address compliance gap")
            if missing_elements:
                recommendations.append(f"Add missing elements: {', '.join(missing_elements[:3])}")

        elif status == "partially_compliant":
            recommendations.append("Enhance existing controls to achieve full compliance")
            if score < 50:
                recommendations.append("Consider comprehensive review and redesign of this control")
            else:
                recommendations.append("Minor adjustments needed to reach full compliance")

        elif status == "compliant":
            recommendations.append("Control is compliant. Maintain current implementation")
            recommendations.append("Schedule regular reviews to ensure continued compliance")

        return recommendations

    def _generate_priority_actions(
        self,
        overall_score: int,
        non_compliant: List[Dict],
        partial_controls: List[Dict],
        missing_controls: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate priority action items with violation context."""
        actions = []

        # Critical actions for non-compliant controls
        for control in non_compliant[:3]:
            actions.append({
                "priority": "CRITICAL",
                "action": f"Address non-compliance in control {control.get('control_id')}",
                "deadline": "URGENT",
                "impact": "Compliance Risk",
                "violations": control.get("violations", {}).get("violation_count", 0)
            })

        # Medium priority for partial controls
        for control in partial_controls[:3]:
            actions.append({
                "priority": "HIGH",
                "action": f"Improve partial compliance in control {control.get('control_id')}",
                "deadline": "30 days",
                "impact": "Compliance Gap",
                "violations": control.get("violations", {}).get("violation_count", 0)
            })
        
        # Add missing controls to priority actions
        if missing_controls:
            for missing in missing_controls[:3]:
                actions.append({
                    "priority": "HIGH",
                    "action": f"Implement missing: {missing}",
                    "deadline": "30-60 days",
                    "impact": "Governance Gap"
                })

        return actions

    def _generate_executive_summary(
        self,
        overall_score: int,
        overall_status: str,
        compliance_summary: Dict[str, Any],
        total_violations: int = 0
    ) -> str:
        """Generate executive summary with violation context."""
        summary = f"Document compliance assessment: {overall_score}/100 ({self._get_status_label(overall_status)})\n"
        summary += f"Compliant controls: {compliance_summary['compliant']}/{compliance_summary['total_controls']} "
        summary += f"({compliance_summary['compliance_percentage']})\n"

        if total_violations > 0:
            summary += f"⚠ {total_violations} violation(s) detected\n"

        if compliance_summary['non_compliant'] > 0:
            summary += f"⚠ {compliance_summary['non_compliant']} non-compliant control(s) require remediation\n"

        if overall_score >= 80:
            summary += "Overall assessment: Document demonstrates strong compliance posture"
        elif overall_score >= 50:
            summary += "Overall assessment: Document shows moderate compliance with areas for improvement"
        else:
            summary += "❌ Overall assessment: Document requires significant compliance improvements and has critical violations"

        return summary

    def _generate_next_steps(self, overall_status: str) -> List[str]:
        """Generate recommended next steps."""
        if overall_status == "non_compliant":
            return [
                "1. Convene compliance team to address critical gaps",
                "2. Develop remediation plan for each non-compliant control",
                "3. Schedule follow-up audit within 30 days",
                "4. Report to management with action items"
            ]
        elif overall_status == "partially_compliant":
            return [
                "1. Review partial controls for improvement opportunities",
                "2. Create enhancement roadmap",
                "3. Schedule re-assessment in 60 days",
                "4. Monitor progress against plan"
            ]
        else:
            return [
                "1. Document and archive compliance evidence",
                "2. Schedule routine maintenance review",
                "3. Monitor for any changes affecting compliance",
                "4. Plan next annual assessment"
            ]

    def _calculate_statistics(self, controls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate statistics."""
        scores = [c.get("score", 0) for c in controls]
        
        return {
            "average_score": int(sum(scores) / len(scores)) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "total_controls": len(controls),
            "score_distribution": self._get_score_distribution(scores)
        }

    def _get_score_distribution(self, scores: List[int]) -> Dict[str, int]:
        """Get distribution of scores in categories."""
        return {
            "80_plus": sum(1 for s in scores if s >= 80),
            "60_to_79": sum(1 for s in scores if 60 <= s < 80),
            "40_to_59": sum(1 for s in scores if 40 <= s < 60),
            "below_40": sum(1 for s in scores if s < 40)
        }
