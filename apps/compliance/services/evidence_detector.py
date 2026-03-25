"""Evidence detection layer for compliance analysis.

This module extracts concrete evidence from documents that supports or contradicts
compliance with specific controls. Evidence is extracted using keyword matching,
semantic similarity, and structural pattern detection.
"""

import re
from typing import Dict, List, Optional
from apps.rag.embedding_service import get_embedding_service


class EvidenceDetector:
    """Detects evidence in documents related to specific compliance controls."""

    def __init__(self):
        self.embedding_service = get_embedding_service()

    def extract_evidence(
        self, 
        document_text: str, 
        control_description: str,
        top_k: int = 5
    ) -> Dict[str, any]:
        """Extract evidence sentences from document related to a control.
        
        Args:
            document_text: Full document text
            control_description: Description of the control to evaluate
            top_k: Number of evidence sentences to extract
            
        Returns:
            Dictionary with evidence sentences, keywords found, and confidence score
        """
        if not document_text or not control_description:
            return {
                "control": control_description[:100],
                "evidence": [],
                "keywords_found": [],
                "confidence": 0.0,
                "evidence_type": "none"
            }

        sentences = self._split_sentences(document_text)
        if not sentences:
            return {
                "control": control_description[:100],
                "evidence": [],
                "keywords_found": [],
                "confidence": 0.0,
                "evidence_type": "none"
            }

        # Extract keywords from control description
        keywords = self._extract_keywords(control_description)
        
        # Rank sentences by relevance
        scored_sentences = []
        for sentence in sentences:
            score = self._score_sentence(sentence, control_description, keywords)
            if score > 0:
                scored_sentences.append((sentence, score))

        # Sort by relevance score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Collect evidence
        evidence_sentences = [sent for sent, _ in scored_sentences[:top_k]]
        found_keywords = [kw for kw in keywords if any(kw.lower() in sent.lower() for sent in evidence_sentences)]
        
        # Calculate overall confidence
        confidence = 0.0
        if evidence_sentences:
            avg_score = sum(score for _, score in scored_sentences[:top_k]) / len(scored_sentences[:top_k])
            confidence = min(1.0, avg_score)

        evidence_type = self._classify_evidence_type(evidence_sentences, keywords)

        return {
            "control": control_description[:100],
            "evidence": evidence_sentences,
            "keywords_found": list(set(found_keywords)),
            "keyword_matches": len(found_keywords),
            "confidence": confidence,
            "evidence_type": evidence_type,
            "total_sentences_analyzed": len(sentences)
        }

    def extract_policy_procedures(self, document_text: str) -> List[str]:
        """Extract sentences containing procedures, responsibilities, and requirements.
        
        Returns:
            List of sentences containing policy procedures
        """
        if not document_text:
            return []

        sentences = self._split_sentences(document_text)
        
        # Patterns that indicate procedures/requirements
        procedure_patterns = [
            r'\b(must|shall|required|mandatory)\b',
            r'\b(responsible|responsible for|responsible party)\b',
            r'\b(procedure|process|step|workflow)\b',
            r'\b(owner|accountable|approval|authoriz)\b',
            r'\b(review|audit|check|verif)\b',
        ]

        procedures = []
        for sentence in sentences:
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in procedure_patterns):
                procedures.append(sentence)

        return procedures

    def detect_missing_evidence(
        self,
        document_text: str,
        control_description: str,
        required_keywords: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """Detect what evidence is missing for a control.
        
        Args:
            document_text: Document text to analyze
            control_description: Control being checked
            required_keywords: Keywords that should be present
            
        Returns:
            Dictionary with missing elements and gaps
        """
        if required_keywords is None:
            required_keywords = self._extract_keywords(control_description)

        document_lower = document_text.lower()
        missing_keywords = []
        
        for keyword in required_keywords:
            if keyword.lower() not in document_lower:
                missing_keywords.append(keyword)

        # Check for common missing elements in governance documents
        missing_elements = []
        
        governance_elements = {
            "version": r'\b(version|v\d+\.\d+)\b',
            "approval": r'\b(approv\w*|sign\w*|authoriz\w*)\b',
            "review_date": r'\b(review|reviewed|last.*review|next.*review)\b',
            "owner": r'\b(owner|sponsor|responsible|approver)\b',
            "scope": r'\b(scope|applies.*to|applicab\w*)\b',
            "effective_date": r'\b(effective|in.*effect|until|valid)\b',
        }

        for element, pattern in governance_elements.items():
            if not re.search(pattern, document_lower):
                missing_elements.append(element)

        return {
            "control": control_description[:100],
            "missing_keywords": missing_keywords,
            "missing_elements": missing_elements,
            "gaps_count": len(missing_keywords) + len(missing_elements),
            "completeness_ratio": max(0.0, 1.0 - (len(missing_keywords) + len(missing_elements)) / 
                                       (len(required_keywords) + len(governance_elements)))
        }

    # Private helper methods

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from control description."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'be', 'been', 'being',
            'have', 'has', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'shall', 'can', 'if', 'as', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }

        # Extract words with 3+ characters
        words = re.findall(r'\b\w{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        # Return top 10 most common keywords
        from collections import Counter
        return [word for word, _ in Counter(keywords).most_common(10)]

    def _score_sentence(self, sentence: str, control_text: str, keywords: List[str]) -> float:
        """Score a sentence's relevance to a control."""
        score = 0.0
        
        # Keyword matches (0.3)
        keyword_matches = sum(1 for kw in keywords if kw.lower() in sentence.lower())
        score += min(0.3, keyword_matches * 0.05)
        
        # Control-specific terms (0.3)
        control_keywords = self._extract_keywords(control_text)
        control_matches = sum(1 for kw in control_keywords if kw.lower() in sentence.lower())
        score += min(0.3, control_matches * 0.05)
        
        # Strong compliance language (0.2)
        strong_language = ['must', 'shall', 'required', 'mandatory', 'responsibility', 'owner']
        if any(word in sentence.lower() for word in strong_language):
            score += 0.2
        
        # Sentence length (not too short) (0.2)
        if 15 < len(sentence.split()) < 150:
            score += 0.2
        
        return min(1.0, score)

    def _classify_evidence_type(self, sentences: List[str], keywords: List[str]) -> str:
        """Classify the type of evidence found."""
        if not sentences:
            return "none"
        
        combined_text = " ".join(sentences).lower()
        
        if any(word in combined_text for word in ['must', 'shall', 'required', 'mandatory']):
            return "explicit_requirement"
        elif any(word in combined_text for word in ['responsibility', 'responsible', 'owner', 'accountable']):
            return "responsibility_assignment"
        elif any(word in combined_text for word in ['review', 'audit', 'check', 'verify', 'assess']):
            return "control_activity"
        elif any(word in combined_text for word in ['procedure', 'process', 'step', 'workflow']):
            return "process_documentation"
        elif any(word in combined_text for word in ['should', 'recommended', 'may', 'can']):
            return "weak_recommendation"
        else:
            return "indirect_evidence"
