"use client";

import { DecomposedPaper, PaperSection } from "@/lib/api";
import {
  HelpCircle,
  BookOpen,
  Cpu,
  BarChart2,
} from "lucide-react";

interface Props {
  data: DecomposedPaper;
}

const SECTION_CONFIG = [
  {
    key: "problem" as const,
    label: "Problem Statement",
    icon: HelpCircle,
    color: "text-[var(--amber)]",
    border: "border-[var(--amber)]/30",
  },
  {
    key: "prior_work" as const,
    label: "Prior Work",
    icon: BookOpen,
    color: "text-[var(--sage-light)]",
    border: "border-[var(--sage)]/30",
  },
  {
    key: "methodology" as const,
    label: "Methodology",
    icon: Cpu,
    color: "text-blue-400",
    border: "border-blue-400/20",
  },
  {
    key: "results" as const,
    label: "Results",
    icon: BarChart2,
    color: "text-purple-400",
    border: "border-purple-400/20",
  },
];

const DIFFICULTY_STYLES: Record<string, string> = {
  beginner: "bg-[var(--sage)]/20 text-[var(--sage-light)] border-[var(--sage)]/30",
  intermediate: "bg-[var(--amber)]/20 text-[var(--amber)] border-[var(--amber)]/30",
  advanced: "bg-[var(--crimson)]/20 text-[var(--crimson-light)] border-[var(--crimson)]/30",
};

function SectionCard({
  section,
  label,
  icon: Icon,
  color,
  border,
}: {
  section: PaperSection;
  label: string;
  icon: React.ElementType;
  color: string;
  border: string;
}) {
  const diffStyle =
    DIFFICULTY_STYLES[section.difficulty.toLowerCase()] ||
    DIFFICULTY_STYLES.intermediate;

  return (
    <div
      className={`bg-[var(--ink-900)] border ${border} rounded-xl p-5 flex flex-col gap-3`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={18} className={color} />
          <h3 className={`font-semibold text-sm ${color}`}>{label}</h3>
        </div>
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full border font-mono ${diffStyle}`}
        >
          {section.difficulty}
        </span>
      </div>
      <p className="text-[var(--ink-300)] text-sm leading-relaxed">
        {section.summary}
      </p>
      <div className="flex flex-wrap gap-1.5 mt-1">
        {section.key_terms.map((term) => (
          <span
            key={term}
            className="text-xs font-mono bg-[var(--ink-800)] text-[var(--ink-400)] px-2 py-0.5 rounded border border-[var(--ink-700)]"
          >
            {term}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function Decomposition({ data }: Props) {
  const overallStyle =
    DIFFICULTY_STYLES[data.overall_difficulty.toLowerCase()] ||
    DIFFICULTY_STYLES.intermediate;

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Paper header */}
      <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-xl p-6">
        <div className="flex items-start justify-between gap-4 mb-3">
          <h2 className="font-serif text-2xl text-[var(--ink-50)] leading-tight">
            {data.title}
          </h2>
          <span
            className={`shrink-0 text-xs px-2.5 py-1 rounded-full border font-mono ${overallStyle}`}
          >
            {data.overall_difficulty}
          </span>
        </div>
        {(data.authors.length > 0 || data.year) && (
          <p className="text-[var(--ink-500)] text-sm mb-3">
            {data.authors.slice(0, 5).join(", ")}
            {data.authors.length > 5 ? " et al." : ""}
            {data.year ? ` · ${data.year}` : ""}
          </p>
        )}
        <blockquote className="border-l-2 border-[var(--amber)] pl-4 text-[var(--ink-300)] italic text-sm">
          {data.one_line_summary}
        </blockquote>
      </div>

      {/* Section cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger">
        {SECTION_CONFIG.map(({ key, label, icon, color, border }) => (
          <SectionCard
            key={key}
            section={data[key]}
            label={label}
            icon={icon}
            color={color}
            border={border}
          />
        ))}
      </div>
    </div>
  );
}
