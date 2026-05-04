from __future__ import annotations
import asyncio
from models import FullAnalysis, DecomposedPaper, ContextResult, CriticResult
from agents.decomposer import decompose_paper
from agents.context_fetcher import fetch_context
from agents.critic import critique_paper


async def run_full_analysis(
    paper_text: str,
    title: str = "",
    authors: list[str] | None = None,
    year: int | None = None,
) -> FullAnalysis:
    # Step 1: decompose; downstream agents need its output.
    decomposition = await decompose_paper(paper_text, title, authors or [], year)

    # Step 2: fan-out; context + critique run in parallel.
    context_result, critique_result = await asyncio.gather(
        fetch_context(
            decomposition.title,
            decomposition.one_line_summary,
            decomposition.methodology.summary,
        ),
        critique_paper(paper_text, decomposition.one_line_summary),
    )

    notes = _build_notes_markdown(decomposition, context_result, critique_result)

    return FullAnalysis(
        paper_id="",  # caller sets this after computing the hash
        decomposition=decomposition,
        context=context_result,
        critique=critique_result,
        notes_markdown=notes,
    )


def _build_notes_markdown(
    d: DecomposedPaper,
    c: ContextResult,
    cr: CriticResult,
) -> str:
    authors_str = ", ".join(d.authors) if d.authors else "Unknown"
    lines: list[str] = [
        f"# Study Notes: {d.title}",
        "",
        f"**Authors:** {authors_str}",
        f"**Year:** {d.year or 'Unknown'}",
        f"**Summary:** {d.one_line_summary}",
        f"**Overall difficulty:** {d.overall_difficulty}",
        "",
        "---",
        "",
        "## Paper Breakdown",
        "",
    ]

    sections = [
        ("Problem Statement", d.problem),
        ("Prior Work", d.prior_work),
        ("Methodology", d.methodology),
        ("Results", d.results),
    ]
    for name, sec in sections:
        lines += [
            f"### {name}",
            "",
            sec.summary,
            "",
            f"**Key terms:** {', '.join(sec.key_terms)}",
            f"**Difficulty:** {sec.difficulty}",
            "",
        ]

    lines += [
        "---",
        "",
        "## Critical Analysis",
        "",
        cr.overall_assessment,
        "",
        "### Findings",
        "",
    ]
    for finding in cr.findings:
        lines.append(
            f"- `[{finding.severity.upper()}]` **{finding.category}:** {finding.finding}"
        )

    lines += ["", "### What This Paper Does NOT Prove", ""]
    for item in cr.what_paper_does_not_prove:
        lines.append(f"- {item}")

    lines += ["", "### Common Misreadings", ""]
    for item in cr.common_misreadings:
        lines.append(f"- {item}")

    if cr.replication_concerns:
        lines += ["", "### Replication Concerns", ""]
        for item in cr.replication_concerns:
            lines.append(f"- {item}")

    return "\n".join(lines)
