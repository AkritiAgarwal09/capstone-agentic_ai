from __future__ import annotations
import hashlib
from dotenv import load_dotenv
load_dotenv()  # loads backend/.env when running from the backend/ directory

from fastapi import FastAPI, UploadFile, HTTPException, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import FullAnalysis, TutorResponse, QuizResult
from tools.pdf_parser import extract_arxiv_id_from_text, parse_pdf_bytes
from tools.arxiv_fetcher import fetch_arxiv_paper
from agents.orchestrator import run_full_analysis
from agents.tutor import ask_tutor, generate_quiz

app = FastAPI(title="Academic Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to frontend Cloud Run URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory paper cache: paper_id → {text, summary}
# Deploy with --max-instances=1 on Cloud Run to avoid cache misses across instances.
_paper_cache: dict[str, dict] = {}


class ArxivRequest(BaseModel):
    arxiv_input: str


class AskRequest(BaseModel):
    paper_id: str
    question: str
    conversation_history: list[dict] = []


class QuizRequest(BaseModel):
    paper_id: str


def _make_paper_id(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze/pdf", response_model=FullAnalysis)
async def analyze_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    parsed = parse_pdf_bytes(pdf_bytes)
    paper_text = parsed.get("abstract") or parsed["text"]
    title = parsed.get("title", "")
    authors: list[str] = []
    year: int | None = None

    arxiv_id = extract_arxiv_id_from_text(
        parsed.get("raw_text") or parsed.get("abstract") or parsed.get("text", "")
    )
    if arxiv_id:
        try:
            arxiv_meta = await fetch_arxiv_paper(arxiv_id)
        except Exception:
            arxiv_meta = {}
        title = arxiv_meta.get("title") or title
        authors = arxiv_meta.get("authors") or authors
        year = arxiv_meta.get("year") or year
        if arxiv_meta.get("abstract"):
            paper_text = arxiv_meta["abstract"]

    analysis = await run_full_analysis(
        paper_text=paper_text,
        title=title,
        authors=authors,
        year=year,
    )

    paper_id = _make_paper_id(title or paper_text[:100])
    analysis = analysis.model_copy(update={"paper_id": paper_id})
    _paper_cache[paper_id] = {
        "text": paper_text,
        "summary": analysis.decomposition.one_line_summary,
    }
    return analysis


@app.post("/analyze/arxiv", response_model=FullAnalysis)
async def analyze_arxiv(body: ArxivRequest):
    try:
        parsed = await fetch_arxiv_paper(body.arxiv_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"arXiv fetch failed: {e}")

    paper_text = parsed.get("abstract") or parsed.get("text")
    if not paper_text:
        raise HTTPException(status_code=502, detail="arXiv fetch failed: no paper text found")

    analysis = await run_full_analysis(
        paper_text=paper_text,
        title=parsed.get("title", ""),
        authors=parsed.get("authors", []),
        year=parsed.get("year"),
    )

    paper_id = _make_paper_id(parsed.get("title") or paper_text[:100])
    analysis = analysis.model_copy(update={"paper_id": paper_id})
    _paper_cache[paper_id] = {
        "text": paper_text,
        "summary": analysis.decomposition.one_line_summary,
    }
    return analysis


@app.post("/ask", response_model=TutorResponse)
async def ask(body: AskRequest):
    cached = _paper_cache.get(body.paper_id)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="Paper not found. Please re-analyze the paper first.",
        )
    response = await ask_tutor(body.question, cached["text"], body.conversation_history)
    return response


@app.post("/quiz", response_model=QuizResult)
async def quiz(body: QuizRequest):
    cached = _paper_cache.get(body.paper_id)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="Paper not found. Please re-analyze the paper first.",
        )
    result = await generate_quiz(cached["text"], cached["summary"])
    return result
