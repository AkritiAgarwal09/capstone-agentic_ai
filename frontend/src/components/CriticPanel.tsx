"use client";

import { CriticResult, CriticFinding } from "@/lib/api";

interface Props {
  data: CriticResult;
}

const SEVERITY_STYLES: Record<string, { badge: string; border: string }> = {
  minor: {
    badge: "bg-[var(--ink-800)] text-[var(--ink-400)] border-[var(--ink-700)]",
    border: "border-l-[var(--ink-600)]",
  },
  moderate: {
    badge: "bg-[var(--amber)]/15 text-[var(--amber)] border-[var(--amber)]/30",
    border: "border-l-[var(--amber)]",
  },
  significant: {
    badge:
      "bg-[var(--crimson)]/15 text-[var(--crimson-light)] border-[var(--crimson)]/30",
    border: "border-l-[var(--crimson)]",
  },
};

function FindingCard({ f }: { f: CriticFinding }) {
  const style =
    SEVERITY_STYLES[f.severity.toLowerCase()] || SEVERITY_STYLES.minor;

  return (
    <div
      className={`bg-[var(--ink-900)] border border-[var(--ink-700)] border-l-2 ${style.border} rounded-xl p-4 flex flex-col gap-2`}
    >
      <div className="flex items-center gap-2">
        <span
          className={`text-xs font-mono px-2 py-0.5 rounded border ${style.badge}`}
        >
          {f.severity}
        </span>
        <span className="text-xs text-[var(--ink-500)] font-mono uppercase tracking-wide">
          {f.category}
        </span>
      </div>
      <p className="text-[var(--ink-300)] text-sm leading-relaxed">{f.finding}</p>
    </div>
  );
}

function BulletList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-xl p-5">
      <h3 className="text-[var(--ink-400)] text-xs font-mono uppercase tracking-wide mb-3">
        {title}
      </h3>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm text-[var(--ink-300)]">
            <span className="text-[var(--crimson-light)] mt-0.5">×</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function CriticPanel({ data }: Props) {
  return (
    <div className="space-y-6 animate-fade-up">
      {/* Overall assessment */}
      <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-xl p-6">
        <h2 className="font-serif text-xl text-[var(--ink-50)] mb-3">
          Overall Assessment
        </h2>
        <p className="text-[var(--ink-300)] text-sm leading-relaxed">
          {data.overall_assessment}
        </p>
      </div>

      {/* Findings */}
      {data.findings.length > 0 && (
        <div>
          <h3 className="text-[var(--ink-400)] text-xs font-mono uppercase tracking-wide mb-3">
            Findings ({data.findings.length})
          </h3>
          <div className="space-y-3 stagger">
            {data.findings.map((f, i) => (
              <FindingCard key={i} f={f} />
            ))}
          </div>
        </div>
      )}

      {/* Bullet sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BulletList
          title="What This Paper Does NOT Prove"
          items={data.what_paper_does_not_prove}
        />
        <BulletList
          title="Common Misreadings"
          items={data.common_misreadings}
        />
        {data.replication_concerns.length > 0 && (
          <div className="md:col-span-2">
            <BulletList
              title="Replication Concerns"
              items={data.replication_concerns}
            />
          </div>
        )}
      </div>
    </div>
  );
}
