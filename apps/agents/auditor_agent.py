"""Auditor review agent for compliance assessment verification.

This agent acts as an independent auditor, reviewing the compliance agent's
conclusions and verifying whether the reasoning and evidence justify the result.

If inconsistencies are detected, it adjusts the confidence score.
"""

import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class AuditorAgent:
    """Independent auditor that verifies compliance assessments."""

    def __init__(self):
        pass

    def audit_assessment(
        self,
        control_description: str,
        evidence: List[str],
        llm_reasoning: str,
        initial_score: int,
        initial_status: str
    ) -> Dict[str, any]:
        """Audit a compliance assessment and verify its validity.
        
        Args:
            control_description: The control being evaluated
            evidence: Evidence sentences found in the document
            llm_reasoning: Explanation from the compliance agent
            initial_score: Initial compliance score (0-100)
            initial_status: Initial compliance status
            
        Returns:
            Auditor verdict with adjusted score if needed
        """
        audit_result = {
            "initial_score": initial_score,
            "initial_status": initial_status,
            "auditor_findings": [],
            "inconsistencies": [],
            "confidence_adjustment": 0.0,
            "adjusted_score": initial_score,
            "adjusted_status": initial_status,
            "audit_verdict": "valid",
            "reasoning": []
        }

        # Perform audit checks
        self._check_evidence_sufficiency(
            evidence, 
            initial_score, 
            audit_result
        )
        
        self._check_reasoning_validity(
            control_description,
            evidence,
            llm_reasoning,
            initial_score,
            audit_result
        )
        
        self._check_score_status_alignment(
            initial_score,
            initial_status,
            audit_result
        )
        
        self._check_evidence_contradictions(
            evidence,
            initial_score,
            audit_result
        )

        # Determine audit verdict
        audit_result["audit_verdict"] = self._determine_verdict(audit_result)
        
        # Calculate adjusted score based on findings
        if audit_result["inconsistencies"]:
            adjustment = self._calculate_adjustment(audit_result)
            audit_result["confidence_adjustment"] = adjustment
            audit_result["adjusted_score"] = max(0, min(100, initial_score + adjustment))
        
        # Determine adjusted status
        audit_result["adjusted_status"] = self._determine_status(
            audit_result["adjusted_score"]
        )

        return audit_result

    def verify_evidence_quality(self, evidence: List[str]) -> Dict[str, any]:
        """Verify the quality and relevance of evidence."""
        if not evidence:
            return {
                "has_evidence": False,
                "evidence_count": 0,
                "evidence_quality": "no_evidence",
                "quality_score": 0.0,
                "issues": ["No evidence found"]
            }

        issues = []
        qualities = []

        for sentence in evidence:
            quality = self._assess_evidence_quality(sentence)
            qualities.append(quality["quality_score"])
            
            if quality["issues"]:
                issues.extend(quality["issues"])

        avg_quality = sum(qualities) / len(qualities) if qualities else 0

        if avg_quality >= 0.8:
            evidence_quality = "high"
        elif avg_quality >= 0.6:
            evidence_quality = "medium"
        elif avg_quality >= 0.4:
            evidence_quality = "low"
        else:
            evidence_quality = "very_low"

        return {
            "has_evidence": len(evidence) > 0,
            "evidence_count": len(evidence),
            "average_quality_score": avg_quality,
            "evidence_quality": evidence_quality,
            "examples": evidence[:3],
            "issues": list(set(issues)) if issues else []
        }

    def verify_reasoning_logic(
        self,
        control_description: str,
        evidence: List[str],
        reasoning: str,
        claimed_score: int
    ) -> Dict[str, any]:
        """Verify that reasoning supports the claimed score.
        
        Returns:
            Dictionary with logical consistency assessment
        """
        issues = []
        
        # Check if reasoning mentions evidence
        if evidence and not any(
            term in reasoning.lower() 
            for term in ["evidence", "document", "found", "shows"]
        ):
            issues.append("Reasoning doesn't reference the evidence found")

        # Check if reasoning is specific
        if "unclear" in reasoning.lower() or "ambiguous" in reasoning.lower():
            if claimed_score > 70:
                issues.append("Score is high but reasoning mentions ambiguity/unclear aspects")

        # Check for logical consistency with score
        if claimed_score >= 80:
            required_keywords = ["compliant", "complete", "adequate", "satisf"]
            if not any(kw in reasoning.lower() for kw in required_keywords):
                issues.append("High score (>80) but reasoning lacks affirmative language")
        
        elif claimed_score <= 30:
            if "strong" in reasoning.lower() or "clear" in reasoning.lower():
                issues.append("Low score (<30) but reasoning describes positives")

        is_logical = len(issues) == 0

        return {
            "is_logical": is_logical,
            "consistency_issues": issues,
            "logic_score": max(0.0, 1.0 - len(issues) * 0.2),
            "recommendation": "Valid reasoning" if is_logical else "Review reasoning"
        }

    # Private audit methods

    def _check_evidence_sufficiency(
        self,
        evidence: List[str],
        score: int,
        audit_result: Dict
    ) -> None:
        """Check if evidence is sufficient for the score."""
        if not evidence and score >= 70:
            audit_result["inconsistencies"].append(
                "High score claimed but no evidence found"
            )
            audit_result["confidence_adjustment"] -= 15

        elif len(evidence) < 2 and score >= 80:
            audit_result["inconsistencies"].append(
                "Very high score with minimal evidence (only 1 sentence)"
            )
            audit_result["confidence_adjustment"] -= 10

        elif len(evidence) >= 3 and score <= 30:
            audit_result["inconsistencies"].append(
                "Low score despite substantial evidence (3+ sentences)"
            )
            audit_result["confidence_adjustment"] += 10

        if evidence:
            evidence_quality = self.verify_evidence_quality(evidence)
            audit_result["auditor_findings"].append(
                f"Evidence quality: {evidence_quality['evidence_quality']}"
            )

    def _check_reasoning_validity(
        self,
        control_description: str,
        evidence: List[str],
        reasoning: str,
        score: int,
        audit_result: Dict
    ) -> None:
        """Check if reasoning is logically valid."""
        logic_check = self.verify_reasoning_logic(
            control_description,
            evidence,
            reasoning,
            score
        )

        if not logic_check["is_logical"]:
            audit_result["inconsistencies"].extend(logic_check["consistency_issues"])
            audit_result["confidence_adjustment"] -= len(logic_check["consistency_issues"]) * 5

        audit_result["auditor_findings"].append(
            f"Logic consistency: {logic_check['logic_score']:.0%}"
        )

    def _check_score_status_alignment(
        self,
        score: int,
        status: str,
        audit_result: Dict
    ) -> None:
        """Check if score aligns with declared status."""
        if status == "compliant" and score < 70:
            audit_result["inconsistencies"].append(
                f"Status is 'compliant' but score {score} is below threshold (70)"
            )
            audit_result["confidence_adjustment"] -= 10

        elif status == "non_compliant" and score >= 70:
            audit_result["inconsistencies"].append(
                f"Status is 'non_compliant' but score {score} suggests compliance"
            )
            audit_result["confidence_adjustment"] -= 10

        elif status == "partially_compliant" and not (40 <= score < 80):
            audit_result["inconsistencies"].append(
                f"Status is 'partially_compliant' but score {score} is outside expected range (40-80)"
            )
            audit_result["confidence_adjustment"] -= 5

    def _check_evidence_contradictions(
        self,
        evidence: List[str],
        score: int,
        audit_result: Dict
    ) -> None:
        """Check for contradictions within evidence."""
        if not evidence:
            return

        contradictions_found = False

        for sentence in evidence:
            # Look for negations
            if has_negation(sentence):
                if score >= 75:
                    audit_result["inconsistencies"].append(
                        "Evidence contains negations but score is very high"
                    )
                    contradictions_found = True

        if contradictions_found:
            audit_result["confidence_adjustment"] -= 8

    def _determine_verdict(self, audit_result: Dict) -> str:
        """Determine overall audit verdict."""
        if not audit_result["inconsistencies"]:
            return "valid"
        elif len(audit_result["inconsistencies"]) <= 1:
            return "minor_issues"
        elif len(audit_result["inconsistencies"]) <= 2:
            return "moderate_issues"
        else:
            return "significant_issues"

    def _calculate_adjustment(self, audit_result: Dict) -> float:
        """Calculate score adjustment based on audit findings."""
        adjustment = audit_result["confidence_adjustment"]
        # Ensure adjustment is within reasonable bounds
        return max(-20, min(20, adjustment))

    def _determine_status(self, score: int) -> str:
        """Determine compliance status from score."""
        if score >= 80:
            return "compliant"
        elif score >= 60:
            return "partially_compliant"
        else:
            return "non_compliant"

    def _assess_evidence_quality(self, sentence: str) -> Dict[str, any]:
        """Assess quality of a single evidence sentence."""
        issues = []
        quality_score = 1.0

        # Check sentence length (too short or too long)
        word_count = len(sentence.split())
        if word_count < 5:
            issues.append("Sentence too short")
            quality_score -= 0.3
        elif word_count > 100:
            issues.append("Sentence too long")
            quality_score -= 0.2

        # Check for vague language
        vague_words = ["maybe", "perhaps", "possibly", "unclear", "ambiguous"]
        if any(word in sentence.lower() for word in vague_words):
            issues.append("Contains vague language")
            quality_score -= 0.25

        # Check for specific and concrete language
        if any(word in sentence.lower() for word in ["must", "shall", "required", "specific", "defined"]):
            quality_score += 0.1

        return {
            "quality_score": max(0.0, quality_score),
            "issues": issues
        }


def has_negation(text: str) -> bool:
    """Check if text contains negation."""
    negations = [
        r'\bnot\b', r'\bno\b', r'\bno\b', r'\bnever\b',
        r'\bdon\'t\b', r'\bdoesn\'t\b', r'\bwon\'t\b'
    ]
    return any(re.search(neg, text, re.IGNORECASE) for neg in negations)
