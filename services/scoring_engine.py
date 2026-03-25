"""Compliance scoring engine.

This module provides a deterministic, explainable scoring system that combines
multiple evidence signals into a final compliance score.

The multi-factor scoring approach aims to reduce hallucinations by grounding the
final decision in measurable signals.

Final score formula:
    final_score =
        0.35 * semantic_similarity +
        0.25 * evidence_score +
        0.20 * llm_confidence +
        0.10 * keyword_score +
        0.10 * structure_score

Where each component is in the [0,1] range.
"""

from typing import List, Dict, Any, Optional


def calculate_multi_factor_score(
    rule_evaluations: List[Dict[str, Any]],
    structure_score: float = 0.0,
    missing_elements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute a multi-factor compliance score for a document.

    Args:
        rule_evaluations: A list of rule evaluation dicts containing the signals.
        structure_score: A document-level structure score (0-100).
        missing_elements: Document level missing structural elements.

    Returns:
        A dict containing the overall score, status, and breakdown.
    """
    
    if missing_elements is None:
        missing_elements = []

    if not rule_evaluations:
        return {"score": 0, "status": "NON_COMPLIANT", "breakdown": {}}

    # Normalize structure score to [0,1]
    structure_norm = max(0.0, min(1.0, structure_score / 100.0))

    total_score = 0.0
    count = 0
    breakdown = []

    for evaluation in rule_evaluations:
        semantic_similarity = float(evaluation.get("score", 0.0))
        evidence_score = float(evaluation.get("evidence_score", 0.0))
        llm_confidence = float(evaluation.get("confidence", 0.0))
        keyword_score = float(evaluation.get("rule", {}).get("keyword_score", 0.0))

        # ------------------------------------------------------------------
        # NEW LOGIC: Score MUST be mapped strictly from LLM output status
        # COMPLIANT = 1, PARTIAL = 0.5, NON_COMPLIANT = 0
        # ------------------------------------------------------------------
        # "status" is populated by the LLM response parsed in llm_validator.py
        llm_status = str(evaluation.get("status", "NON_COMPLIANT")).upper()

        if llm_status == "COMPLIANT":
            rule_score = 1.0
        elif llm_status == "PARTIAL":
            rule_score = 0.5
        else:
            rule_score = 0.0

        evaluation["final_score"] = int(rule_score * 100)
        evaluation["final_status"] = llm_status

        total_score += rule_score
        count += 1

        breakdown.append(
            {
                "rule_id": evaluation.get("rule_id"),
                "final_score": evaluation["final_score"],
                "final_status": evaluation["final_status"],
                "semantic_similarity": semantic_similarity,
                "evidence_score": evidence_score,
                "llm_confidence": llm_confidence,
                "keyword_score": keyword_score,
                "structure_score": structure_norm,
            }
        )

    avg_score = (total_score / count) if count else 0.0
    overall_score = int(avg_score * 100)

    # Determine document status based strictly on the aggregated LLM score
    if overall_score >= 100:
        status = "COMPLIANT"
    elif overall_score > 0:
        status = "PARTIAL"
    else:
        status = "NON_COMPLIANT"

    if overall_score >= 90:
        risk_level = "LOW"
    elif overall_score >= 70:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "score": overall_score,
        "status": status,
        "risk_level": risk_level,
        "breakdown": breakdown,
        "components": {
            "structure_score": int(structure_norm * 100),
            "criteria": {
                "semantic_similarity": 0.35,
                "evidence_score": 0.25,
                "llm_confidence": 0.20,
                "keyword_score": 0.10,
                "structure_score": 0.10,
            },
        },
    }
