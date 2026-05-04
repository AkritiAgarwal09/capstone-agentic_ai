"use client";

import { ContextResult, RelatedPaper } from "@/lib/api";
import { ExternalLink } from "lucide-react";

interface Props {
  data: ContextResult;
}

function PaperCard({ paper }: { paper: RelatedPaper }) {
  const authStr =
    paper.authors.slice(0, 3).join(", ") +
    (paper.authors.length > 3 ? " et al." : "");

  return (
    <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-xl p-4 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[var(--ink-100)] font-medium text-sm leading-snug">
          {paper.title}
        </p>
        {paper.semantic_scholar_url && (
          <a
            href={paper.semantic_scholar_url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-[var(--ink-500)] hover:text-[var(--amber)] transition-colors mt-0.5"
          >
            <ExternalLink size={14} />
          </a>
        )}
      </div>
      <p className="text-[var(--ink-500)] text-xs font-mono">
        {authStr}
        {paper.year ? ` · ${paper.year}` : ""}
      </p>
      {paper.relevance_reason && (
        <p className="text-[var(--ink-400)] text-xs leading-relaxed border-t border-[var(--ink-800)] pt-2 mt-1">
          {paper.relevance_reason}
        </p>
      )}
    </div>
  );
}

export default function RelatedWork({ data }: Props) {
  return (
    <div className="space-y-6 animate-fade-up">
      {/* Field summary */}
      <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-xl p-6">
        <h2 className="font-serif text-xl text-[var(--ink-50)] mb-3">
          Research Field
        </h2>
        <p className="text-[var(--ink-300)] text-sm leading-relaxed">
          {data.field_summary}
        </p>
      </div>

      {/* Research gap */}
      <div className="bg-[var(--amber)]/8 border border-[var(--amber)]/25 rounded-xl p-5">
        <p className="text-xs font-mono text-[var(--amber)] uppercase tracking-wide mb-2">
          Gap Addressed
        </p>
        <p className="text-[var(--ink-200)] text-sm leading-relaxed">
          {data.research_gap_addressed}
        </p>
      </div>

      {/* Related papers grid */}
      {data.related_papers.length > 0 && (
        <div>
          <h3 className="text-[var(--ink-400)] text-xs font-mono uppercase tracking-wide mb-3">
            Related Papers ({data.related_papers.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 stagger">
            {data.related_papers.map((paper, i) => (
              <PaperCard key={i} paper={paper} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
