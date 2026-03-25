from django.test import SimpleTestCase
from unittest.mock import patch

from services.compliance_engine import ComplianceEngine
from services.hybrid_retriever import HybridRetriever
from services.language_analyzer import LanguageAnalyzer


class MultilingualComplianceTests(SimpleTestCase):
    def test_language_detection_detects_french_and_english(self):
        analyzer = LanguageAnalyzer()

        english_text = "The organization must define responsibilities and document procedures."
        french_text = "L'organisation doit définir les responsabilités et documenter les procédures."

        self.assertEqual(analyzer.detect_language(english_text), "en")
        self.assertEqual(analyzer.detect_language(french_text), "fr")

    def test_multilingual_keyword_matching_with_french_text(self):
        engine = ComplianceEngine()
        french_sentence = "Les responsabilités doivent être clairement définies."

        score = engine._compute_keyword_score(["responsibility"], [{"text": french_sentence}])
        self.assertGreater(score, 0.0)

    def test_hybrid_retriever_prioritizes_semantic_similarity(self):
        # The first candidate is a French sentence that should match the English query semantically.
        candidates = [
            {
                "id": "1",
                "metadata": {
                    "document_id": "doc1",
                    "text": "Les responsabilités doivent être clairement définies.",
                },
                "score": 0.9,
            },
            {
                "id": "2",
                "metadata": {
                    "document_id": "doc1",
                    "text": "Un texte non lié sans correspondance.",
                },
                "score": 0.2,
            },
        ]

        class DummyStore:
            def __init__(self, items):
                self.items = items

            def query(self, query_vector, top_k=5):
                return self.items[:top_k]

        store = DummyStore(candidates)
        retriever = HybridRetriever(vector_store=store, embedding_weight=0.6, bm25_weight=0.4, top_k=2)

        # Ensure the retrieval logic uses the embedding score strongly even if BM25 is low due to language mismatch.
        with patch("services.hybrid_retriever.embed_text", return_value=[1.0, 0.0]):
            results = retriever.retrieve(
                "The organization shall define responsibilities",
                document_id="doc1",
                top_k=2,
            )

        self.assertTrue(results)
        self.assertEqual(results[0]["id"], "1")
