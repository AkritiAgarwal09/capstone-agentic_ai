"use client";

import { useState } from "react";
import { X, CheckCircle, XCircle } from "lucide-react";
import { getQuiz, QuizResult, QuizQuestion } from "@/lib/api";

interface Props {
  paperId: string;
  onClose: () => void;
}

export default function QuizModal({ paperId, onClose }: Props) {
  const [quiz, setQuiz] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [done, setDone] = useState(false);

  const loadQuiz = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getQuiz(paperId);
      setQuiz(result);
      setAnswers(new Array(result.questions.length).fill(null));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate quiz");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (idx: number) => {
    if (selected !== null) return;
    setSelected(idx);
  };

  const handleNext = () => {
    if (!quiz) return;
    const newAnswers = [...answers];
    newAnswers[currentQ] = selected;
    setAnswers(newAnswers);

    if (currentQ < quiz.questions.length - 1) {
      setCurrentQ(currentQ + 1);
      setSelected(null);
    } else {
      setDone(true);
    }
  };

  const score = done
    ? answers.filter(
        (a, i) => quiz && a === quiz.questions[i].correct_index
      ).length
    : 0;

  const q: QuizQuestion | undefined = quiz?.questions[currentQ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-2xl w-full max-w-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[var(--ink-800)]">
          <h2 className="font-serif text-lg text-[var(--ink-50)]">
            Comprehension Quiz
          </h2>
          <button
            onClick={onClose}
            className="text-[var(--ink-500)] hover:text-[var(--ink-200)] transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          {/* Initial state */}
          {!quiz && !loading && !error && (
            <div className="text-center py-6">
              <p className="text-[var(--ink-400)] text-sm mb-6">
                5 questions testing understanding, not memorization.
              </p>
              <button
                onClick={loadQuiz}
                className="px-6 py-3 bg-[var(--amber)] text-[var(--ink-950)] rounded-xl font-semibold hover:bg-[var(--amber-light)] transition-colors"
              >
                Generate Quiz
              </button>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <div className="w-10 h-10 border-3 border-[var(--ink-700)] border-t-[var(--amber)] rounded-full animate-spin mx-auto mb-4" />
              <p className="text-[var(--ink-400)] text-sm">
                Generating questions…
              </p>
            </div>
          )}

          {error && (
            <div className="text-center py-6">
              <p className="text-[var(--crimson-light)] text-sm mb-4">{error}</p>
              <button
                onClick={loadQuiz}
                className="px-4 py-2 text-sm border border-[var(--ink-600)] text-[var(--ink-300)] rounded-lg hover:border-[var(--amber)] transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {/* Score screen */}
          {done && quiz && (
            <div className="text-center py-4 animate-fade-up">
              <div className="text-5xl font-serif text-[var(--amber)] mb-2">
                {score}/{quiz.questions.length}
              </div>
              <p className="text-[var(--ink-400)] text-sm mb-6">
                {score === quiz.questions.length
                  ? "Perfect score!"
                  : score >= quiz.questions.length * 0.6
                  ? "Good understanding"
                  : "Worth reviewing the paper again"}
              </p>
              {/* Answer review */}
              <div className="space-y-3 text-left mb-6">
                {quiz.questions.map((q, i) => {
                  const correct = answers[i] === q.correct_index;
                  return (
                    <div
                      key={i}
                      className={`p-3 rounded-xl border text-sm ${
                        correct
                          ? "border-[var(--sage)]/30 bg-[var(--sage)]/8"
                          : "border-[var(--crimson)]/30 bg-[var(--crimson)]/8"
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {correct ? (
                          <CheckCircle
                            size={15}
                            className="text-[var(--sage-light)] mt-0.5 shrink-0"
                          />
                        ) : (
                          <XCircle
                            size={15}
                            className="text-[var(--crimson-light)] mt-0.5 shrink-0"
                          />
                        )}
                        <div>
                          <p className="text-[var(--ink-200)] mb-1">{q.question}</p>
                          {!correct && (
                            <p className="text-[var(--ink-500)] text-xs">
                              Correct: {q.options[q.correct_index]}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <button
                onClick={onClose}
                className="px-5 py-2.5 bg-[var(--ink-800)] border border-[var(--ink-600)] text-[var(--ink-300)] rounded-xl text-sm hover:border-[var(--ink-500)] transition-colors"
              >
                Close
              </button>
            </div>
          )}

          {/* Active question */}
          {q && !done && (
            <div className="animate-fade-up">
              {/* Progress */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono text-[var(--ink-500)]">
                  Question {currentQ + 1} of {quiz!.questions.length}
                </span>
                <div className="flex gap-1">
                  {quiz!.questions.map((_, i) => (
                    <div
                      key={i}
                      className={`h-1 w-6 rounded-full transition-colors ${
                        i < currentQ
                          ? "bg-[var(--amber)]"
                          : i === currentQ
                          ? "bg-[var(--amber)]/50"
                          : "bg-[var(--ink-700)]"
                      }`}
                    />
                  ))}
                </div>
              </div>

              <p className="text-[var(--ink-100)] text-sm font-medium mb-4 leading-relaxed">
                {q.question}
              </p>

              <div className="space-y-2 mb-4">
                {q.options.map((opt, i) => {
                  const isSelected = selected === i;
                  const isCorrect = selected !== null && i === q.correct_index;
                  const isWrong =
                    selected !== null && isSelected && i !== q.correct_index;

                  let cls =
                    "w-full text-left px-4 py-3 rounded-xl border text-sm transition-colors ";
                  if (selected === null) {
                    cls +=
                      "border-[var(--ink-700)] text-[var(--ink-300)] hover:border-[var(--ink-500)] hover:text-[var(--ink-100)]";
                  } else if (isCorrect) {
                    cls +=
                      "border-[var(--sage)] bg-[var(--sage)]/12 text-[var(--sage-light)]";
                  } else if (isWrong) {
                    cls +=
                      "border-[var(--crimson)] bg-[var(--crimson)]/12 text-[var(--crimson-light)]";
                  } else {
                    cls += "border-[var(--ink-800)] text-[var(--ink-600)]";
                  }

                  return (
                    <button key={i} onClick={() => handleSelect(i)} className={cls}>
                      <span className="font-mono mr-2 text-xs opacity-60">
                        {String.fromCharCode(65 + i)}.
                      </span>
                      {opt}
                    </button>
                  );
                })}
              </div>

              {selected !== null && (
                <div className="mb-4 p-3 bg-[var(--ink-800)] rounded-xl border border-[var(--ink-700)]">
                  <p className="text-xs font-mono text-[var(--ink-500)] uppercase tracking-wide mb-1">
                    Explanation
                  </p>
                  <p className="text-[var(--ink-300)] text-sm">{q.explanation}</p>
                </div>
              )}

              <button
                onClick={handleNext}
                disabled={selected === null}
                className="w-full py-3 bg-[var(--amber)] text-[var(--ink-950)] rounded-xl font-semibold text-sm hover:bg-[var(--amber-light)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {currentQ < quiz!.questions.length - 1 ? "Next Question" : "See Results"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
