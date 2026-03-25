"""Agent that suggests improvements based on audit results."""

from typing import Dict, List


class RecommendationAgent:
    """Generates improvement recommendations from audit analysis."""

    def suggest(self, parsed_document: Dict, compliance_summary: Dict, risks: List[str]) -> List[str]:
        recommendations: List[str] = []
        violations = compliance_summary.get("violations", []) or []

        if not violations:
            recommendations.append("Document appears compliant. Keep maintaining your documentation.")
        else:
            # Violations may be a list of strings or structured dicts.
            viol_texts = []
            for v in violations:
                if isinstance(v, str):
                    viol_texts.append(v[:80] + ("..." if len(v) > 80 else ""))
                elif isinstance(v, dict):
                    # Prefer rule identifier and short description
                    rule_id = v.get("rule_id") or v.get("rule", {}).get("id")
                    desc = v.get("rule", {}).get("description") or v.get("reason") or ""
                    if rule_id:
                        viol_texts.append(f"{rule_id}: {desc[:60]}".strip())
                    else:
                        viol_texts.append(desc[:80])
            recommendations.append(
                "Review the following sections to address missing controls: "
                + ", ".join(viol_texts)
            )

        if risks:
            recommendations.append(
                "Address these risks to strengthen your compliance posture: "
                + ", ".join(risks)
            )

        # General advice
        if "version" not in (parsed_document.get("text") or "").lower():
            recommendations.append("Add a document versioning and change control section.")

        return recommendations
