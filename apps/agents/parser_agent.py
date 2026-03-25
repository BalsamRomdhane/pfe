"""Agent responsible for extracting structured information from documents."""

from typing import Dict

from apps.documents.models import Document


class ParserAgent:
    """Extracts structured data from a document."""

    def parse_document(self, document: Document) -> Dict:
        """Parse the document and return a structured representation, preserving structure."""
        raw_text = document.text or ""
        text = raw_text.strip()
        print("===== PARSER OUTPUT =====")
        print("TEXT LENGTH:", len(text))
        print("TEXT PREVIEW:", text[:500])
        print("LINES:", text.split("\n")[:10])
        return {
            "document_id": document.id,
            "text": text,
            "file_name": document.file.name if document.file else None,
        }
