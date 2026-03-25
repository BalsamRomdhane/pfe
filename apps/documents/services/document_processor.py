"""Document processing pipeline for OCR, chunking, and embedding generation."""

import logging
import re
from typing import Dict, List

from apps.documents.models import Document
from services.chunking_service import chunk_document
from services.embedding_service import embed_texts
from services.vector_store import VectorStore
from .ocr_service import extract_text_from_file

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    # Add space between lowercase and uppercase
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Add space between words and numbers
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    # Add line breaks before key sections
    text = re.sub(r'(Title|Version|Date|Purpose|Accessibility|Review|Clarity|Protection|Review Cycle|Version Control)', r'\n\1', text)
    return text

def split_sentences(text: str) -> list:
    sentences = re.split(r'[.\n]', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def _is_heading_line(line: str) -> bool:
    """Heuristic to detect section heading lines."""
    if not line or len(line.strip()) < 3:
        return False

    stripped = line.strip()
    # Consider common numbering schemes and short all-caps lines as headings
    if re.match(r"^(\d+\.|\d+\))\s+", stripped):
        return True
    if re.match(r"^[IVXLC]+\.?\s+", stripped):
        return True
    words = stripped.split()
    if len(words) <= 10 and stripped.upper() == stripped and any(c.isalpha() for c in stripped):
        return True

    return False


def split_into_sections(text: str) -> List[Dict[str, str]]:
    """Split text into sections based on headings and blank lines."""
    if not text:
        return []

    lines = text.split("\n")
    sections: List[Dict[str, str]] = []
    current_title = ""
    current_lines: List[str] = []

    def flush_section():
        if not current_lines:
            return
        sections.append({
            "title": current_title.strip(),
            "content": "\n".join(current_lines).strip(),
        })

    for line in lines:
        if _is_heading_line(line):
            # Start a new section when encountering a heading line
            flush_section()
            current_title = line.strip()
            current_lines = []
            continue

        if not line.strip():
            # Blank line can separate paragraphs but not necessarily sections
            current_lines.append("")
            continue

        current_lines.append(line)

    flush_section()
    return sections


def chunk_content(
    text: str,
    chunk_size: int = 200,
    overlap: int = 50,
    section_title: str = "",
    section_index: int = 0,
) -> List[Dict[str, str]]:
    """Chunk a text span into overlapping windows retaining section metadata."""
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    chunks: List[Dict[str, str]] = []
    start = 0
    chunk_index = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunk_text = " ".join(words[start:end]).strip()
        if chunk_text:
            chunks.append(
                {
                    "section_title": section_title,
                    "section_index": section_index,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                }
            )
            chunk_index += 1
        start += chunk_size - overlap

    return chunks


def generate_document_chunks(text: str) -> List[Dict[str, str]]:
    """Generate structured chunks from a full document text."""
    normalized = normalize_text(text)
    sections = split_into_sections(normalized)
    chunks: List[Dict[str, str]] = []

    for section_index, section in enumerate(sections):
        if not section.get("content"):
            continue
        section_chunks = chunk_content(
            section["content"],
            section_title=section.get("title", ""),
            section_index=section_index,
        )
        chunks.extend(section_chunks)

    # If no sections were detected, fallback to simple chunking
    if not chunks and normalized:
        simple_chunks = chunk_content(normalized)
        chunks.extend(simple_chunks)

    return chunks


class DocumentProcessor:
    """Orchestrates document processing and vector indexing."""

    def __init__(self):
        self.vector_store = VectorStore()

    def process(self, document: Document) -> Document:
        """Ingest a document, extract text, normalize, split, debug, chunk, embed, and index."""
        file_path = document.file.path
        raw_text = extract_text_from_file(file_path)
        text = normalize_text(raw_text)
        print("===== NORMALIZED TEXT =====")
        print(text[:500])

        document.text = text
        document.save(update_fields=["text"])

        # Chunking for embedding/indexing (optional, can be improved)
        chunks = chunk_document(text)
        if not chunks:
            return document

        # Use chunks directly for retrieval/evidence
        candidates = [c.get("text", "") for c in chunks]

        print("===== USING CHUNKS =====")
        print("CHUNK COUNT:", len(chunks))
        if chunks:
            print("FIRST CHUNK:", chunks[0].get("text", "")[:200])

        # Remove existing embeddings for this document before re-indexing.
        self.vector_store.delete_document(str(document.id))

        chunk_texts = [c.get("text", "") for c in chunks]
        embeddings = embed_texts(chunk_texts)

        self.vector_store.add_chunks(
            document_id=str(document.id),
            standard_id=str(getattr(document, "standard_id", "")),
            chunks=chunks,
            embeddings=embeddings,
        )

        return document

    def delete_document(self, document: Document) -> None:
        """Delete a document and its associated vectors."""
        self.vector_store.delete_document(str(document.id))
        document.delete()
