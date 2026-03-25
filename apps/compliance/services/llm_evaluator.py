"""LLM evaluation utilities for compliance decisions.

This module provides a lightweight wrapper around an LLM-based classifier.
It is used to analyze whether document text provides evidence for a requirement
and generate a human-readable rationale for the decision.

The implementation uses HuggingFace transformers zero-shot classification to
avoid requiring an expensive training step.
"""

import logging
from typing import List, Optional, Dict

from django.conf import settings

from ai.models import get_zero_shot_classifier

logger = logging.getLogger(__name__)


class LLMEvaluator:
    """Evaluates compliance requirements using an LLM classification pipeline."""

    DEFAULT_MODEL = "facebook/bart-large-mnli"
    # Use strict labels to match compliance evaluation categories.
    DEFAULT_LABELS = ["COMPLIANT", "PARTIAL", "NON_COMPLIANT"]

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or getattr(settings, "COMPLIANCE_LLM_MODEL", self.DEFAULT_MODEL)
        self._classifier = None

    @property
    def classifier(self):
        if self._classifier is None:
            try:
                self._classifier = get_zero_shot_classifier(self.model_name)
            except Exception as ex:
                logger.warning("Failed to initialize LLM classifier: %s", ex)
                self._classifier = None
        return self._classifier

    def evaluate(self, requirement: str, evidence_texts: List[str]) -> Dict[str, any]:
        """Return a compliance assessment based on the requirement and evidence."""
        if not requirement or not evidence_texts:
            return {
                "status": "missing",
                "confidence": 0.0,
                "reasoning": "No requirement or evidence provided.",
            }

        combined = "\n\n".join(evidence_texts[:3])

        if self.classifier:
            try:
                result = self.classifier(
                    combined,
                    self.DEFAULT_LABELS,
                    hypothesis_template="This text is {} with respect to the requirement.",
                )
                label = (result.get("labels", [None])[0] or "NON_COMPLIANT").upper()
                score = float((result.get("scores", [0.0])[0] or 0.0))
                status = label
                reasoning = (
                    f"LLM assessed evidence as '{label}' with confidence {score:.2f}."
                    f" Requirement snippet: {requirement[:120]}"
                )
                return {"status": status, "confidence": score, "reasoning": reasoning}
            except Exception as ex:  # pragma: no cover
                logger.warning("LLM evaluation failed: %s", ex)

        return {
            "status": "uncertain",
            "confidence": 0.0,
            "reasoning": "LLM evaluation not available; falling back to keyword heuristics.",
        }
