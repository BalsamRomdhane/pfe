"""Structural validation engine for governance documents.

Detects whether documents contain basic structural elements required for
good governance such as version, owner, approval, review date, scope, etc.

Returns a structure score (0-100) indicating how complete the document is.
"""

import re
from typing import Dict, List
from datetime import datetime


class StructureValidator:
    """Validates document structure and governance completeness."""

    # Patterns for detecting governance elements
    GOVERNANCE_PATTERNS = {
        "title": {
            "patterns": [
                # Explicit title markers
                r"^\s*(document\s+)?title\s*[:\-]",
                r"^\s*[A-Z][A-Za-z0-9\s\-]{5,}$",  # Likely a heading/title line
                r"^\s*[A-Z][a-z]+(\s+[A-Z][a-z]+){1,5}\s*$",  # Title case line
            ],
            "weight": 0.08,
            "description": "Document title"
        },
        "version": {
            "patterns": [
                r"\bversion\s*[:\-]?\s*\d+(?:\.\d+)*\b",
                r"\bver\s*[:\-]?\s*\d+(?:\.\d+)*\b",
                r"\bv\d+(?:\.\d+)*\b",
                r"\brevision\s*[:\-]?\s*\d+(?:\.\d+)*\b",
            ],
            "weight": 0.08,
            "description": "Version number"
        },
        "owner": {
            "patterns": [
                r"\bowner\s*[:\-]?\s*[A-Za-z]",
                r"\bresponsible\s+(party|officer|for)\s*[:\-]?",
                r"\bauthor\s*[:\-]?\s*[A-Za-z]",
                r"\bsponsor\s*[:\-]?",
                r"\bauthenticated\s+by",
            ],
            "weight": 0.12,
            "description": "Document owner/sponsor"
        },
        "approval": {
            "patterns": [
                r"\bapproval\s*[:\-]?",
                r"\bapproved?\s+(by|on|date)\b",
                r"\bauthorized?\s+(by|on|date)\b",
                r"\bsign(ed)?\s*(by|on|date)\b",
                r"\bapprover\s*[:\-]?",
            ],
            "weight": 0.12,
            "description": "Approval/authorization"
        },
        "effective_date": {
            "patterns": [
                r"\beffective\s+(date|as of)\s*[:\-]?\s*[\d/\-]",
                r"\bin\s+effect\s+(from|on)\s*[\d/\-]",
                r"\beffective\b.*\d{1,2}[\s/\-]\d{1,2}[\s/\-]\d{2,4}",
                r"\bdate\s*[:\-]\s*\d{1,2}[\s/\-]\d{1,2}[\s/\-]\d{2,4}",
                r"\bdate\s*[:\-]\s*[A-Za-z]{3,}\s*\d{1,2},?\s*\d{4}",
                r"\bdated\s*[:\-]?\s*[A-Za-z0-9].*",
            ],
            "weight": 0.10,
            "description": "Effective date"
        },
        "review_date": {
            "patterns": [
                r"\bnext\s+review\s+(date|on)\s*[:\-]?",
                r"\breview\s*[:\-]?\s*date\b",
                r"\breview(ed)?\s+(on|date)\s*[:\-]?\s*[\d/\-]",
                r"\blast\s+review(ed)?\s+(on|date)",
            ],
            "weight": 0.10,
            "description": "Review/renewal date"
        },
        "scope": {
            "patterns": [
                r"\bscope\s*[:\-]",
                r"\bapplies?\s+to",
                r"\bapplicable?\s+to",
                r"\bscope[^.]*\b(includes?|applies?)",
                r"\bthis\s+(policy|document)\s+(applies|applies to)\b",
            ],
            "weight": 0.08,
            "description": "Scope definition"
        },
        "responsibilities": {
            "patterns": [
                r"\bresponsibilit(?:ies|y)\s*[:\-]",
                r"\broles?\s+(?:and\s+)?responsibilit(?:ies|y)",
                r"\bwho\s+is\s+responsible",
                r"\brole\s+definition",
            ],
            "weight": 0.12,
            "description": "Roles and responsibilities"
        },
        "procedures": {
            "patterns": [
                r"\bprocedure\s*[:\-]",
                r"\bprocess(?:es)?\s*[:\-]",
                r"\bsteps?\s*[:\-]",
                r"\bworkflow\s*[:\-]",
            ],
            "weight": 0.10,
            "description": "Procedures/processes"
        },
        "compliance_requirements": {
            "patterns": [
                r"\bmust\s+",
                r"\bshall\s+",
                r"\brequired?\s+",
                r"\bmandatory\b",
            ],
            "weight": 0.10,
            "description": "Compliance requirements"
        }
    }

    def __init__(self):
        self.total_weight = sum(p["weight"] for p in self.GOVERNANCE_PATTERNS.values())

    def validate_structure(self, document_text: str) -> Dict[str, any]:
        """Validate document structure and return detailed report.
        
        Args:
            document_text: Full document text
            
        Returns:
            Dictionary with structure score and detailed findings
        """
        if not document_text:
            return {
                "structure_score": 0,
                "status": "empty",
                "elements_found": [],
                "missing_elements": [],
                "details": {}
            }

        text = document_text
        doc_length = len(document_text)
        elements_found = []
        details = {}

        # Check each governance element
        for element_name, element_config in self.GOVERNANCE_PATTERNS.items():
            found = False

            for pattern in element_config["patterns"]:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    found = True
                    break
            
            details[element_name] = {
                "found": found,
                "weight": element_config["weight"],
                "description": element_config["description"]
            }
            
            if found:
                elements_found.append(element_name)

        # Calculate structure score
        structure_score = self._calculate_structure_score(details)
        
        # Determine missing elements
        missing_elements = [
            elem for elem, config in details.items()
            if not config["found"]
        ]

        # Assess document maturity
        if len(elements_found) >= 7:
            maturity = "mature"
        elif len(elements_found) >= 5:
            maturity = "developing"
        elif len(elements_found) >= 3:
            maturity = "basic"
        else:
            maturity = "minimal"

        # Additional structural checks
        has_sections = len(re.findall(r'^#{1,3}\s+', document_text, re.MULTILINE)) > 0 or \
                      len(re.findall(r'^\d+\.?\s+[A-Z]', document_text, re.MULTILINE)) > 0
        
        has_lists = bool(re.search(r'^[\-\*•]\s+', document_text, re.MULTILINE))
        
        avg_section_length = len(elements_found) > 0 and doc_length / len(elements_found) or 0

        return {
            "structure_score": structure_score,
            "maturity": maturity,
            "elements_found": elements_found,
            "elements_count": len(elements_found),
            "missing_elements": missing_elements,
            "missing_count": len(missing_elements),
            "has_sections": has_sections,
            "has_lists": has_lists,
            "document_length": doc_length,
            "avg_section_length": avg_section_length,
            "details": details,
            "recommendations": self._generate_recommendations(missing_elements)
        }

    def _calculate_structure_score(self, details: Dict[str, Dict]) -> int:
        """Calculate structure score based on found elements."""
        score = 0.0
        
        for element_name, config in details.items():
            if config["found"]:
                # Award points proportional to element weight
                score += config["weight"] * 100

        # Normalize to 0-100
        return int(min(100, score / self.total_weight * 100))

    def _generate_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for missing elements."""
        recommendations = []

        if "title" in missing_elements:
            recommendations.append("Add a clear document title at the beginning")

        if "version" in missing_elements:
            recommendations.append("Include version number (e.g., v1.0, v2.1)")

        if "owner" in missing_elements:
            recommendations.append("Specify the document owner/responsible party")

        if "approval" in missing_elements:
            recommendations.append("Add approval signatures or authorization statements")

        if "effective_date" in missing_elements:
            recommendations.append("Specify when this policy becomes effective")

        if "review_date" in missing_elements:
            recommendations.append("Define review or renewal schedule")

        if "scope" in missing_elements:
            recommendations.append("Clearly define the scope and applicability")

        if "responsibilities" in missing_elements:
            recommendations.append("Define roles and responsibilities for implementation")

        if "procedures" in missing_elements:
            recommendations.append("Document the specific procedures or processes")

        if "compliance_requirements" in missing_elements:
            recommendations.append("Use mandatory language (must, shall, required) for requirements")

        return recommendations

    def check_governance_completeness(self, document_text: str) -> Dict[str, any]:
        """Check how complete the governance elements are.
        
        Returns dictionary with individual element assessments.
        """
        validation = self.validate_structure(document_text)
        
        completeness_by_element = {}
        for element, config in validation["details"].items():
            completeness_by_element[element] = {
                "present": config["found"],
                "importance": config["weight"],
                "description": config["description"]
            }

        return {
            "overall_score": validation["structure_score"],
            "completeness": completeness_by_element,
            "missing_count": len(validation["missing_elements"]),
            "elements_found": len(validation["elements_found"]),
            "percentage_complete": int(len(validation["elements_found"]) / 10 * 100)
        }

    def suggest_document_improvements(self, document_text: str) -> List[str]:
        """Suggest improvements to the document."""
        suggestions = []
        validation = self.validate_structure(document_text)

        # Structural suggestions
        if not validation["has_sections"]:
            suggestions.append("Add clear section headings for better organization")

        if not validation["has_lists"]:
            if len(validation["elements_found"]) > 3:
                suggestions.append("Use bullet points or numbered lists for procedures and responsibilities")

        if validation["document_length"] < 500:
            suggestions.append("Document seems brief; ensure all necessary details are included")

        if validation["document_length"] > 10000:
            suggestions.append("Document is very long; consider breaking into multiple sections")

        # Add recommendations for missing elements
        suggestions.extend(validation["recommendations"])

        return suggestions
