from __future__ import annotations
from typing import Optional
import httpx
from models import RelatedPaper


async def search_related_papers(query: str, limit: int = 5) -> list[RelatedPaper]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "limit": limit,
                    "fields": "title,authors,year,url,externalIds",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    papers: list[RelatedPaper] = []
    for item in data.get("data", []):
        pid = item.get("paperId", "")
        url = item.get("url") or (
            f"https://www.semanticscholar.org/paper/{pid}" if pid else None
        )
        papers.append(
            RelatedPaper(
                title=item.get("title", "Unknown"),
                authors=[a.get("name", "") for a in item.get("authors", [])],
                year=item.get("year"),
                relevance_reason="",  # agent fills this in during synthesis
                semantic_scholar_url=url,
            )
        )
    return papers


async def get_paper_by_arxiv_id(arxiv_id: str) -> Optional[RelatedPaper]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}",
                params={"fields": "title,authors,year,url"},
            )
            resp.raise_for_status()
            item = resp.json()
    except Exception:
        return None

    return RelatedPaper(
        title=item.get("title", ""),
        authors=[a.get("name", "") for a in item.get("authors", [])],
        year=item.get("year"),
        semantic_scholar_url=item.get("url"),
    )
