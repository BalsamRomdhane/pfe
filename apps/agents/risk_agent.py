"""Agent to detect compliance risks based on audit findings."""

from typing import Dict, List


class RiskAgent:
    """Identifies risk statements based on violations and missing requirements."""

    def detect(self, parsed_document: Dict, compliance_summary: Dict) -> List[str]:
        risks: List[str] = []
        violations = compliance_summary.get("violations", []) or []

        if not parsed_document.get("text"):
            risks.append("Document contains no extracted text. OCR may have failed.")

        if len(violations) > 5:
            risks.append("Multiple controls appear to be missing or insufficient.")

        if "confidential" in (parsed_document.get("text") or "").lower():
            risks.append("Document contains confidential keywords; verify data handling policies.")

        return risks
