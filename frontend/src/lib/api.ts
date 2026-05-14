const API_URL =
  process.env.NEXT_PUBLIC_API_URL ;

// ── Shared types (mirror backend Pydantic models exactly) ──

export interface PaperSection {
  summary: string;
  key_terms: string[];
  difficulty: string;
}

export interface DecomposedPaper {
  title: string;
  authors: string[];
  year: number | null;
  one_line_summary: string;
  overall_difficulty: string;
  problem: PaperSection;
  prior_work: PaperSection;
  methodology: PaperSection;
  results: PaperSection;
  limitations: PaperSection;
}

export interface RelatedPaper {
  title: string;
  authors: string[];
  year: number | null;
  relevance_reason: string;
  semantic_scholar_url: string | null;
}

export interface ContextResult {
  field_summary: string;
  related_papers: RelatedPaper[];
  research_gap_addressed: string;
}

export interface CriticFinding {
  category: string;
  severity: "minor" | "moderate" | "significant";
  finding: string;
}

export interface CriticResult {
  overall_assessment: string;
  findings: CriticFinding[];
  what_paper_does_not_prove: string[];
  common_misreadings: string[];
  replication_concerns: string[];
}

export interface TutorResponse {
  explanation: string;
  follow_up_questions: string[];
  analogy: string | null;
  simplified_version: string | null;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface QuizResult {
  questions: QuizQuestion[];
}

export interface FullAnalysis {
  paper_id: string;
  decomposition: DecomposedPaper;
  context: ContextResult;
  critique: CriticResult;
  notes_markdown: string;
}

export type ConversationMessage = { role: "user" | "assistant"; content: string };

// ── API fetch helpers ──────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function analyzeArxiv(arxivInput: string): Promise<FullAnalysis> {
  const res = await fetch(`${API_URL}/analyze/arxiv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arxiv_input: arxivInput }),
  });
  return handleResponse<FullAnalysis>(res);
}

export async function analyzePdf(file: File): Promise<FullAnalysis> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/analyze/pdf`, {
    method: "POST",
    body: form,
  });
  return handleResponse<FullAnalysis>(res);
}

export async function askTutor(
  paperId: string,
  question: string,
  conversationHistory: ConversationMessage[]
): Promise<TutorResponse> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      paper_id: paperId,
      question,
      conversation_history: conversationHistory,
    }),
  });
  return handleResponse<TutorResponse>(res);
}

export async function getQuiz(paperId: string): Promise<QuizResult> {
  const res = await fetch(`${API_URL}/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paper_id: paperId }),
  });
  return handleResponse<QuizResult>(res);
}
