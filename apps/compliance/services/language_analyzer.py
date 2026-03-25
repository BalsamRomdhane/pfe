"""Policy language strength detection for compliance documents.

Analyzes the language used in compliance documents to determine whether
requirements are strong, weak, or ambiguous.

Strong language (must, shall, required) indicates mandatory compliance.
Weak language (should, recommended, may) indicates optional compliance.
"""

import re
from typing import Dict, List, Tuple
from collections import Counter


class LanguageAnalyzer:
    """Analyzes language strength in compliance documents."""

    # Language classifications
    STRONG_LANGUAGE = {
        # English
        'must': 1.0,
        'shall': 1.0,
        'required': 1.0,
        'mandatory': 1.0,
        'must not': 0.95,
        'shall not': 0.95,
        'will': 0.9,
        'must be': 0.95,
        # French
        'doit': 1.0,
        'obligatoire': 1.0,
        'exigé': 1.0,
        'doit pas': 0.95,
        'sera': 0.9,
    }

    WEAK_LANGUAGE = {
        # English
        'should': 0.3,
        'may': 0.2,
        'can': 0.25,
        'might': 0.15,
        'could': 0.25,
        'recommended': 0.3,
        'suggest': 0.25,
        'consider': 0.2,
        'optional': 0.1,
        'possible': 0.2,
        'preferred': 0.35,
        # French
        'devrait': 0.3,
        'peut': 0.2,
        'recommandé': 0.3,
        'suggeré': 0.25,
    }

    RESPONSIBILITY_WORDS = {
        'responsible': 1.0,
        'accountable': 1.0,
        'owner': 0.9,
        'responsible party': 1.0,
        'approver': 0.85,
        'approves': 0.8,
        'reviews': 0.75,
        'verifies': 0.8,
    }

    def __init__(self):
        pass

    def analyze_language_strength(self, document_text: str) -> Dict[str, any]:
        """Analyze the overall language strength in a document.
        
        Returns:
            Dictionary with language strength metrics
        """
        if not document_text:
            return self._empty_analysis()

        sentences = self._split_sentences(document_text)
        
        if not sentences:
            return self._empty_analysis()

        # Analyze each sentence
        sentence_scores = []
        strong_sentences = []
        weak_sentences = []
        ambiguous_sentences = []

        for sentence in sentences:
            strength = self._analyze_sentence_strength(sentence)
            sentence_scores.append(strength)
            
            if strength["classification"] == "strong":
                strong_sentences.append(sentence)
            elif strength["classification"] == "weak":
                weak_sentences.append(sentence)
            elif strength["classification"] == "ambiguous":
                ambiguous_sentences.append(sentence)

        # Calculate overall metrics
        avg_strength = sum(s["strength_score"] for s in sentence_scores) / len(sentence_scores) if sentence_scores else 0
        
        # Classify document language
        if avg_strength >= 0.7:
            language_type = "strong_mandatory"
        elif avg_strength >= 0.5:
            language_type = "balanced"
        elif avg_strength >= 0.3:
            language_type = "weak_optional"
        else:
            language_type = "ambiguous"

        # Count keywords
        strong_count = sum(1 for s in sentence_scores if s["classification"] == "strong")
        weak_count = sum(1 for s in sentence_scores if s["classification"] == "weak")
        ambiguous_count = sum(1 for s in sentence_scores if s["classification"] == "ambiguous")

        return {
            "overall_strength": avg_strength,
            "language_type": language_type,
            "sentence_count": len(sentences),
            "strong_sentences_count": strong_count,
            "weak_sentences_count": weak_count,
            "ambiguous_sentences_count": ambiguous_count,
            "strong_percentage": int(strong_count / len(sentences) * 100) if sentences else 0,
            "weak_percentage": int(weak_count / len(sentences) * 100) if sentences else 0,
            "strong_examples": strong_sentences[:3],
            "weak_examples": weak_sentences[:3],
            "language_quality_score": int(avg_strength * 100),
            "recommendations": self._language_recommendations(language_type, avg_strength)
        }

    def find_requirements(self, document_text: str) -> List[Dict[str, any]]:
        """Find all requirement statements in the document.
        
        Returns:
            List of requirement sentences with strength assessment
        """
        if not document_text:
            return []

        sentences = self._split_sentences(document_text)
        requirements = []

        for sentence in sentences:
            strength = self._analyze_sentence_strength(sentence)
            
            # Only include sentences with strong or balanced language
            if strength["strength_score"] >= 0.3:
                requirements.append({
                    "text": sentence,
                    "strength": strength["strength_score"],
                    "classification": strength["classification"],
                    "keywords": strength["keywords_found"],
                    "is_mandatory": strength["is_mandatory"]
                })

        return requirements

    def find_procedures_and_steps(self, document_text: str) -> List[Dict[str, any]]:
        """Extract procedure/process statements.
        
        Returns:
            List of procedure statements
        """
        if not document_text:
            return []

        sentences = self._split_sentences(document_text)
        procedures = []

        for sentence in sentences:
            # Look for procedure keywords and action verbs
            if re.search(r'\b(step|procedure|process|workflow|activity|task)\b', sentence, re.IGNORECASE):
                strength = self._analyze_sentence_strength(sentence)
                procedures.append({
                    "text": sentence,
                    "strength": strength["strength_score"],
                    "has_responsibility": self._has_responsibility_words(sentence)
                })

        return procedures

    def find_responsibility_statements(self, document_text: str) -> List[Dict[str, any]]:
        """Extract responsibility and accountability statements.
        
        Returns:
            List of responsibility assignments
        """
        if not document_text:
            return []

        sentences = self._split_sentences(document_text)
        responsibilities = []

        for sentence in sentences:
            if self._has_responsibility_words(sentence):
                strength = self._analyze_sentence_strength(sentence)
                responsibilities.append({
                    "text": sentence,
                    "strength": strength["strength_score"],
                    "keywords": strength["keywords_found"]
                })

        return responsibilities

    def language_compliance_score(self, document_text: str) -> int:
        """Generate a language compliance score (0-100).
        
        Higher score = clearer, more enforceable requirements
        """
        analysis = self.analyze_language_strength(document_text)
        
        # Base score from language strength
        base_score = analysis["language_quality_score"]
        
        # Bonus for high proportion of strong language
        if analysis["strong_percentage"] >= 60:
            base_score = min(100, base_score + 10)
        
        # Penalty for high proportion of weak language
        if analysis["weak_percentage"] >= 40:
            base_score = max(0, base_score - 10)

        # Penalty for ambiguous language
        if analysis["ambiguous_sentences_count"] > len(self._split_sentences(document_text)) * 0.5:
            base_score = max(0, base_score - 15)

        return int(base_score)

    # Private helper methods

    def _analyze_sentence_strength(self, sentence: str) -> Dict[str, any]:
        """Analyze the language strength of a single sentence."""
        if not sentence:
            return {
                "strength_score": 0.0,
                "classification": "unknown",
                "keywords_found": [],
                "is_mandatory": False
            }

        sentence_lower = sentence.lower()
        strength_score = 0.5  # Default baseline (neutral)
        keywords_found = []
        is_mandatory = False

        # Check for strong language
        for keyword, weight in self.STRONG_LANGUAGE.items():
            if keyword in sentence_lower:
                strength_score = max(strength_score, weight)
                keywords_found.append(keyword)
                is_mandatory = True

        # Check for weak language
        for keyword, weight in self.WEAK_LANGUAGE.items():
            if keyword in sentence_lower:
                strength_score = min(strength_score, weight)
                keywords_found.append(keyword)
                is_mandatory = False

        # Classify based on score
        if strength_score >= 0.7:
            classification = "strong"
        elif strength_score <= 0.35:
            classification = "weak"
        else:
            classification = "ambiguous"

        return {
            "strength_score": strength_score,
            "classification": classification,
            "keywords_found": list(set(keywords_found)),
            "is_mandatory": is_mandatory
        }

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _has_responsibility_words(self, sentence: str) -> bool:
        """Check if sentence contains responsibility-related words."""
        sentence_lower = sentence.lower()
        return any(word in sentence_lower for word in self.RESPONSIBILITY_WORDS.keys())

    def _language_recommendations(self, language_type: str, avg_strength: float) -> List[str]:
        """Generate recommendations based on language analysis."""
        recommendations = []

        if language_type == "strong_mandatory":
            recommendations.append("Language is clear and mandatory. Good compliance clarity.")

        elif language_type == "balanced":
            recommendations.append("Language is balanced. Consider clarifying which items are mandatory vs. recommended.")
            if avg_strength < 0.6:
                recommendations.append("Increase use of 'must' and 'shall' for critical requirements.")

        elif language_type == "weak_optional":
            recommendations.append("Language is mostly optional. Clarify which requirements are mandatory.")
            recommendations.append("Replace 'should' and 'may' with 'must' or 'shall' for enforceable requirements.")

        elif language_type == "ambiguous":
            recommendations.append("Language is unclear and ambiguous. Rewrite for clarity.")
            recommendations.append("Use consistent terminology and mandatory language for all requirements.")

        return recommendations

    def _empty_analysis(self) -> Dict[str, any]:
        """Return empty analysis structure."""
        return {
            "overall_strength": 0.0,
            "language_type": "empty",
            "sentence_count": 0,
            "strong_sentences_count": 0,
            "weak_sentences_count": 0,
            "ambiguous_sentences_count": 0,
            "strong_percentage": 0,
            "weak_percentage": 0,
            "strong_examples": [],
            "weak_examples": [],
            "language_quality_score": 0,
            "recommendations": ["Document is empty or cannot be analyzed"]
        }
