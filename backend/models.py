from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, model_validator


class PaperSection(BaseModel):
    summary: str
    key_terms: list[str]
    difficulty: str  # "beginner" | "intermediate" | "advanced"


class DecomposedPaper(BaseModel):
    title: str
    authors: list[str]
    year: Optional[int] = None
    one_line_summary: str
    overall_difficulty: str
    problem: PaperSection
    prior_work: PaperSection
    methodology: PaperSection
    results: PaperSection
    limitations: PaperSection

    @model_validator(mode="before")
    @classmethod
    def unwrap_ollama_function_call(cls, data):
        if isinstance(data, dict) and isinstance(data.get("parameters"), dict):
            return data["parameters"]
        return data


class RelatedPaper(BaseModel):
    title: str
    authors: list[str] = []
    year: Optional[int] = None
    relevance_reason: str = ""
    semantic_scholar_url: Optional[str] = None


class ContextResult(BaseModel):
    field_summary: str
    related_papers: list[RelatedPaper]
    research_gap_addressed: str

    @model_validator(mode="before")
    @classmethod
    def unwrap_ollama_function_call(cls, data):
        if not isinstance(data, dict):
            return data

        parameters = data.get("parameters")
        if isinstance(parameters, dict):
            json_object = parameters.get("json_object")
            if isinstance(json_object, dict):
                return json_object
            return parameters

        return data


class CriticFinding(BaseModel):
    category: str
    severity: str  # "minor" | "moderate" | "significant"
    finding: str


class CriticResult(BaseModel):
    overall_assessment: str
    findings: list[CriticFinding]
    what_paper_does_not_prove: list[str]
    common_misreadings: list[str]
    replication_concerns: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def unwrap_ollama_function_call(cls, data):
        if not isinstance(data, dict):
            return data

        parameters = data.get("parameters")
        if isinstance(parameters, dict):
            json_object = parameters.get("json_object")
            if isinstance(json_object, dict):
                return json_object
            return parameters

        return data


class TutorResponse(BaseModel):
    explanation: str
    follow_up_questions: list[str]
    analogy: Optional[str] = None
    simplified_version: Optional[str] = None


class QuizQuestion(BaseModel):
    question: str
    options: list[str]   # exactly 4 options
    correct_index: int   # 0–3
    explanation: str


class QuizResult(BaseModel):
    questions: list[QuizQuestion]  # exactly 5


class FullAnalysis(BaseModel):
    paper_id: str
    decomposition: DecomposedPaper
    context: ContextResult
    critique: CriticResult
    notes_markdown: str
