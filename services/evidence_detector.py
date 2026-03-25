"""Evidence detection and scoring for compliance requirements.

This module identifies sentences within document chunks that provide evidence
for a compliance requirement, and scores them using a combination of semantic
similarity, keyword match, and strong requirement language.

Evidence score:
    evidence_score = 0.6 * semantic_similarity
                   + 0.2 * keyword_match
                   + 0.2 * strong_language

Evidence types:
    - explicit_requirement
    - responsibility_assignment
    - process_description
    - control_activity
    - approval_statement
"""

import math
import re
from typing import Dict, List, Optional, Tuple

from services.embedding_service import embed_text
from services.keyword_detector import KeywordDetector, keyword_match_score
from services.language_analyzer import LanguageAnalyzer


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    import numpy as np
    a = np.array(vec_a).flatten()
    b = np.array(vec_b).flatten()
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return 0.0
    return float(np.dot(a, b))


class EvidenceDetector:
    """Detects and scores evidence sentences for compliance evaluation."""

    def __init__(self):
        self.language_analyzer = LanguageAnalyzer()
        self.keyword_detector = KeywordDetector()

    def extract_evidence(
        self,
        requirement: str,
        candidate_texts: List[str],
        keywords: Optional[List[str]] = None,
        top_n: int = 3,
    ) -> Dict[str, any]:
        print("===== RULE =====")
        print("RULE TEXT:", requirement)
        print("===== SENTENCES =====")
        all_sentences = []
        for chunk in candidate_texts:
            chunk_sentences = self._split_sentences(chunk)
            all_sentences.extend(chunk_sentences)
        print("TOTAL SENTENCES:", len(all_sentences))
        print("FIRST SENTENCES:", all_sentences[:5])

        if not requirement or not candidate_texts:
            print("ERROR: No requirement or candidate texts for evidence detection")
            return {
                "evidence": [],
                "evidence_sentences": [],
                "evidence_score": 0.0,
                "top_sentence": "",
                "evidence_types": [],
                "detected_keywords": [],
                "keyword_counts": {},
            }

        # Always use BGE query prefix and normalization
        if not requirement.strip().lower().startswith("query:"):
            req_text = "query: " + requirement
        else:
            req_text = requirement
        req_embedding = embed_text(req_text)
        import numpy as np
        if req_embedding is None or (hasattr(req_embedding, 'size') and req_embedding.size == 0):
            print("ERROR: No embedding for requirement")
            return {
                "evidence": [],
                "evidence_sentences": [],
                "evidence_score": 0.0,
                "top_sentence": "",
                "evidence_types": [],
                "detected_keywords": [],
                "keyword_counts": {},
            }

        evidence_items: List[Dict[str, any]] = []

        for chunk in candidate_texts:
            for sentence in self._split_sentences(chunk):
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Always use BGE passage prefix and normalization
                t = sentence.strip()
                if not t.lower().startswith("passage:"):
                    t = "passage: " + t
                sentence_embedding = embed_text(t)
                sem_sim = _cosine_similarity(req_embedding, sentence_embedding)
                # Debug print
                print(f"SIMILARITY: {sem_sim:.3f} | {sentence[:100]}")

                if sem_sim <= 0.0:
                    continue

                keyword_score = keyword_match_score(keywords or [], sentence)
                keyword_detection = self.keyword_detector.detect(keywords or [], sentence)

                lang_info = self.language_analyzer._analyze_sentence_strength(sentence)
                strong_score = lang_info.get("strength_score", 0.0)

                evidence_items.append(
                    {
                        "sentence": sentence,
                        "semantic_similarity": sem_sim,
                        "keyword_score": keyword_score,
                        "matched_keywords": keyword_detection.get("matched_keywords", []),
                        "keyword_counts": keyword_detection.get("keyword_counts", {}),
                        "strong_language_score": strong_score,
                        "evidence_type": _detect_evidence_type(sentence),
                    }
                )

        evidence_items.sort(key=lambda e: e.get("semantic_similarity", 0.0), reverse=True)

        threshold = 0.6
        filtered = [e for e in evidence_items if e.get("semantic_similarity", 0.0) > threshold][:top_n]

        evidence_sentences = [e.get("sentence", "") for e in filtered if e.get("sentence")]
        evidence_score = (
            sum(e.get("semantic_similarity", 0.0) for e in filtered) / len(filtered)
            if filtered
            else 0.0
        )

        detected_keywords = sorted(
            {kw for e in filtered for kw in e.get("matched_keywords", [])}
        )
        keyword_counts = {}
        for e in filtered:
            for kw, count in (e.get("keyword_counts") or {}).items():
                keyword_counts[kw] = keyword_counts.get(kw, 0) + count

        keyword_match_score_value = (
            float(len(detected_keywords)) / len(keywords)
            if keywords else 0.0
        )

        print("===== EVIDENCE =====")
        print("EVIDENCE FOUND:", evidence_sentences)
        print("EVIDENCE COUNT:", len(evidence_sentences))
        if not evidence_sentences:
            print("ERROR: No evidence detected")

        return {
            "evidence": filtered,
            "evidence_sentences": evidence_sentences,
            "evidence_score": evidence_score,
            "top_sentence": evidence_sentences[0] if evidence_sentences else "",
            "evidence_types": list({item.get("evidence_type") for item in filtered}),
            "detected_keywords": detected_keywords,
            "keyword_counts": keyword_counts,
            "keyword_match_score": keyword_match_score_value,
        }

    @staticmethod
    def classify_sentence(sentence: str) -> str:
        s = sentence.lower()
        negative_patterns = ["no", "not", "without", "missing", "not implemented", "may be", "not necessarily", "unclear"]
        positive_patterns = ["is implemented", "is defined", "is maintained", "is reviewed", "is approved"]
        
        if any(p in s for p in negative_patterns):
            return "negative"
        if any(p in s for p in positive_patterns):
            return "positive"
        return "neutral"

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        # Basic sentence splitting; keeps punctuation in results.
        if not text:
            return []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]


def _detect_evidence_type(text: str) -> str:
    """Assign an evidence type based on heuristics."""
    tl = text.lower()
    if re.search(r"\b(must|shall|required|mandatory|needs to|doit|obligatoire|exigé)\b", tl):
        return "explicit_requirement"
    if re.search(r"\b(responsible|accountable|owner|approver|assigned to|responsabilité|responsable)\b", tl):
        return "responsibility_assignment"
    if re.search(r"\b(process|procedure|workflow|step|activity|processus|étape)\b", tl):
        return "process_description"
    if re.search(r"\b(control|monitor|check|verify|audit|contrôle|vérifier|inspect)\b", tl):
        return "control_activity"
    if re.search(r"\b(approved|authorized|signed|endorsed|approuvé|autorisé)\b", tl):
        return "approval_statement"
    return "other"
