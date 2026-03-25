
"""Semantic document chunking based on document structure.

Instead of fixed-size chunks, this module intelligently chunks documents
based on structural elements like:
- Sections and subsections
- Paragraphs
- Lists
- Tables

This improves context preservation and makes evidence extraction more accurate.
"""

import re
from typing import List, Dict, Tuple, Optional
from enum import Enum

from services.chunking_service import chunk_document


class ChunkType(Enum):
    """Enumeration of chunk types."""
    TITLE = "title"
    HEADING = "heading"
    SUBHEADING = "subheading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    PROCEDURE = "procedure"
    RESPONSIBILITY = "responsibility"
    POLICY = "policy"
    REVIEW = "review"
    UNKNOWN = "unknown"


class SemanticChunker:
    """Intelligently chunks documents based on semantic structure."""

    def __init__(self, min_chunk_size: int = 150, max_chunk_size: int = 300):
        """Initialize semantic chunker.

        Args:
            min_chunk_size: Minimum tokens per chunk (approximate)
            max_chunk_size: Maximum tokens per chunk (approximate)
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> List[Dict[str, any]]:
        """Chunk document into semantic blocks using token-aware chunking.

        This method uses document structure (headings, paragraphs, line breaks)
        and token-based limits (150-300 tokens) to create meaningful chunks that
        can be embedded and searched efficiently.
        """
        if not text:
            return []

        chunk_size = chunk_size or self.max_chunk_size
        overlap = overlap if overlap is not None else int(chunk_size * 0.2)

        # Split into paragraphs first to ensure larger documents are broken into
        # multiple chunks even when there are no explicit section headings.
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        raw_chunks: List[Dict[str, any]] = []
        if len(paragraphs) <= 1:
            raw_chunks = chunk_document(text, chunk_size=chunk_size, overlap=overlap)
        else:
            for section_index, paragraph in enumerate(paragraphs):
                section_chunks = chunk_document(
                    paragraph,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
                # Ensure section indexing is preserved for traceability.
                for c in section_chunks:
                    c["section_index"] = section_index
                raw_chunks.extend(section_chunks)

        # If the document is still treated as a single chunk but contains
        # multiple lines, create additional chunks based on line breaks.
        if len(raw_chunks) <= 1 and text.count("\n") > 0:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if len(lines) > 1:
                raw_chunks = []
                for idx, line in enumerate(lines):
                    raw_chunks.append(
                        {
                            "chunk_index": idx,
                            "section_title": "",
                            "section_index": idx,
                            "text": line,
                            "token_count": len(line.split()),
                        }
                    )

        chunks: List[Dict[str, any]] = []
        for c in raw_chunks:
            content = str(c.get("text", "")).strip()
            if not content:
                continue

            section_title = str(c.get("section_title", ""))
            token_count = int(c.get("token_count") or len(content.split()))

            chunks.append(
                {
                    "content": content,
                    "type": section_title or "paragraph",
                    "size": token_count,
                    "lines": content.count("\n") + 1,
                    "chunk_index": c.get("chunk_index"),
                    "section_index": c.get("section_index"),
                }
            )

        return chunks

    def chunk_with_overlap(self, text: str, overlap: int = 2, chunk_size: Optional[int] = None) -> List[Dict[str, any]]:
        """Chunk document with semantic overlap for context preservation."""
        if not text:
            return []

        return self.chunk(text, chunk_size=chunk_size, overlap=overlap)

    # Private helpers

    def _normalize_lines(self, text: str) -> List[str]:
        """Normalize and clean document lines."""
        # Normalize line endings
        text = re.sub(r'\r\n?', '\n', text)
        # Remove multiple consecutive blank lines
        text = re.sub(r'\n\n+', '\n\n', text)
        return text.split('\n')

    def _detect_line_type(self, line: str) -> ChunkType:
        """Detect the semantic type of a line."""
        line = line.strip()
        
        if not line:
            return ChunkType.UNKNOWN

        # Title (usually short, all caps or title case at start of doc)
        if line.isupper() and len(line.split()) <= 5:
            return ChunkType.TITLE

        # Heading (lines ending with colon or all caps)
        if line.endswith(':') or (line.isupper() and len(line.split()) <= 4):
            return ChunkType.HEADING

        # Subheading (1-2 digit prefix like "1.2.3")
        if re.match(r'^\d+(\.\d+)*\s+', line):
            return ChunkType.SUBHEADING

        # List items (start with -, *, •, or numbers)
        if re.match(r'^[\-\*•]\s+', line) or re.match(r'^\d+\)\s+', line):
            return ChunkType.LIST

        # Procedure keywords
        if any(word in line.lower() for word in ['step', 'procedure', 'process', 'workflow']):
            return ChunkType.PROCEDURE

        # Responsibility keywords
        if any(word in line.lower() for word in ['responsible', 'accountable', 'owner', 'approver']):
            return ChunkType.RESPONSIBILITY

        # Policy keywords
        if any(word in line.lower() for word in ['policy', 'standard', 'guideline', 'requirement']):
            return ChunkType.POLICY

        # Review keywords
        if any(word in line.lower() for word in ['review', 'audit', 'check', 'assessment']):
            return ChunkType.REVIEW

        # Table detection (contains pipes or multiple spaces)
        if '|' in line or re.search(r'\s{2,}', line):
            return ChunkType.TABLE

        return ChunkType.PARAGRAPH

    def extract_sections(self, text: str) -> Dict[str, List[str]]:
        """Extract key sections from document.
        
        Returns:
            Dictionary mapping section type to list of content
        """
        sections = {
            "title": [],
            "scope": [],
            "policy": [],
            "procedures": [],
            "responsibilities": [],
            "review": [],
            "other": []
        }

        chunks = self.chunk(text)
        
        for chunk in chunks:
            chunk_type = chunk["type"]
            content = chunk["content"]
            
            if chunk_type == "title":
                sections["title"].append(content)
            elif "procedure" in content.lower() or chunk_type == "procedure":
                sections["procedures"].append(content)
            elif "responsible" in content.lower() or chunk_type == "responsibility":
                sections["responsibilities"].append(content)
            elif "review" in content.lower() or chunk_type == "review":
                sections["review"].append(content)
            elif "scope" in content.lower():
                sections["scope"].append(content)
            elif "policy" in content.lower() or chunk_type == "policy":
                sections["policy"].append(content)
            else:
                sections["other"].append(content)

        return {k: v for k, v in sections.items() if v}

    def estimate_chunk_quality(self, chunk: Dict[str, any]) -> float:
        """Estimate quality score of a chunk (0-1).
        
        Better quality = more likely to contain relevant information
        """
        score = 0.5  # Base score

        # Prefer structured types
        structured_types = ["heading", "subheading", "procedure", "responsibility", "policy"]
        if chunk["type"] in structured_types:
            score += 0.2

        # Prefer medium-length chunks (not too short, not too long)
        if self.min_chunk_size < chunk["size"] < self.max_chunk_size * 0.8:
            score += 0.2

        # Prefer chunks with multiple lines (more complete context)
        if chunk["lines"] >= 3:
            score += 0.1

        return min(1.0, score)
