"""Multi-factor compliance scoring system.

Combines multiple scoring factors to produce a robust compliance score:
- Semantic similarity (0.25)
- Evidence detection (0.25)
- LLM reasoning (0.30)
- Document structure (0.10)
- Policy language quality (0.10)

Violations significantly reduce scores with strict classification thresholds:
- Compliant: score >= 80
- Partially Compliant: 50 <= score < 80
- Non-Compliant: score < 50

This reduces reliance on LLM alone and improves reliability.
"""

import logging
from typing import Dict, List, Optional
from apps.compliance.services.evidence_detector import EvidenceDetector
from apps.compliance.services.structure_validator import StructureValidator
from apps.compliance.services.language_analyzer import LanguageAnalyzer
from apps.compliance.services.violation_detector import ViolationDetector

logger = logging.getLogger(__name__)


class MultiFactorScorer:
    """Produces compliance scores using weighted multiple factors."""

    # Weight distribution
    WEIGHTS = {
        "semantic_similarity": 0.25,
        "evidence_detection": 0.25,
        "llm_reasoning": 0.30,
        "document_structure": 0.10,
        "policy_language": 0.10,
    }

    def __init__(self):
        self.evidence_detector = EvidenceDetector()
        self.structure_validator = StructureValidator()
        self.language_analyzer = LanguageAnalyzer()
        self.violation_detector = ViolationDetector()

    def calculate_control_score(
        self,
        document_text: str,
        control_description: str,
        semantic_similarity: float = 0.5,
        llm_score: Optional[Dict[str, any]] = None,
        is_critical_control: bool = False
    ) -> Dict[str, any]:
        """Calculate compliance score for a single control with violation penalties.
        
        Args:
            document_text: Document being evaluated
            control_description: Control requirement
            semantic_similarity: Similarity score from vector search (0-1)
            llm_score: LLM evaluation result with score and reasoning
            is_critical_control: Whether this is a critical control (higher penalty)
            
        Returns:
            Dictionary with overall score, violations, and strict status classification
        """
        if not document_text or not control_description:
            return {
                "overall_score": 0,
                "confidence": 0.0,
                "status": "non_compliant",
                "violations": {"has_violations": True, "violation_count": 0},
                "factors": {},
                "violation_details": "Missing required data"
            }

        # Calculate individual factor scores
        factors = {}

        # 1. Semantic Similarity (0-100)
        factors["semantic_similarity"] = {
            "score": int(semantic_similarity * 100),
            "weight": self.WEIGHTS["semantic_similarity"],
            "explanation": f"Text relevance: {semantic_similarity:.1%}"
        }

        # 2. Evidence Detection (0-100)
        evidence_result = self.evidence_detector.extract_evidence(
            document_text, 
            control_description
        )
        evidence_score = int(evidence_result["confidence"] * 100)
        factors["evidence_detection"] = {
            "score": evidence_score,
            "weight": self.WEIGHTS["evidence_detection"],
            "explanation": f"Evidence found: {len(evidence_result['evidence'])} sentences",
            "evidence_count": len(evidence_result["evidence"])
        }

        # 3. LLM Reasoning (0-100)
        llm_score_value = 50  # Default neutral
        if llm_score:
            llm_score_value = llm_score.get("score", 50)
            if not (0 <= llm_score_value <= 100):
                llm_score_value = 50
        
        factors["llm_reasoning"] = {
            "score": llm_score_value,
            "weight": self.WEIGHTS["llm_reasoning"],
            "explanation": llm_score.get("explanation", "LLM evaluation") if llm_score else "No LLM evaluation"
        }

        # 4. Document Structure (0-100)
        structure = self.structure_validator.validate_structure(document_text)
        structure_score = structure["structure_score"]
        factors["document_structure"] = {
            "score": structure_score,
            "weight": self.WEIGHTS["document_structure"],
            "explanation": f"Structure maturity: {structure['maturity']}"
        }

        # 5. Policy Language Quality (0-100)
        language_score = self.language_analyzer.language_compliance_score(document_text)
        factors["policy_language"] = {
            "score": language_score,
            "weight": self.WEIGHTS["policy_language"],
            "explanation": f"Language strength: {int(language_score/10)}/10"
        }

        # Calculate base weighted score
        base_score = sum(
            factors[factor]["score"] * factors[factor]["weight"]
            for factor in factors
        )

        # ==== VIOLATION DETECTION AND PENALTIES ====
        violations = self.violation_detector.detect_violations(
            document_text,
            control_description,
            is_critical_control=is_critical_control
        )

        # Apply violation penalties to base score
        score_after_violations = base_score - violations.get("penalty", 0)
        
        # Ensure score stays in valid range
        score_after_violations = max(0, min(100, score_after_violations))

        # ==== STRICT CLASSIFICATION THRESHOLDS ====
        # Apply strict thresholds regardless of semantic similarity
        if score_after_violations >= 80:
            status = "compliant"
            confidence = min(0.95, 0.8 + (score_after_violations - 80) * 0.003)
        elif score_after_violations >= 50:
            status = "partially_compliant"
            confidence = 0.5 + (score_after_violations - 50) * 0.006
        else:
            status = "non_compliant"
            confidence = max(0.5, 0.8 - (50 - score_after_violations) * 0.01)

        # ==== AUTO-CLASSIFICATION FOR NON-COMPLIANCE ====
        # If violations trigger auto-non-compliance, override status
        auto_check = self.violation_detector.detect_automatic_non_compliant_triggers(
            violations,
            [],
            evidence_result["confidence"],
            control_count=0
        )
        if auto_check["auto_classify_non_compliant"]:
            status = "non_compliant"
            score_after_violations = min(score_after_violations, 45)  # Cap non-compliant score
            confidence = 0.85  # High confidence in non-compliance

        return {
            "overall_score": int(score_after_violations),
            "confidence": confidence,
            "status": status,
            "score_before_violations": int(base_score),
            "violation_penalty": violations.get("penalty", 0),
            "violations": violations,
            "auto_non_compliant": auto_check["auto_classify_non_compliant"],
            "auto_non_compliant_reasons": auto_check.get("reasons", []),
            "factors": factors,
            "factor_breakdown": {
                name: factor["score"] for name, factor in factors.items()
            },
            "is_critical_control": is_critical_control
        }

    def calculate_document_score(
        self,
        document_text: str,
        controls: List[Dict[str, any]],
        control_scores: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """Calculate overall document compliance score with strict classification.
        
        Args:
            document_text: Document being evaluated
            controls: List of controls to evaluate
            control_scores: List of scores for each control
            
        Returns:
            Overall compliance score and strict status
        """
        if not control_scores:
            return {
                "overall_score": 0,
                "status": "non_compliant",
                "summary": {}
            }

        # Count compliance statuses
        compliant = sum(1 for cs in control_scores if cs["status"] == "compliant")
        partial = sum(1 for cs in control_scores if cs["status"] == "partially_compliant")
        non_compliant = sum(1 for cs in control_scores if cs["status"] == "non_compliant")
        
        total = len(control_scores)
        violation_count = sum(
            cs.get("violations", {}).get("violation_count", 0)
            for cs in control_scores
        )
        
        # Calculate average score
        scores = [cs["overall_score"] for cs in control_scores]
        overall_score = sum(scores) / len(scores) if scores else 0

        # ==== STRICT CLASSIFICATION LOGIC ====
        # Override overall status with strict rules
        
        # Rule 1: If any critical violations exist, non-compliant
        critical_violations = sum(
            cs.get("violations", {}).get("critical_violation_count", 0)
            for cs in control_scores
        )
        if critical_violations >= 1:
            overall_status = "non_compliant"
            overall_score = min(overall_score, 45)
        
        # Rule 2: If too many violations, non-compliant
        elif violation_count >= 3:
            overall_status = "non_compliant"
            overall_score = min(overall_score, 45)
        
        # Rule 3: If majority are non-compliant, overall is non-compliant
        elif non_compliant > total * 0.5:
            overall_status = "non_compliant"
            overall_score = min(overall_score, 45)
        
        # Rule 4: Use strict score thresholds
        elif overall_score >= 80 and non_compliant == 0:
            overall_status = "compliant"
        elif overall_score >= 50 and non_compliant < total * 0.3:
            overall_status = "partially_compliant"
        else:
            overall_status = "non_compliant"
            overall_score = min(overall_score, 45)

        # Calculate average confidence
        avg_confidence = sum(cs["confidence"] for cs in control_scores) / len(control_scores)

        # Identify missing and non-compliant controls
        missing_controls = []
        for idx, cs in enumerate(control_scores):
            if cs["status"] in ["non_compliant", "partially_compliant"]:
                control_desc = controls[idx].get("description", f"Control {idx}") if idx < len(controls) else f"Control {idx}"
                missing_controls.append(control_desc[:100])

        return {
            "overall_score": int(overall_score),
            "status": overall_status,
            "confidence": avg_confidence,
            "violation_summary": {
                "total_violations": violation_count,
                "critical_violations": critical_violations,
                "auto_non_compliant": critical_violations >= 1 or violation_count >= 3
            },
            "summary": {
                "total_controls": total,
                "compliant": compliant,
                "partially_compliant": partial,
                "non_compliant": non_compliant,
                "compliance_percentage": int((compliant / total) * 100) if total > 0 else 0
            },
            "missing_controls": missing_controls,
            "compliance_percentage": int(compliant / total * 100) if control_scores else 0
        }

    def apply_critical_control_penalties(
        self,
        document_score: Dict[str, any],
        missing_critical_controls: List[str]
    ) -> Dict[str, any]:
        """Apply additional penalties for missing critical controls.
        
        Args:
            document_score: Document scoring result
            missing_critical_controls: List of missing critical controls
            
        Returns:
            Updated document score with critical control penalties
        """
        critical_penalty_per_control = 25
        total_critical_penalty = len(missing_critical_controls) * critical_penalty_per_control
        
        adjusted_score = max(0, document_score["overall_score"] - total_critical_penalty)
        
        # Auto-classify as non-compliant if 3+ critical controls missing
        if len(missing_critical_controls) >= 3:
            adjusted_score = min(adjusted_score, 45)
            adjusted_status = "non_compliant"
        else:
            adjusted_status = document_score["status"]
        
        return {
            "original_score": document_score["overall_score"],
            "critical_controls_missing": len(missing_critical_controls),
            "critical_penalty": total_critical_penalty,
            "adjusted_score": adjusted_score,
            "adjusted_status": adjusted_status,
            "missing_controls_list": missing_critical_controls
        }

    def get_scoring_explanation(self, control_score: Dict[str, any]) -> str:
        """Generate human-readable explanation of scoring including violations.
        
        Args:
            control_score: Score result from calculate_control_score
            
        Returns:
            Formatted explanation string with violation details
        """
        factors = control_score.get("factors", {})
        violations = control_score.get("violations", {})
        
        explanation = f"Score: {control_score['overall_score']}/100\n"
        explanation += f"Status: {control_score['status'].upper()}\n"
        explanation += f"Confidence: {control_score['confidence']:.1%}\n\n"
        
        # Add violation information
        if violations.get("has_violations"):
            explanation += f"Violations Detected: {violations.get('violation_count', 0)}\n"
            explanation += f"Violation Penalty: -{violations.get('penalty', 0)} points\n"
            if violations.get("critical_violation_count", 0) > 0:
                explanation += f"!!CRITICAL: {violations['critical_violation_count']} critical violation(s)\n"
            explanation += "\n"
        
        explanation += "Factor Breakdown:\n"
        for factor_name, factor_data in factors.items():
            explanation += f"  • {factor_name.replace('_', ' ').title()}: "
            explanation += f"{factor_data['score']}/100 "
            explanation += f"({factor_data['weight']:.0%} weight) - "
            explanation += f"{factor_data['explanation']}\n"
        
        if violations.get("has_violations"):
            explanation += f"\nViolation Details:\n"
            for violation in violations.get("violation_patterns", []):
                explanation += f"  • {violation['type']}: {violation['matches']} instance(s)\n"
            
            recommendation = violations.get("recommendations", [])
            if recommendation:
                explanation += f"\nRecommendations:\n"
                for rec in recommendation[:3]:
                    explanation += f"  • {rec}\n"

        return explanation

    def generate_scoring_report(
        self,
        document_text: str,
        controls: List[Dict[str, any]],
        control_scores: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """Generate comprehensive scoring report.
        
        Returns:
            Detailed report with all scoring information
        """
        overall_result = self.calculate_document_score(
            document_text,
            controls,
            control_scores
        )

        # Identify top-scoring and lowest-scoring controls
        sorted_scores = sorted(
            enumerate(control_scores),
            key=lambda x: x[1]["overall_score"],
            reverse=True
        )

        top_controls = sorted_scores[:3]
        weak_controls = sorted_scores[-3:]

        return {
            "overall_result": overall_result,
            "control_details": control_scores,
            "top_performing_controls": [
                {
                    "index": idx,
                    "control_id": controls[idx].get("id", f"control_{idx}"),
                    "score": cs["overall_score"],
                    "status": cs["status"]
                }
                for idx, cs in top_controls
            ],
            "weak_controls": [
                {
                    "index": idx,
                    "control_id": controls[idx].get("id", f"control_{idx}"),
                    "score": cs["overall_score"],
                    "status": cs["status"],
                    "violation_count": cs.get("violations", {}).get("violation_count", 0),
                    "critical_violations": cs.get("violations", {}).get("critical_violation_count", 0),
                    "violation_penalty": cs.get("violation_penalty", 0),
                    "main_issue": self._identify_main_issue(cs),
                    "violation_details": cs.get("violations", {}).get("violation_patterns", [])[:2]
                }
                for idx, cs in weak_controls
            ],
            "scoring_methodology": {
                "weights": self.WEIGHTS,
                "factors": list(self.WEIGHTS.keys()),
                "explanation": "Score calculated as weighted average of 5 independent factors with violation penalties applied",
                "strict_classification": {
                    "compliant_threshold": ">= 80 points AND no violations",
                    "partial_threshold": "50-79 points AND < 30% non-compliant",
                    "non_compliant_threshold": "< 50 points OR violations present"
                }
            }
        }

    def _identify_main_issue(self, control_score: Dict[str, any]) -> str:
        """Identify the main factor limiting the control score."""
        factors = control_score.get("factors", {})
        
        if not factors:
            return "Unknown issue"

        # Find lowest-scoring factor
        min_factor = min(
            factors.items(),
            key=lambda x: x[1]["score"]
        )

        factor_name = min_factor[0].replace("_", " ").title()
        return f"Low {factor_name} ({min_factor[1]['score']}/100)"
