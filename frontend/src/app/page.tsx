"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  BookOpen,
  Shield,
  MessageSquare,
  FileText,
  Download,
} from "lucide-react";

import PaperInput from "@/components/PaperInput";
import Decomposition from "@/components/Decomposition";
import CriticPanel from "@/components/CriticPanel";
import TutorChat from "@/components/TutorChat";
import QuizModal from "@/components/QuizModal";
import { analyzeArxiv, analyzePdf, FullAnalysis } from "@/lib/api";

type AppState = "landing" | "loading" | "results";
type Tab = "breakdown" | "critique" | "tutor" | "notes";

const EXAMPLE_PAPERS = [
  { id: "1706.03762", label: "Attention Is All You Need" },
  { id: "2005.14165", label: "GPT-3" },
  { id: "2106.09685", label: "LoRA" },
];

const TABS: { id: Tab; label: string; Icon: React.ElementType }[] = [
  { id: "breakdown", label: "Breakdown", Icon: BookOpen },
  { id: "critique", label: "Critique", Icon: Shield },
  { id: "tutor", label: "Ask Professor", Icon: MessageSquare },
  { id: "notes", label: "Notes", Icon: FileText },
];

export default function Home() {
  const [appState, setAppState] = useState<AppState>("landing");
  const [analysis, setAnalysis] = useState<FullAnalysis | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("breakdown");
  const [showQuiz, setShowQuiz] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (type: "arxiv" | "pdf", value: string | File) => {
    setAppState("loading");
    setError(null);
    try {
      const result =
        type === "arxiv"
          ? await analyzeArxiv(value as string)
          : await analyzePdf(value as File);
      setAnalysis(result);
      setActiveTab("breakdown");
      setAppState("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed. Please try again.");
      setAppState("landing");
    }
  };

  const downloadNotes = () => {
    if (!analysis) return;
    const slug = analysis.decomposition.title
      .slice(0, 50)
      .replace(/[^a-z0-9]/gi, "_")
      .toLowerCase();
    const blob = new Blob([analysis.notes_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${slug}_notes.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /* ── Landing ──────────────────────────────────────────── */
  if (appState === "landing") {
    return (
      <div className="min-h-screen bg-[var(--ink-950)] flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-xl">
          <div className="text-center mb-10 animate-fade-up">
            <h1 className="font-serif text-5xl font-bold text-[var(--ink-50)] mb-3 leading-tight">
              Academic Copilot
            </h1>
            <p className="text-[var(--ink-400)] text-lg">
              Read research papers like a professor explains them.
            </p>
          </div>

          {error && (
            <div className="mb-5 p-4 bg-[var(--crimson)]/15 border border-[var(--crimson)]/40 rounded-xl text-[var(--crimson-light)] text-sm animate-fade-up">
              {error}
            </div>
          )}

          <PaperInput onAnalyze={handleAnalyze} />

          <div className="mt-6 text-center animate-fade-up">
            <p className="text-[var(--ink-600)] text-sm mb-3">
              Try an example paper:
            </p>
            <div className="flex gap-2 justify-center flex-wrap">
              {EXAMPLE_PAPERS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleAnalyze("arxiv", p.id)}
                  className="px-3.5 py-1.5 text-sm bg-[var(--ink-800)] border border-[var(--ink-700)] text-[var(--ink-300)] rounded-full hover:border-[var(--amber)]/60 hover:text-[var(--amber)] transition-colors"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* ── Loading ──────────────────────────────────────────── */
  if (appState === "loading") {
    return (
      <div className="min-h-screen bg-[var(--ink-950)] flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-14 h-14 border-4 border-[var(--ink-800)] border-t-[var(--amber)] rounded-full animate-spin mx-auto mb-6" />
          <h2 className="font-serif text-2xl text-[var(--ink-100)] mb-2">
            Analyzing paper…
          </h2>
          <p className="text-[var(--ink-500)] text-sm mb-8">
            Four agents working in parallel — this takes about 30 seconds.
          </p>
          <div className="space-y-2 text-sm text-[var(--ink-600)] stagger">
            <p>→ Decomposer reading paper structure</p>
            <p>→ Context agent querying Semantic Scholar</p>
            <p>→ Critic agent surfacing findings</p>
            <p>→ Orchestrator building study notes</p>
          </div>
        </div>
      </div>
    );
  }

  /* ── Results ──────────────────────────────────────────── */
  const a = analysis!;

  return (
    <div className="min-h-screen bg-[var(--ink-950)]">
      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-[var(--ink-950)]/95 backdrop-blur border-b border-[var(--ink-800)] px-6 py-3 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-serif text-base text-[var(--ink-50)] leading-tight truncate">
            {a.decomposition.title}
          </h1>
          <p className="text-[var(--ink-600)] text-xs mt-0.5 truncate">
            {a.decomposition.authors.slice(0, 3).join(", ")}
            {a.decomposition.authors.length > 3 ? " et al." : ""}
            {a.decomposition.year ? ` · ${a.decomposition.year}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setShowQuiz(true)}
            className="px-3 py-1.5 text-xs bg-[var(--ink-800)] border border-[var(--ink-700)] text-[var(--ink-300)] rounded-lg hover:border-[var(--amber)]/60 hover:text-[var(--amber)] transition-colors"
          >
            Take Quiz
          </button>
          <button
            onClick={downloadNotes}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-[var(--amber)] text-[var(--ink-950)] rounded-lg font-semibold hover:bg-[var(--amber-light)] transition-colors"
          >
            <Download size={13} />
            Download Notes
          </button>
          <button
            onClick={() => { setAnalysis(null); setAppState("landing"); }}
            className="px-3 py-1.5 text-xs border border-[var(--ink-700)] text-[var(--ink-500)] rounded-lg hover:border-[var(--ink-600)] transition-colors"
          >
            New Paper
          </button>
        </div>
      </header>

      {/* Tab bar */}
      <div className="border-b border-[var(--ink-800)] px-6 overflow-x-auto">
        <div className="flex gap-0 min-w-max">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm border-b-2 transition-colors whitespace-nowrap ${
                activeTab === id
                  ? "border-[var(--amber)] text-[var(--amber)]"
                  : "border-transparent text-[var(--ink-500)] hover:text-[var(--ink-300)]"
              }`}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <main className="max-w-5xl mx-auto p-6">
        {activeTab === "breakdown" && <Decomposition data={a.decomposition} />}
        {activeTab === "critique" && <CriticPanel data={a.critique} />}
        {activeTab === "tutor" && <TutorChat paperId={a.paper_id} />}
        {activeTab === "notes" && (
          <div className="prose-academic animate-fade-up">
            <ReactMarkdown>{a.notes_markdown}</ReactMarkdown>
          </div>
        )}
      </main>

      {showQuiz && (
        <QuizModal paperId={a.paper_id} onClose={() => setShowQuiz(false)} />
      )}
    </div>
  );
}
