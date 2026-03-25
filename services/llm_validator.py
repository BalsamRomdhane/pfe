"""LLM validation layer for compliance evidence.

This module sends a requirement and its evidence to an LLM and expects a JSON
response that indicates compliance status, confidence, reason, and the evidence
used.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ai.models import get_llm_model

logger = logging.getLogger(__name__)


class LLMValidationError(Exception):
    pass


class LLMValidator:
    """Validates compliance requirements using an LLM."""

    def __init__(self):
        self._model = get_llm_model()

    def validate(self, rule: Dict[str, Any], evidence_texts: List[str]) -> Dict[str, Any]:
        """Validate a single rule against provided evidence."""
        requirement = rule.get("description") or rule.get("name") or ""
        rule_id = rule.get("id", "")

        # EXPLICIT FALLSAFE: If no evidence is provided, short-circuit immediately.
        if not evidence_texts or all(not e.strip() for e in evidence_texts):
            return {
                "status": "NON_COMPLIANT",
                "confidence": 1.0,
                "reason": "No evidence provided",
                "evidence": [],
                "evidence_used": "",
                "evidence_sentence": "",
            }

        print("===== LLM INPUT =====")
        print("RULE:", requirement)
        print("EVIDENCE:", evidence_texts)

        prompt = self._build_prompt(requirement, rule_id, evidence_texts)

        try:
            # Deterministic generation settings
            output = self._model(
                prompt, 
                max_new_tokens=256, 
                do_sample=False,
                temperature=0.0
            )
            text = output[0].get("generated_text") if isinstance(output, list) else str(output)
            text = text or ""
            print("===== LLM OUTPUT =====")
            print(text)
            
            response = self._parse_json(text)
            return response
        except Exception as ex:
            logger.exception("LLM validation failed: %s", ex)
            # EXPLICIT FALLSAFE: If the LLM throws an error (e.g. timeout), return PARTIAL to avoid crash
            return {
                "status": "PARTIAL",
                "confidence": 0.0,
                "reason": f"LLM Failure: {str(ex)}",
                "evidence": [],
                "evidence_used": "",
                "evidence_sentence": "",
            }

    def _build_prompt(self, requirement: str, rule_id: str, evidence_texts: List[str]) -> str:
        top_evidence = []
        if evidence_texts:
            for i, text in enumerate(evidence_texts):
                if i >= 3: break
                top_evidence.append(text)
        evidence_block = "\n\n".join(top_evidence) if top_evidence else "(no evidence provided)"
        
        if len(requirement) > 300:
            requirement = requirement[:300] + "..."
            
        if len(evidence_block) > 800:
            evidence_block = evidence_block[:800] + " ...[truncated]"

        return (
            "You are a strict compliance auditor AI.\n"
            "Your task is to evaluate whether the provided document evidence satisfies a compliance requirement.\n"
            "You MUST return ONLY a valid JSON object.\n"
            "Do NOT include any explanation, introduction, repetition, or extra text.\n"
            "Do NOT repeat the instructions.\n"
            "Do NOT output anything outside the JSON.\n\n"
            "---\n\n"
            f"### Requirement:\n{requirement}\n\n"
            f"### Evidence:\n{evidence_block}\n\n"
            "---\n\n"
            "### Evaluation guidelines:\n"
            "* COMPLIANT → evidence clearly and directly satisfies the requirement\n"
            "* PARTIAL → evidence partially satisfies or is incomplete / implicit\n"
            "* NON_COMPLIANT → requirement is not satisfied or missing\n"
            "* Use semantic understanding (not keyword matching only)\n"
            "* Be strict and objective\n"
            "* If uncertain → return PARTIAL (never guess COMPLIANT)\n\n"
            "---\n\n"
            "### Output format (STRICT JSON ONLY):\n"
            "{\n"
            '  "status": "COMPLIANT" | "PARTIAL" | "NON_COMPLIANT",\n'
            '  "confidence": number between 0 and 1,\n'
            '  "reason": "short explanation (max 20 words)",\n'
            '  "evidence_used": "exact sentence from evidence"\n'
            "}\n\n"
            "### Rules (MANDATORY):\n"
            "* Output ONLY the JSON object\n"
            "* No markdown\n"
            "* No repetition\n"
            "* No additional keys\n"
            "* No text before or after JSON\n"
            "* Ensure valid JSON (parsable)\n\n"
            "Return ONLY valid JSON. No explanations. No text. No repetition.\n"
        )

    def _parse_json(self, text: str) -> Dict[str, Any]:
        import re
        
        # Extract everything between the first '{' and the last '}'
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            logger.debug("No JSON block found in LLM output. Falling back.")
            return self._parse_freeform(text)

        json_str = match.group(0)

        try:
            parsed = json.loads(json_str)
            
            # Reconstruct the response safely with fallbacks
            return {
                "status": str(parsed.get("status", "NON_COMPLIANT")).upper(),
                "confidence": float(parsed.get("confidence", 0.0) or 0.0),
                "reason": str(parsed.get("reason", "")),
                "evidence_used": str(parsed.get("evidence_used", "")),
                "evidence_sentence": str(parsed.get("evidence_used", "")),
                "evidence": parsed.get("evidence", []) or [parsed.get("evidence_used")] if parsed.get("evidence_used") else [],
            }
        except Exception as ex:
            logger.warning("Failed to parse extracted JSON block: %s | Text: %s", ex, json_str)
            return self._parse_freeform(text)

    def _parse_freeform(self, text: str) -> Dict[str, Any]:
        """Attempt to extract a compliance decision from non-JSON model output."""
        normalized = text.strip().replace("\n", " ")
        upper = normalized.upper()

        # Determine status
        status = "NON_COMPLIANT"
        for candidate in ("COMPLIANT", "PARTIAL", "NON_COMPLIANT"):
            if candidate in upper:
                status = candidate
                break

        # Try to find a confidence value in the output
        confidence = 0.0
        try:
            import re

            match = re.search(r"\b(0\.?\d+|1(?:\.0+)?)\b", normalized)
            if match:
                confidence = float(match.group(1))
                if confidence > 1.0:
                    confidence = min(confidence / 100.0, 1.0)
        except Exception:
            confidence = 0.0

        # Take a short excerpt as reason/evidence
        reason = "".join(normalized.split()[:30])
        evidence_used = "".join(normalized.split()[:30])

        return {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "evidence_used": evidence_used,
            "evidence_sentence": evidence_used,
        }
