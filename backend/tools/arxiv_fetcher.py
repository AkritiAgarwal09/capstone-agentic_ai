from __future__ import annotations
import re
import httpx
from tools.pdf_parser import parse_pdf_bytes


def _clean_id(raw: str) -> str:
    raw = raw.strip()
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+(?:v[0-9]+)?)", raw)
    if m:
        return m.group(1)
    m = re.match(r"^([0-9]+\.[0-9]+(?:v[0-9]+)?)$", raw)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot parse arXiv ID from: {raw!r}")


async def fetch_arxiv_paper(arxiv_input: str) -> dict:
    arxiv_id = _clean_id(arxiv_input)

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        # Metadata from Atom API
        meta_resp = await client.get(
            f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        )
        meta_resp.raise_for_status()
        xml = meta_resp.text

        # Pull title (skip the first "arXiv Query Interface" title tag)
        title = ""
        for t in re.findall(r"<title>([^<]+)</title>", xml):
            if "arxiv" not in t.lower():
                title = t.strip()
                break

        authors = re.findall(r"<name>([^<]+)</name>", xml)

        year: int | None = None
        dm = re.search(r"<published>(\d{4})", xml)
        if dm:
            year = int(dm.group(1))

        abstract = ""
        am = re.search(r"<summary[^>]*>(.*?)</summary>", xml, re.DOTALL)
        if am:
            abstract = am.group(1).strip()

        # Download PDF
        pdf_resp = await client.get(f"https://arxiv.org/pdf/{arxiv_id}")
        pdf_resp.raise_for_status()
        parsed = parse_pdf_bytes(pdf_resp.content)

    return {
        "title": title or parsed["title"],
        "authors": authors,
        "year": year,
        "abstract": abstract or parsed.get("abstract", ""),
        "text": parsed.get("abstract") or parsed.get("text", ""),
        "arxiv_id": arxiv_id,
    }
