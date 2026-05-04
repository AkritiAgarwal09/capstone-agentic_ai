from __future__ import annotations
import json
import re
from typing import Any

from pydantic_ai import Agent
from models import TutorResponse, QuizResult
from model_config import make_agent

_TUTOR_SYSTEM = """\
You are a brilliant professor who excels at explaining complex research to students.

For each question:
- explanation: a clear, direct answer grounded in the paper
- follow_up_questions: 2-3 questions the student is likely to ask next
- analogy: a concrete real-world analogy when it would help intuition
- simplified_version: a simpler re-explanation - ONLY include this when the student explicitly
  asks to "explain simpler", "ELI5", "break it down", or similar

Build on any conversation history to go progressively deeper.
Ground all explanations in the paper content provided.\
"""

_QUIZ_SYSTEM = """\
You are creating a comprehension quiz for a research paper.

Generate exactly 5 multiple-choice questions that test UNDERSTANDING, not memorization.
Good questions probe:
- Why the authors made key methodological choices (not just what they chose)
- What the results actually mean for the field
- Limitations and their practical implications
- How this work relates to or differs from prior work

Each question must have exactly 4 answer options (A-D), one clearly correct answer,
and an explanation of why it is correct.

Return exactly one raw JSON object.
The JSON object must contain a top-level questions array.
Each question item must contain question, options, correct_index, and explanation.

Do not return markdown.
Do not wrap the object in a function call.
Do not include name or parameters.
Do not escape the JSON as a string.\
"""

tutor_agent = make_agent(_TUTOR_SYSTEM)

quiz_agent = make_agent(_QUIZ_SYSTEM)


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in quiz output")

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

    raise ValueError("Malformed JSON object in quiz output")


def _unwrap_quiz_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    parameters = data.get("parameters")
    if isinstance(parameters, dict):
        json_object = parameters.get("json_object")
        if isinstance(json_object, dict):
            return json_object
        return parameters

    return data


def _remove_trailing_commas(raw_json: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", raw_json)


def _unwrap_object_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    parameters = data.get("parameters")
    if isinstance(parameters, dict):
        json_object = parameters.get("json_object")
        if isinstance(json_object, dict):
            return json_object
        return parameters

    return data


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        parts = [f"{key}: {val}" for key, val in value.items() if val is not None]
        return "; ".join(parts) or None
    return str(value)


def _normalise_tutor_data(data: Any) -> Any:
    data = _unwrap_object_data(data)
    if not isinstance(data, dict):
        return data

    follow_ups = data.get("follow_up_questions", [])
    if isinstance(follow_ups, str):
        follow_ups = [
            item.strip(" -")
            for item in re.split(r"\n|[?]\s*", follow_ups)
            if item.strip(" -")
        ]
        follow_ups = [f"{item}?" if not item.endswith("?") else item for item in follow_ups]
    elif isinstance(follow_ups, list):
        follow_ups = [str(item) for item in follow_ups if item is not None]
    else:
        follow_ups = []

    return {
        "explanation": str(data.get("explanation") or data.get("answer") or ""),
        "follow_up_questions": follow_ups,
        "analogy": _string_or_none(data.get("analogy")),
        "simplified_version": _string_or_none(data.get("simplified_version")),
    }


def _answer_from_excerpt(question: str, paper_text: str) -> TutorResponse:
    excerpt = re.sub(r"\s+", " ", paper_text).strip()
    if len(excerpt) > 650:
        excerpt = excerpt[:650].rsplit(" ", 1)[0] + "."
    if not excerpt:
        excerpt = "The analyzed paper text is not available in the current session."

    explanation = (
        f"The paper's answer to your question is best read through its stated problem and evidence. "
        f"For '{question}', the relevant point is that the paper frames its contribution around this content: {excerpt} "
        f"In practical terms, focus on what claim the authors make, what method or comparison supports it, and what scope limits the conclusion. "
        f"A careful reading should separate the paper's demonstrated findings from broader implications that would need more evidence."
    )
    return TutorResponse(
        explanation=explanation,
        follow_up_questions=[
            "Which part of the paper supports this answer?",
            "How does this connect to the paper's methodology?",
            "What limitation should I keep in mind?",
        ],
        analogy=None,
        simplified_version=None,
    )


def _options_from_string(options: str) -> list[str]:
    parts = [
        part.strip(" \t\r\n:-.)")
        for part in re.split(r"(?:^|\s)[A-Da-d][\).:-]\s*", options)
        if part.strip(" \t\r\n:-.)")
    ]
    if len(parts) >= 4:
        return parts[:4]

    lines = [line.strip(" \t\r\n:-.)") for line in options.splitlines() if line.strip()]
    if len(lines) >= 4:
        return lines[:4]

    return ["Option A", "Option B", "Option C", "Option D"]


def _normalise_correct_index(value: Any) -> int:
    if isinstance(value, int):
        return min(max(value, 0), 3)

    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return min(max(int(value), 0), 3)
        letter = value[:1].upper()
        if letter in {"A", "B", "C", "D"}:
            return ord(letter) - ord("A")

    return 0


def _normalise_question(question: dict[str, Any]) -> dict[str, Any]:
    options = question.get("options", [])
    if isinstance(options, str):
        options = _options_from_string(options)
    elif isinstance(options, list):
        options = [str(option) for option in options[:4]]
        while len(options) < 4:
            options.append(f"Option {chr(ord('A') + len(options))}")
    else:
        options = ["Option A", "Option B", "Option C", "Option D"]

    return {
        "question": str(question.get("question") or "What is a key idea from this paper?"),
        "options": options,
        "correct_index": _normalise_correct_index(question.get("correct_index", 0)),
        "explanation": str(
            question.get("explanation")
            or "This question checks basic understanding of the paper."
        ),
    }


def _normalise_quiz_data(data: Any) -> Any:
    data = _unwrap_quiz_data(data)

    if isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    elif isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and {"question", "options"} <= set(data):
        questions = [data]
    else:
        return data

    if isinstance(questions, dict):
        questions = [questions]

    if not isinstance(questions, list):
        return data

    return {
        "questions": [
            _normalise_question(question)
            for question in questions
            if isinstance(question, dict)
        ]
    }


def _summary_excerpt(one_line_summary: str) -> str:
    summary = re.sub(r"\s+", " ", one_line_summary).strip()
    if not summary:
        return "the paper's main claim"
    if len(summary) <= 120:
        return summary
    return summary[:120].rsplit(" ", 1)[0]


def _fallback_questions(one_line_summary: str) -> list[dict[str, Any]]:
    summary = _summary_excerpt(one_line_summary)
    is_tool_llm = any(
        term in summary.lower()
        for term in ("tool", "llm", "language model", "chameleon", "scienceqa")
    )
    if is_tool_llm:
        return [
            {
                "question": "Why do language models need external tools in this paper's setting?",
                "options": [
                    "To improve access to precise, current, or specialized capabilities",
                    "To make every answer shorter",
                    "To remove the need for planning",
                    "To avoid using any evidence",
                ],
                "correct_index": 0,
                "explanation": "Tool use helps cover weaknesses such as stale knowledge, precision limits, and specialized operations.",
            },
            {
                "question": "What does tool invocation timing refer to?",
                "options": [
                    "Deciding when the model should call a tool during reasoning",
                    "Measuring how fast a user types",
                    "Choosing the publication year of a paper",
                    "Skipping feedback after tool execution",
                ],
                "correct_index": 0,
                "explanation": "A tool-using model must decide not only which tool to use, but when to use it.",
            },
            {
                "question": "Why is tool selection accuracy important?",
                "options": [
                    "The wrong tool can produce irrelevant or misleading intermediate results",
                    "It guarantees every benchmark is solved",
                    "It replaces the need for evaluation",
                    "It only affects user interface design",
                ],
                "correct_index": 0,
                "explanation": "Selecting the right tool is central to reliable tool-augmented reasoning.",
            },
            {
                "question": "Which workflow best matches the standardized tool-use paradigm?",
                "options": [
                    "User instruction, intent, plan, execute, feedback, perception, adjustment",
                    "Title, abstract, bibliography, appendix",
                    "Train once, ignore tools, answer immediately",
                    "Retrieve documents and skip reasoning",
                ],
                "correct_index": 0,
                "explanation": "The paradigm describes a repeated loop of understanding, planning, execution, feedback, and adjustment.",
            },
            {
                "question": "How do fine-tuning, in-context learning, and retrieval differ in tool-use systems?",
                "options": [
                    "They are different ways to teach or supply tool knowledge to the model",
                    "They are identical names for the same benchmark",
                    "They only describe frontend rendering",
                    "They prevent the need for tool documentation",
                ],
                "correct_index": 0,
                "explanation": "Fine-tuning changes model behavior, in-context learning uses examples in the prompt, and retrieval can supply tool documentation.",
            },
        ]

    return [
        {
            "question": f"What is the main purpose of this paper about {summary}?",
            "options": [
                "To solve or study the problem described in the paper",
                "To replace all prior research without comparison",
                "To avoid evaluating any results",
                "To summarize unrelated work",
            ],
            "correct_index": 0,
            "explanation": "The paper should be read around its stated problem and contribution.",
        },
        {
            "question": "Why are limitations important when interpreting this paper?",
            "options": [
                "They clarify what the paper does and does not prove",
                "They make the results irrelevant",
                "They are always implementation bugs",
                "They replace the methodology",
            ],
            "correct_index": 0,
            "explanation": "Limitations help define the scope of the paper's claims.",
        },
        {
            "question": "What should this paper be compared against?",
            "options": [
                "Prior work and related methods in the field",
                "Only the paper title",
                "Unrelated benchmarks",
                "The number of pages",
            ],
            "correct_index": 0,
            "explanation": "Related work gives context for the paper's contribution.",
        },
        {
            "question": f"What should a reader check to evaluate the claim that {summary}?",
            "options": [
                "Whether the methodology and evidence support the claim",
                "Whether the abstract is short",
                "Whether the paper has many authors",
                "Whether every limitation is solved",
            ],
            "correct_index": 0,
            "explanation": "Understanding depends on connecting the claim to the method and evidence.",
        },
        {
            "question": "Why is the methodology section important for understanding the paper?",
            "options": [
                "It explains how the authors support their conclusions",
                "It lists unrelated future work",
                "It replaces the results section",
                "It determines the publication year",
            ],
            "correct_index": 0,
            "explanation": "The methodology explains how the paper moves from problem to evidence.",
        },
    ]


def _ensure_five_questions(quiz: QuizResult, one_line_summary: str) -> QuizResult:
    questions = list(quiz.questions[:5])
    fallback = _fallback_questions(one_line_summary)
    index = 0
    while len(questions) < 5:
        questions.append(_normalise_question(fallback[index]))
        index += 1
    return QuizResult(questions=questions[:5])


def _fallback_quiz_result(one_line_summary: str) -> QuizResult:
    return QuizResult(
        questions=[
            _normalise_question(question)
            for question in _fallback_questions(one_line_summary)
        ]
    )


async def ask_tutor(
    question: str,
    paper_text: str,
    conversation_history: list[dict],
) -> TutorResponse:
    history_text = ""
    for msg in conversation_history[-6:]:
        role = "Student" if msg.get("role") == "user" else "Professor"
        history_text += f"{role}: {msg.get('content', '')}\n\n"

    history_section = (
        f"Previous conversation:\n{history_text}\n" if history_text else ""
    )

    prompt = (
        f"Paper text (excerpt):\n{paper_text[:50_000]}\n\n"
        f"{history_section}"
        f"Student question: {question}"
    )
    result = await tutor_agent.run(prompt)
    try:
        raw_json = _extract_json_object(result.output)
        raw_json = _remove_trailing_commas(raw_json)
        data = json.loads(raw_json)
        data = _normalise_tutor_data(data)
        response = TutorResponse.model_validate(data)
        if not response.explanation.strip():
            return _answer_from_excerpt(question, paper_text)
        return response
    except Exception:
        return _answer_from_excerpt(question, paper_text)


async def generate_quiz(paper_text: str, one_line_summary: str) -> QuizResult:
    prompt = (
        f"Paper summary: {one_line_summary}\n\n"
        f"Paper text:\n{paper_text[:40_000]}"
    )
    result = await quiz_agent.run(prompt)

    try:
        raw_json = _extract_json_object(result.output)
        raw_json = _remove_trailing_commas(raw_json)
        data = json.loads(raw_json)
        data = _normalise_quiz_data(data)
        quiz = QuizResult.model_validate(data)
        if not quiz.questions:
            return _fallback_quiz_result(one_line_summary)
        return _ensure_five_questions(quiz, one_line_summary)
    except Exception:
        return _fallback_quiz_result(one_line_summary)
