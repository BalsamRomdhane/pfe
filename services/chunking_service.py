"""Semantic chunking utilities.

This module provides a stable, token-aware way to split large documents into
smaller, overlapping chunks suitable for embedding and retrieval.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    if not text:
        return ""

    # Normalize whitespace and line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"[\x00-\x1f\x7f]+", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_into_sections(text: str) -> List[Dict[str, str]]:
    """Split text into logical sections using heading heuristics."""

    def _is_heading_line(line: str) -> bool:
        if not line or len(line.strip()) < 3:
            return False
        stripped = line.strip()
        if re.match(r"^(\d+\.|\d+\))\s+", stripped):
            return True
        if re.match(r"^[IVXLC]+\.?\s+", stripped):
            return True
        words = stripped.split()
        if len(words) <= 10 and stripped.upper() == stripped and any(c.isalpha() for c in stripped):
            return True
        return False

    if not text:
        return []

    lines = text.split("\n")
    sections: List[Dict[str, str]] = []
    current_title = ""
    current_lines: List[str] = []

    def flush_section():
        if not current_lines:
            return
        sections.append({"title": current_title.strip(), "content": "\n".join(current_lines).strip()})

    for line in lines:
        if _is_heading_line(line):
            flush_section()
            current_title = line.strip()
            current_lines = []
            continue

        # Keep blank lines in the section to preserve paragraph boundaries.
        current_lines.append(line)

    flush_section()
    return sections


def _get_tokenizer():
    """Return a tokenizer that can count tokens.

    Uses tiktoken when available; falls back to simple whitespace tokenization.
    """
    try:
        import tiktoken  # type: ignore

        # Use cl100k_base which works for many openai-style models
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def _tokenize(text: str, tokenizer) -> List[int]:
    if tokenizer is None:
        # Fallback: simple whitespace splitting
        return text.split()
    try:
        return tokenizer.encode(text)
    except Exception:
        # Fallback if tokenization fails
        return text.split()


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences, attempting to preserve sentence boundaries.

    This splitter is intentionally lightweight and avoids external dependencies.
    It splits on common sentence-ending punctuation as well as on line breaks to
    ensure documents without punctuation (e.g., bullet lists) still chunk cleanly.
    """

    if not text:
        return []

    # Normalize line endings so we can split reliably.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    sentences: List[str] = []
    # First, split into paragraphs by double newlines to preserve semantic blocks.
    for paragraph in re.split(r"\n{2,}", normalized):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # Split on sentence-ending punctuation, or on single line breaks.
        parts = re.split(r"(?<=[\.!?])\s+|\n+", paragraph)
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    return sentences


def chunk_text(
    text: str,
    chunk_size: int = 250,
    overlap: int = 50,
    section_title: Optional[str] = None,
    section_index: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Chunk text into overlapping token windows.

    Each chunk is represented as a dict containing metadata for traceability.
    This implementation tries to avoid breaking sentences across chunk boundaries.
    """
    if not text:
        return []

    normalized = _normalize_text(text)
    tokenizer = _get_tokenizer()

    # If tokenizer isn't available, fall back to simple whitespace chunks.
    if tokenizer is None:
        token_ids = _tokenize(normalized, None)
        if not token_ids:
            return []
        # Without tokenization, we just split by words and use the last words as overlap.
        chunks: List[Dict[str, any]] = []
        start = 0
        chunk_index = 0
        while start < len(token_ids):
            end = min(len(token_ids), start + chunk_size)
            chunk_text = " ".join(token_ids[start:end])
            chunks.append(
                {
                    "section_title": section_title or "",
                    "section_index": section_index or 0,
                    "chunk_index": chunk_index,
                    "text": chunk_text.strip(),
                    "token_count": end - start,
                }
            )
            chunk_index += 1
            start += chunk_size - overlap
        return chunks

    sentences = _split_into_sentences(normalized)
    if not sentences:
        return []

    chunks: List[Dict[str, any]] = []
    current_chunk_sentences: List[str] = []
    current_chunk_tokens: int = 0
    chunk_index = 0

    def _flush_chunk(overlap_tokens: int = 0):
        nonlocal current_chunk_sentences, current_chunk_tokens, chunk_index
        if not current_chunk_sentences:
            return
        chunk_text = " ".join(current_chunk_sentences).strip()
        token_ids = _tokenize(chunk_text, tokenizer)
        token_count = len(token_ids)
        chunks.append(
            {
                "section_title": section_title or "",
                "section_index": section_index or 0,
                "chunk_index": chunk_index,
                "text": chunk_text,
                "token_count": token_count,
            }
        )
        chunk_index += 1

        # Prepare overlap for the next chunk
        if overlap_tokens > 0 and token_count > 0:
            overlap_ids = token_ids[-min(overlap_tokens, token_count) :]
            overlap_text = tokenizer.decode(overlap_ids)
            current_chunk_sentences = [overlap_text.strip()] if overlap_text else []
            current_chunk_tokens = len(overlap_ids)
        else:
            current_chunk_sentences = []
            current_chunk_tokens = 0

    for sentence in sentences:
        sentence_tokens = _tokenize(sentence, tokenizer)
        sentence_len = len(sentence_tokens)

        # If adding this sentence would exceed the chunk size, flush the current chunk.
        if current_chunk_tokens and current_chunk_tokens + sentence_len > chunk_size:
            _flush_chunk(overlap_tokens=overlap)

        current_chunk_sentences.append(sentence)
        current_chunk_tokens += sentence_len

        # If a single sentence is longer than chunk_size, force flush to avoid infinite loops.
        if current_chunk_tokens >= chunk_size and len(current_chunk_sentences) == 1:
            _flush_chunk(overlap_tokens=overlap)

    # Flush remaining sentences as a final chunk
    _flush_chunk(overlap_tokens=0)

    return chunks


def clean_text(text: str) -> str:
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return text.strip()


def chunk_document(text: str, chunk_size: int = 250, overlap: int = 50) -> List[Dict[str, Any]]:
    """Split a document into semantic chunks by sections."""
    sections = _split_into_sections(text)
    
    # If no sections could be detected, treat the whole document as one section
    if not sections:
        sections = [{"title": "General", "content": text}]
        
    chunks = []
    chunk_index = 0
    
    for sec_idx, section in enumerate(sections):
        cleaned_content = clean_text(section["content"])
        if not cleaned_content:
            continue
            
        chunks.append({
            "section_title": clean_text(section["title"]),
            "section_index": sec_idx,
            "chunk_index": chunk_index,
            "text": cleaned_content,
            "token_count": len(cleaned_content.split()),
        })
        print(f"[Chunking] Section '{chunks[-1]['section_title']}' mapped to chunk {chunk_index} (tokens={chunks[-1]['token_count']})")
        chunk_index += 1
        
    print(f"[Chunking] CHUNK COUNT: {len(chunks)}")
    if chunks:
        print("[Chunking] FIRST CHUNK:", chunks[0]["text"][:200])
    return chunks
