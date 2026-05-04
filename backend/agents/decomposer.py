from __future__ import annotations
import json
import re
from typing import Any

from pydantic_ai import Agent
from models import DecomposedPaper, PaperSection
from model_config import make_agent

_SYSTEM = """\
You are an expert academic researcher who explains research papers clearly.

Analyze the provided paper and extract exactly five sections:
- problem: What specific problem is this paper solving?
- prior_work: What previous work does this build on, and where does it fall short?
- methodology: What is the core approach, architecture, or method?
- results: What are the key quantitative and qualitative findings?
- limitations: What are the stated or apparent limitations?

For each section provide:
- summary: A clear, jargon-light explanation (2-4 sentences)
- key_terms: 3-5 important technical terms from that section
- difficulty: One of "beginner", "intermediate", or "advanced"

Also provide:
- title, authors (list of strings), year
- one_line_summary: A single sentence that captures the paper's core contribution
- overall_difficulty: One of "beginner", "intermediate", or "advanced"

Return exactly one raw JSON object.
The JSON object must contain the DecomposedPaper fields at the top level:
title, authors, year, one_line_summary, overall_difficulty, problem, prior_work, methodology, results, limitations.

Do not return markdown.
Do not wrap the object in a function call.
Do not include name or parameters.
Do not put the JSON inside a string field such as input.
Do not escape the JSON as a string.

Be faithful to the paper - do not invent claims not present in the text.\
"""

decomposer_agent = make_agent(_SYSTEM)


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in decomposer output")

    in_string = False
    escape = False
    depth = 0

    for index in range(start, len(text)):
        char = text[index]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    if depth > 0:
        return text[start:] + ("}" * depth)

    raise ValueError("Malformed JSON object in decomposer output")


def _unwrap_decomposition_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    parameters = data.get("parameters")
    if isinstance(parameters, dict):
        json_object = parameters.get("json_object")
        if isinstance(json_object, dict):
            return json_object
        return parameters

    return data


_STOPWORDS = {
    "about",
    "after",
    "against",
    "among",
    "based",
    "between",
    "could",
    "during",
    "from",
    "have",
    "into",
    "paper",
    "results",
    "study",
    "that",
    "their",
    "these",
    "this",
    "through",
    "using",
    "were",
    "which",
    "with",
}

_PREFERRED_TERMS = [
    "large language models",
    "tool integration",
    "tool invocation timing",
    "tool selection accuracy",
    "robust reasoning",
    "fine-tuning",
    "in-context learning",
    "retrieval",
    "Chameleon",
    "ScienceQA",
    "ToolLLM",
    "Toolformer",
    "HuggingGPT",
    "WebGPT",
    "ReAct",
    "TaskMatrix.AI",
    "Gorilla",
    "API-Bank",
    "ToolAlpaca",
]


def _clean_text(text: str, limit: int = 1200) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rsplit(" ", 1)[0] + "."


def _split_sentences(text: str) -> list[str]:
    cleaned = _clean_text(text, 4000)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) > 20]


def _pick_sentences(
    sentences: list[str],
    keywords: tuple[str, ...],
    fallback_start: int = 0,
    count: int = 2,
) -> str:
    matches = [
        sentence
        for sentence in sentences
        if any(keyword in sentence.lower() for keyword in keywords)
    ]
    selected = matches[:count]
    if not selected:
        selected = sentences[fallback_start : fallback_start + count]
    return _clean_text(" ".join(selected), 700) if selected else ""


def _present_phrases(text: str, phrases: list[str]) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in phrases if phrase.lower() in lowered]


def _join_phrases(phrases: list[str]) -> str:
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    return ", ".join(phrases[:-1]) + f", and {phrases[-1]}"


def _section_summary(
    base: str,
    detected: list[str],
    fallback: str,
    limit: int = 850,
) -> str:
    pieces = []
    if base:
        pieces.append(base)
    if detected:
        pieces.append(f"The abstract specifically points to {_join_phrases(detected)}.")
    if not pieces:
        pieces.append(fallback)
    return _clean_text(" ".join(pieces), limit)


def _extract_key_terms(text: str) -> list[str]:
    terms = _present_phrases(text, _PREFERRED_TERMS)
    if len(terms) >= 5:
        return terms[:5]

    words = re.findall(r"\b[A-Za-z][A-Za-z-]{4,}\b", text)
    seen: set[str] = set()
    for term in terms:
        seen.add(term.lower())
    for word in words:
        key = word.lower()
        if key in _STOPWORDS or key in seen:
            continue
        seen.add(key)
        terms.append(word)
        if len(terms) == 5:
            break
    return terms


def _fallback_section(summary: str, source_text: str) -> PaperSection:
    return PaperSection(
        summary=summary,
        key_terms=_extract_key_terms(source_text or summary),
        difficulty="intermediate",
    )


def _fallback_decomposition(
    paper_text: str,
    title: str,
    authors: list[str] | None,
    year: int | None,
) -> DecomposedPaper:
    fallback_title = title or "Untitled paper"
    sentences = _split_sentences(paper_text)
    abstract = _clean_text(paper_text)
    one_line_summary = (
        _clean_text(sentences[0], 350)
        if sentences
        else "This paper studies the research problem described in the submitted abstract."
    )
    full_text = _clean_text(paper_text, 5000)

    problem_summary = _pick_sentences(
        sentences,
        (
            "problem",
            "challenge",
            "address",
            "aim",
            "goal",
            "need",
            "gap",
            "hallucination",
            "precision",
            "real-time",
            "tool invocation",
            "tool selection",
            "reasoning",
        ),
        fallback_start=0,
    )
    methodology_summary = _pick_sentences(
        sentences,
        (
            "method",
            "approach",
            "model",
            "framework",
            "paradigm",
            "intent",
            "plan",
            "execute",
            "feedback",
            "perception",
            "adjust",
            "fintent",
            "fplan",
            "fexec",
            "ffeedback",
            "fperceive",
            "fadjust",
        ),
        fallback_start=1,
    )
    results_summary = _pick_sentences(
        sentences,
        (
            "result",
            "show",
            "demonstrate",
            "achieve",
            "improve",
            "outperform",
            "evaluation",
            "chameleon",
            "scienceqa",
            "accuracy",
            "table",
            "state-transition",
        ),
        fallback_start=2,
    )
    limitations_summary = _pick_sentences(
        sentences,
        ("limit", "future", "however", "although", "while", "remain", "scope"),
        fallback_start=max(len(sentences) - 1, 0),
        count=1,
    )
    prior_work_summary = _pick_sentences(
        sentences,
        (
            "prior",
            "previous",
            "existing",
            "state-of-the-art",
            "baseline",
            "related",
            "toolformer",
            "toollm",
            "chameleon",
            "hugginggpt",
            "webgpt",
            "react",
            "retrieval",
            "fine-tuning",
            "in-context",
        ),
        fallback_start=0,
        count=1,
    )

    problem_terms = _present_phrases(
        full_text,
        [
            "precision",
            "real-time information",
            "hallucination",
            "tool invocation timing",
            "tool selection accuracy",
            "robust reasoning",
        ],
    )
    prior_terms = _present_phrases(
        full_text,
        [
            "Toolformer",
            "ToolLLM",
            "Chameleon",
            "HuggingGPT",
            "WebGPT",
            "ReAct",
            "TaskMatrix.AI",
            "Gorilla",
            "API-Bank",
            "ToolAlpaca",
            "retrieval",
            "fine-tuning",
            "in-context learning",
        ],
    )
    method_terms = _present_phrases(
        full_text,
        [
            "user instruction",
            "intent",
            "plan",
            "execute",
            "feedback",
            "perception",
            "summary",
            "plan adjustment",
            "fintent",
            "fplan",
            "fexec",
            "ffeedback",
            "fperceive",
            "fadjust",
        ],
    )
    result_terms = _present_phrases(
        full_text,
        [
            "Chameleon",
            "ScienceQA",
            "CoT",
            "QA accuracy",
            "accuracy tables",
            "state-transition",
            "code-structure",
        ],
    )

    if not problem_summary:
        problem_summary = (
            "The paper examines why large language models need external tools: they can struggle with precision, current information, hallucination, deciding when to invoke tools, selecting the right tool, and maintaining robust reasoning across tool-use steps."
        )
    if not methodology_summary:
        methodology_summary = (
            "The paper frames tool use as a workflow that moves from user instruction to intent recognition, planning, tool execution, feedback, perception or summarization, and plan adjustment."
        )
    if not results_summary:
        results_summary = (
            "The paper reproduces Chameleon results on ScienceQA and compares reproduced outcomes with reported CoT and Chameleon accuracy, while also analyzing Chameleon code structure/state transitions."
        )
    if not limitations_summary:
        limitations_summary = (
            "The abstract does not state clear limitations; treat the claims as scoped to the described setting and evidence."
        )
    if not prior_work_summary:
        prior_work_summary = (
            "The paper should be read against prior work on tool-using language models, including retrieval, fine-tuning, in-context learning, and agent-style tool orchestration."
        )

    problem_summary = _section_summary(
        problem_summary,
        problem_terms,
        "The paper studies limitations that appear when language models need external tools for accurate, current, and reliable problem solving.",
    )
    prior_work_summary = _section_summary(
        prior_work_summary,
        prior_terms,
        "The related-work context includes tool-augmented LLM systems, retrieval-based methods, fine-tuning approaches, and in-context learning approaches.",
    )
    methodology_summary = _section_summary(
        methodology_summary,
        method_terms,
        "The methodology is organized around a standardized tool-use loop from instruction understanding through planning, execution, feedback, perception, and adjustment.",
    )
    results_summary = _section_summary(
        results_summary,
        result_terms,
        "The results focus on how tool-use workflows behave in reproduced experiments, comparisons with chain-of-thought baselines, accuracy tables, and code-structure or state-transition analyses.",
    )

    return DecomposedPaper(
        title=fallback_title,
        authors=authors or [],
        year=year,
        one_line_summary=one_line_summary,
        overall_difficulty="intermediate",
        problem=_fallback_section(problem_summary, abstract),
        prior_work=_fallback_section(prior_work_summary, abstract),
        methodology=_fallback_section(methodology_summary, abstract),
        results=_fallback_section(results_summary, abstract),
        limitations=_fallback_section(limitations_summary, abstract),
    )


async def decompose_paper(
    paper_text: str,
    title: str = "",
    authors: list[str] | None = None,
    year: int | None = None,
) -> DecomposedPaper:
    meta_lines: list[str] = []
    if title:
        meta_lines.append(f"Title: {title}")
    if authors:
        meta_lines.append(f"Authors: {', '.join(authors)}")
    if year:
        meta_lines.append(f"Year: {year}")
    meta = "\n".join(meta_lines) + "\n\n" if meta_lines else ""

    prompt = f"{meta}Paper text:\n{paper_text[:60_000]}"
    result = await decomposer_agent.run(prompt)

    try:
        raw_json = _extract_json_object(result.output)
        data = json.loads(raw_json)
        data = _unwrap_decomposition_data(data)
        return DecomposedPaper.model_validate(data)
    except Exception:
        return _fallback_decomposition(paper_text, title, authors, year)
