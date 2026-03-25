"""Keyword detection utilities.

This module provides keyword detection functionality used for identifying
and scoring keyword occurrences within document text.

It is used to surface which keywords from a compliance control are present in
candidate evidence, and to support explainable keyword-based scoring.
"""

import re
from typing import Dict, List, Tuple

# Multilingual keyword mappings to support English/French keyword matching.
# This is shared with evidence scoring to ensure consistent behavior.
MULTILINGUAL_KEYWORD_MAP: Dict[str, List[str]] = {
    "responsibility": ["responsibility", "responsabilité", "responsabilités"],
    "authority": ["authority", "autorité"],
    "define": ["define", "définir", "définition"],
    "must": ["must", "doit", "devra"],
    "mandatory": ["mandatory", "obligatoire", "obligatoire"],
    "should": ["should", "devrait", "devraient"],
    "may": ["may", "peut"],
    "requirement": ["requirement", "exigence", "obligation"],
}


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = _normalize(text)
    return re.findall(r"\b\w+\b", text)


def _count_occurrences(text: str, pattern: str, word_boundary: bool = True) -> int:
    """Count occurrences of a keyword variant.

    If `word_boundary` is True, the match will only count whole words.
    """
    if not text or not pattern:
        return 0

    flags = re.IGNORECASE
    if word_boundary:
        regex = rf"\b{re.escape(pattern)}\b"
    else:
        regex = re.escape(pattern)

    return len(re.findall(regex, text, flags=flags))


class KeywordDetector:
    """Detects and counts keywords in text."""

    def __init__(self, keyword_map: Dict[str, List[str]] = None):
        self.keyword_map = keyword_map or MULTILINGUAL_KEYWORD_MAP

    def detect_keywords(self, text: str) -> List[str]:
        print("===== KEYWORDS =====")
        print("TEXT SAMPLE:", text[:300])
        detected = []
        for key, variants in self.keyword_map.items():
            for variant in variants:
                if _count_occurrences(text, variant) > 0:
                    detected.append(key)
                    break
        print("KEYWORDS DETECTED:", detected)
        if not detected:
            print("ERROR: No keywords detected")
        return detected

    def _variants_for_keyword(self, keyword: str) -> List[str]:
        if not keyword:
            return []
        key = _normalize(keyword)
        return self.keyword_map.get(key, [key])

    def detect(self, keywords: List[str], text: str) -> Dict[str, any]:
        """Detect which keywords appear in the given text.

        Returns:
            {
                "matched_keywords": [...],  # keywords from the input list that were found
                "keyword_counts": {keyword: count},
                "total_matches": int,
                "matched_variants": {keyword: [found_variant, ...]},
            }
        """

        result = {
            "matched_keywords": [],
            "keyword_counts": {},
            "matched_variants": {},
            "total_matches": 0,
        }

        if not keywords or not text:
            return result

        normalized_text = _normalize(text)

        for keyword in keywords:
            if not keyword:
                continue

            variants = self._variants_for_keyword(keyword)
            total_for_keyword = 0
            matched_variants = []

            for variant in variants:
                # Use word boundaries for single words, otherwise allow substring match
                word_boundary = " " not in variant and "\t" not in variant
                count = _count_occurrences(normalized_text, variant, word_boundary=word_boundary)
                if count > 0:
                    total_for_keyword += count
                    matched_variants.append(variant)

            if total_for_keyword > 0:
                result["matched_keywords"].append(keyword)
                result["keyword_counts"][keyword] = total_for_keyword
                result["matched_variants"][keyword] = matched_variants
                result["total_matches"] += total_for_keyword

        return result


def keyword_match_score(keywords: List[str], text: str) -> float:
    """Compute a normalized keyword match score (0.0-1.0)."""

    if not keywords or not text:
        return 0.0

    detector = KeywordDetector()
    detected = detector.detect(keywords, text)
    if not detected.get("matched_keywords"):
        return 0.0

    return float(len(detected.get("matched_keywords", []))) / len(keywords)
