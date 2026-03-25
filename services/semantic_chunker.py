"""Semantic chunker for compliance auditing: robust, paragraph-based chunking."""

import re
from typing import List

def chunk_text(text: str, min_tokens: int = 150, max_tokens: int = 300) -> List[str]:
    """
    Split text by paragraphs, then merge into chunks of 150–300 tokens, preserving meaning.
    Returns a list of chunk strings.
    """
    import re
    import sys
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3", trust_remote_code=True)
        def count_tokens(s):
            return len(tokenizer.encode(s, add_special_tokens=False))
    except Exception:
        # Fallback: whitespace token count
        print("[Chunker] WARNING: Using whitespace token count fallback.", file=sys.stderr)
        def count_tokens(s):
            return len(s.split())

    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    chunks = []
    current = ""
    current_tokens = 0
    for p in paragraphs:
        p_tokens = count_tokens(p)
        if current_tokens + p_tokens < max_tokens:
            if current:
                current += "\n" + p
            else:
                current = p
            current_tokens += p_tokens
        else:
            if current:
                chunks.append(current.strip())
            current = p
            current_tokens = p_tokens
    if current:
        chunks.append(current.strip())

    # Merge small trailing chunk if needed
    if len(chunks) > 1 and count_tokens(chunks[-1]) < min_tokens:
        chunks[-2] += "\n" + chunks[-1]
        chunks = chunks[:-1]

    print("===== CHUNKING =====")
    print("CHUNK COUNT:", len(chunks))
    print("FIRST 3 CHUNKS:", chunks[:3])
    if len(chunks) == 1:
        print("ERROR: Chunking failed")
    return chunks
