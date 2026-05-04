from __future__ import annotations
import re
import fitz  # PyMuPDF


def normalize_arxiv_id(value: str) -> str:
    value = value.strip()
    match = re.search(r"([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?", value)
    if not match:
        raise ValueError(f"Cannot normalize arXiv ID from: {value!r}")
    return match.group(1)


def extract_arxiv_id_from_text(text: str) -> str | None:
    patterns = [
        r"arXiv\s*:\s*([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)",
        r"\b([0-9]{4}\.[0-9]{4,5}v[0-9]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return normalize_arxiv_id(match.group(1))
    return None


def _fix_ligatures(text: str) -> str:
    """Fix common academic PDF ligature artifacts and formatting."""
    for src, dst in [("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")]:
        text = text.replace(src, dst)
    # Rejoin hyphenated line-breaks (word-\nword → wordword)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _extract_abstract(text: str) -> str:
    """
    Extract only the abstract section from academic paper text.
    Tries several heading patterns and falls back to the first ~1500 chars.
    """
    # Normalise for matching (keep original for extraction)
    normalised = text.replace("\r\n", "\n")

    # Pattern: find "Abstract" heading and capture until the next major section
    abstract_pattern = re.compile(
        r"(?:^|\n)\s*Abstract\s*\n+(.*?)(?=\n\s*(?:1\.?\s+Introduction|Keywords?|Index Terms|1\s+Introduction|\n{2,}[A-Z][^\n]{0,60}\n)|$)",
        re.IGNORECASE | re.DOTALL,
    )
    match = abstract_pattern.search(normalised)
    if match:
        abstract = match.group(1).strip()
        if len(abstract) > 100:          # sanity-check: avoid empty captures
            return abstract[:4000]

    # Fallback: look for "Abstract—" or "Abstract:" inline (IEEE / ACM style)
    inline_pattern = re.compile(
        r"Abstract[—:\-]\s*(.*?)(?=\n\s*(?:Index Terms|Keywords?|I\.\s+Introduction|1\.?\s+Introduction)|$)",
        re.IGNORECASE | re.DOTALL,
    )
    match = inline_pattern.search(normalised)
    if match:
        abstract = match.group(1).strip()
        if len(abstract) > 100:
            return abstract[:4000]

    # Last resort: return the first 1500 characters (likely title + abstract area)
    return normalised[:1500].strip()


def parse_pdf_bytes(pdf_bytes: bytes) -> dict:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count

    # Only read the first 4 pages — abstract is always near the start
    pages_to_read = min(4, num_pages)
    raw_text = ""
    for i in range(pages_to_read):
        raw_text += doc[i].get_text()
    doc.close()

    raw_text = _fix_ligatures(raw_text)

    # Heuristic: first non-empty line longer than 20 chars is probably the title
    title = ""
    for line in raw_text.split("\n"):
        line = line.strip()
        if len(line) > 20:
            title = line[:200]
            break

    abstract = _extract_abstract(raw_text)

    return {
        "title": title,
        "num_pages": num_pages,
        "text": abstract,   # downstream agents receive only the abstract
        "abstract": abstract,
        "raw_text": raw_text,
    }
