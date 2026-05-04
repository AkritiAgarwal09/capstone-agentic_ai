"use client";

import { useState, useRef, DragEvent } from "react";
import { Upload, Link } from "lucide-react";

interface Props {
  onAnalyze: (type: "arxiv" | "pdf", value: string | File) => void;
}

export default function PaperInput({ onAnalyze }: Props) {
  const [mode, setMode] = useState<"arxiv" | "pdf">("arxiv");
  const [arxivValue, setArxivValue] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (mode === "arxiv" && arxivValue.trim()) {
      onAnalyze("arxiv", arxivValue.trim());
    } else if (mode === "pdf" && selectedFile) {
      onAnalyze("pdf", selectedFile);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file?.type === "application/pdf") setSelectedFile(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const canSubmit = mode === "arxiv" ? !!arxivValue.trim() : !!selectedFile;

  return (
    <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-xl p-6 animate-fade-up">
      {/* Mode tabs */}
      <div className="flex gap-1 bg-[var(--ink-800)] rounded-lg p-1 mb-5">
        {(["arxiv", "pdf"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-2 text-sm rounded-md transition-colors font-medium ${
              mode === m
                ? "bg-[var(--ink-700)] text-[var(--ink-50)]"
                : "text-[var(--ink-500)] hover:text-[var(--ink-300)]"
            }`}
          >
            {m === "arxiv" ? "arXiv ID / URL" : "PDF Upload"}
          </button>
        ))}
      </div>

      {mode === "arxiv" ? (
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Link
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink-500)]"
            />
            <input
              type="text"
              value={arxivValue}
              onChange={(e) => setArxivValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder="e.g. 1706.03762 or https://arxiv.org/abs/..."
              className="w-full bg-[var(--ink-800)] border border-[var(--ink-600)] text-[var(--ink-100)] placeholder:text-[var(--ink-600)] rounded-lg pl-9 pr-4 py-3 text-sm focus:outline-none focus:border-[var(--amber)] transition-colors"
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="px-5 py-3 bg-[var(--amber)] text-[var(--ink-950)] rounded-lg font-semibold text-sm hover:bg-[var(--amber-light)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Analyze
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={() => setIsDragging(false)}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? "border-[var(--amber)] bg-[var(--amber)]/5"
                : "border-[var(--ink-600)] hover:border-[var(--ink-500)]"
            }`}
          >
            <Upload
              size={28}
              className="mx-auto mb-3 text-[var(--ink-500)]"
            />
            {selectedFile ? (
              <p className="text-[var(--ink-200)] font-medium text-sm">
                {selectedFile.name}
              </p>
            ) : (
              <>
                <p className="text-[var(--ink-300)] text-sm font-medium">
                  Drop a PDF here or click to browse
                </p>
                <p className="text-[var(--ink-600)] text-xs mt-1">
                  PDF files only
                </p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) setSelectedFile(f);
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="w-full py-3 bg-[var(--amber)] text-[var(--ink-950)] rounded-lg font-semibold text-sm hover:bg-[var(--amber-light)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Analyze PDF
          </button>
        </div>
      )}
    </div>
  );
}
