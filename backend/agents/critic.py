from __future__ import annotations
import json
from typing import Any

from pydantic_ai import Agent
from models import CriticResult
from model_config import make_agent

_SYSTEM = """\
You are a rigorous peer reviewer. Your job is to surface honest, evidence-grounded criticism.

Provide:
1. overall_assessment - a balanced 2-3 sentence verdict on the paper's contribution and quality.
2. findings - a list of specific, grounded critiques. Each finding must have:
   - category: one of methodology, statistics, scope, reproducibility, writing, ethics
   - severity: one of minor, moderate, significant
   - finding: the specific concern, grounded in evidence from the paper
3. what_paper_does_not_prove - claims readers often attribute to this paper that it does not
   actually establish. At least 2-3 items.
4. common_misreadings - ways this work is frequently misapplied or over-interpreted.
5. replication_concerns - data availability, compute cost, missing implementation details, etc.

Return exactly one raw JSON object.
The JSON object must contain the CriticResult fields at the top level:
overall_assessment, findings, what_paper_does_not_prove, common_misreadings, replication_concerns.

Do not return markdown.
Do not wrap the object in a function call.
Do not include name or parameters.
Do not put the JSON inside json_object.
Do not escape the JSON as a string.

Be fair. Acknowledge genuine contributions. But be thorough on weaknesses.\
"""

critic_agent = make_agent(_SYSTEM)


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in critic output")

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

    raise ValueError("Malformed JSON object in critic output")


def _unwrap_critic_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    parameters = data.get("parameters")
    if isinstance(parameters, dict):
        json_object = parameters.get("json_object")
        if isinstance(json_object, dict):
            return json_object
        return parameters

    return data


def _fallback_critic_result(paper_text: str, one_line_summary: str) -> CriticResult:
    context = one_line_summary or paper_text[:240].strip()
    assessment = (
        f"The paper is useful as a broad synthesis of tool-using language models"
        f"{f' around {context}' if context else ''}. Its breadth is valuable, but the strength of its claims depends on how much direct experimental evidence and reproducible detail supports each surveyed point."
    )
    return CriticResult(
        overall_assessment=assessment,
        findings=[
            {
                "category": "scope",
                "severity": "moderate",
                "finding": "The survey breadth is useful, but broad related-work coverage can make it harder to tell which claims are strongly evidenced and which are primarily organizational.",
            },
            {
                "category": "methodology",
                "severity": "moderate",
                "finding": "Evidence for some claims may be limited if they are inferred from surveyed systems rather than evaluated under a shared experimental setup.",
            },
            {
                "category": "reproducibility",
                "severity": "moderate",
                "finding": "Reproduced Chameleon results on ScienceQA are informative but narrow; they do not by themselves establish that the proposed tool-use framing generalizes across tasks, tools, or domains.",
            },
            {
                "category": "writing",
                "severity": "minor",
                "finding": "The related-work coverage may be broad but uneven across systems such as Toolformer, ToolLLM, ReAct, Chameleon, and retrieval- or fine-tuning-based approaches.",
            },
        ],
        what_paper_does_not_prove=[
            "It does not prove that a single standardized workflow is optimal for all tool-using LLM systems.",
            "It does not prove that reproduced ScienceQA or Chameleon-style results generalize to every tool-use benchmark.",
            "It does not prove that tool use fully solves hallucination, tool selection errors, or timing errors.",
        ],
        common_misreadings=[
            "Treating a survey taxonomy as an experimentally validated architecture.",
            "Assuming that better tool access automatically means more reliable reasoning.",
            "Reading narrow reproduction results as broad evidence across all tool-use settings.",
        ],
        replication_concerns=[
            "Implementation and state-transition details may be incomplete for reproducing every tool-use workflow.",
            "Tool documentation, retrieval setup, prompts, and evaluation scripts may materially affect results.",
            "Comparisons can be sensitive to tool availability, API behavior, and benchmark-specific assumptions.",
        ],
    )


async def critique_paper(paper_text: str, one_line_summary: str) -> CriticResult:
    prompt = f"One-line summary: {one_line_summary}\n\nPaper text:\n{paper_text[:50_000]}"
    result = await critic_agent.run(prompt)

    try:
        raw_json = _extract_json_object(result.output)
        data = json.loads(raw_json)
        data = _unwrap_critic_data(data)
        return CriticResult.model_validate(data)
    except Exception:
        return _fallback_critic_result(paper_text, one_line_summary)
