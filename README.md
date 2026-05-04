# Academic Copilot

> Read research papers like a professor explains them.

Four AI agents working in parallel to decompose, contextualize, critique, and teach any research paper — from PDF upload or arXiv ID.

**Live URL:** `<your-deployed-url>`

---

## Changes in this fork

- **LLM backend → Ollama** — all four agents (`decomposer`, `critic`, `tutor`, `quiz`, `context_fetcher`) now use `ollama:llama3.3` via pydantic-ai's Ollama provider. No cloud API key is required; just run `ollama serve` locally (default `http://localhost:11434`). Override the base URL with `OLLAMA_BASE_URL` in your `.env`.
- **Abstract-only PDF parsing** — `pdf_parser.py` now reads only the first 4 pages and extracts the **abstract section** using heading-based regex patterns (supports "Abstract\n", "Abstract—", "Abstract:"). This dramatically reduces token usage and focuses agents on the paper's core contribution rather than the full body.

---

## Three Steps (Collect → EDA → Hypothesize)

### Step 1: Collect
- **PDF upload** — `backend/tools/pdf_parser.py::parse_pdf_bytes` opens the PDF with PyMuPDF, fixes ligature/hyphenation artifacts common in academic PDFs, reads only the first 4 pages, and extracts the abstract section using regex heuristics with a fallback to the first 1500 characters
- **arXiv fetch** — `backend/tools/arxiv_fetcher.py::fetch_arxiv_paper` normalizes any arXiv ID or URL, hits the Atom metadata API for title/authors/year/abstract, downloads the PDF, and passes it through `parse_pdf_bytes`
- Both paths produce the same dict: `{title, authors, year, text, abstract, num_pages}`

### Step 2: EDA (Explore & Analyze)

Three agents fan out in parallel after the Decomposer finishes:

| Agent | File | What it does |
|-------|------|--------------|
| **Decomposer** | `backend/agents/decomposer.py` | Structured breakdown of 5 sections (Problem, Prior Work, Methodology, Results, Limitations) — each with summary, key terms, difficulty rating |
| **Context Fetcher** | `backend/agents/context_fetcher.py` | Calls `find_related_papers` tool 2–3× against Semantic Scholar API; synthesizes field summary, related papers, research gap |
| **Critic** | `backend/agents/critic.py` | Surfaces findings by category and severity; lists what the paper does NOT prove, common misreadings, replication concerns |

Fan-out coordination: `backend/agents/orchestrator.py::run_full_analysis` — Decomposer runs first, then Context + Critic run via `asyncio.gather`.

### Step 3: Hypothesize
- **Tutor** (`backend/agents/tutor.py::ask_tutor`) — interactive multi-turn Q&A; last 6 messages of conversation history included in each prompt; "explain simpler" chip sends a follow-up automatically
- **Quiz** (`backend/agents/tutor.py::generate_quiz`) — 5 questions testing understanding, not memorization; generated on-demand (not pre-fetched)
- **Notes artifact** (`backend/agents/orchestrator.py::_build_notes_markdown`) — downloadable Markdown study guide stitching all three agent outputs

---

## Class Concepts → Code

| Concept | Location |
|---------|----------|
| Agent framework (PydanticAI) | `backend/agents/*.py` — all four agents use `Agent(output_type=...)` |
| Multi-agent fan-out | `backend/agents/orchestrator.py::run_full_analysis` — `asyncio.gather` |
| Tool calling | `backend/agents/context_fetcher.py` — `@context_agent.tool_plain find_related_papers` |
| Structured output | `backend/models.py` — every agent returns a typed Pydantic model |
| Chunked context (RAG-adjacent) | `backend/tools/pdf_parser.py` — 3 000-char chunks, 300-char overlap |
| Second data source | `backend/tools/semantic_scholar.py` — Semantic Scholar `/paper/search` API |
| Iterative refinement | `backend/components/TutorChat.tsx` — "Explain simpler ↓" chip; `backend/agents/tutor.py` — `simplified_version` field |
| Artifact output | `backend/agents/orchestrator.py::_build_notes_markdown` — Markdown study guide |
| Deployed frontend | `frontend/` — Next.js 15 on Cloud Run |

---

## Running Locally

### Backend

```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install "fastapi>=0.115.0" "uvicorn[standard]>=0.32.0" "pydantic-ai>=1.0.0" \
               "pymupdf>=1.24.0" "httpx>=0.27.0" "python-multipart>=0.0.12" "pydantic>=2.8.0"

# Create .env with your key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

ANTHROPIC_API_KEY=sk-ant-... uvicorn app:app --reload --port 8080
```

Test with:
```bash
curl -s -X POST http://localhost:8080/analyze/arxiv \
  -H "Content-Type: application/json" \
  -d '{"arxiv_input": "1706.03762"}' | python3 -m json.tool | head -30
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local
npm run dev
```

Open **http://localhost:3000**

---

## Deploying to GCP

### Prerequisites
```bash
gcloud projects create YOUR_PROJECT_ID
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

### Set secrets
```bash
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key --data-file=-
```

### Deploy backend
```bash
gcloud builds submit --config cloudbuild-backend.yaml
# Note the Cloud Run URL, e.g. https://capstone-agentic-ai-backend-xxx.run.app
```

### Deploy frontend
```bash
echo -n "https://capstone-agentic-ai-backend-xxx.run.app" | gcloud secrets create backend-url --data-file=-
gcloud builds submit --config cloudbuild-frontend.yaml
```

> **Note:** The backend is deployed with `--max-instances=1` to keep the in-memory paper cache consistent. If you need higher throughput, migrate `_paper_cache` to Firestore.

---

## Architecture

```
User
 │
 ▼
Next.js Frontend (port 3000)
 │  POST /analyze/arxiv  or  POST /analyze/pdf
 │  POST /ask            (multi-turn tutor)
 │  POST /quiz           (on-demand)
 ▼
FastAPI Backend (port 8080)
 │
 ├─ PDF Parser / arXiv Fetcher ──────── Step 1: Collect
 │    tools/pdf_parser.py
 │    tools/arxiv_fetcher.py
 │    tools/semantic_scholar.py
 │
 └─ Orchestrator (fan-out) ──────────── Step 2: EDA
      agents/decomposer.py   ── DecomposedPaper
           │
           ├── agents/context_fetcher.py  ── ContextResult (tool calls Semantic Scholar)
           └── agents/critic.py           ── CriticResult
                    │
                    └── _build_notes_markdown ─── Step 3: Artifact

Tutor Agent  ←── /ask  (iterative Q&A with conversation history)
Quiz Agent   ←── /quiz (5 comprehension questions)
```

---

## Key Design Decisions

**paper_id:** Computed server-side as `md5(title)[:12]` and returned as part of `FullAnalysis`. The frontend stores and passes it directly — no client-side hash that could drift.

**Chunking:** 80 000-char cap fits cleanly inside Claude's context window. Chunks (3 000 chars, 300 overlap) are produced but the agents currently receive the full truncated text; chunks are available for future RAG retrieval.

**pydantic-ai v1.89:** Uses `output_type=` (not `result_type=`) and `result.output` (not `result.data`). All agents are created with `defer_model_check=True` so the app imports cleanly without the API key set.

---

## Token Economics

| Item | Estimate |
|------|----------|
| Avg paper size | ~8 k tokens input |
| Full analysis (4 agents) | ~25 k tokens total |
| Cost per analysis (Sonnet) | ~$0.06 |
| Avg user: 20 analyses/month | ~$1.20/month cost |
| Freemium: 5 free, paid $12/month | $10.80 gross margin per user |
| Target: 10 k paying users | ~$108 k MRR |
