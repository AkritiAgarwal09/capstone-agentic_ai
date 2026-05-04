from __future__ import annotations
from models import ContextResult


def _short_text(value: str, fallback: str, limit: int = 220) -> str:
    text = " ".join((value or "").split()).strip()
    if not text:
        return fallback
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "."


async def fetch_context(
    title: str,
    one_line_summary: str,
    methodology_summary: str,
) -> ContextResult:
    paper_label = _short_text(title, "this paper", 120)
    summary = _short_text(
        one_line_summary,
        "The paper studies a focused research problem and proposes an approach to address it.",
    )
    method = _short_text(
        methodology_summary,
        "The method provides the main evidence for the paper's claimed contribution.",
    )

    return ContextResult(
        field_summary=(
            f"{paper_label} sits in the research area described by its central claim: {summary}"
        ),
        related_papers=[],
        research_gap_addressed=(
            f"The claimed gap is the need for the kind of approach summarized by the paper's method: {method}"
        ),
    )
