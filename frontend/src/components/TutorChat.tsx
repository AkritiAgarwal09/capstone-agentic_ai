"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send } from "lucide-react";
import { askTutor, TutorResponse, ConversationMessage } from "@/lib/api";

interface Props {
  paperId: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  response?: TutorResponse;
}

export default function TutorChat({ paperId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const history: ConversationMessage[] = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const resp = await askTutor(paperId, question, history.slice(-6));
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: resp.explanation, response: resp },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${e instanceof Error ? e.message : "Request failed"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[70vh] animate-fade-up">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center py-16 text-[var(--ink-600)]">
            <p className="font-serif text-xl text-[var(--ink-400)] mb-2">
              Ask Professor anything
            </p>
            <p className="text-sm">
              Questions about methodology, results, implications…
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "flex justify-end" : ""}>
            {msg.role === "user" ? (
              <div className="max-w-[75%] bg-[var(--amber)]/15 border border-[var(--amber)]/25 rounded-2xl rounded-tr-sm px-4 py-3 text-sm text-[var(--ink-100)]">
                {msg.content}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-[var(--ink-900)] border border-[var(--ink-700)] rounded-2xl rounded-tl-sm p-5">
                  <div className="prose-academic text-sm">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>

                  {msg.response?.analogy && (
                    <div className="mt-3 p-3 bg-[var(--ink-800)] border border-[var(--ink-700)] rounded-lg">
                      <p className="text-xs font-mono text-[var(--amber)] uppercase tracking-wide mb-1">
                        Analogy
                      </p>
                      <p className="text-[var(--ink-300)] text-sm italic">
                        {msg.response.analogy}
                      </p>
                    </div>
                  )}

                  {msg.response?.simplified_version && (
                    <div className="mt-3 p-3 bg-[var(--sage)]/10 border border-[var(--sage)]/25 rounded-lg">
                      <p className="text-xs font-mono text-[var(--sage-light)] uppercase tracking-wide mb-1">
                        Simpler explanation
                      </p>
                      <p className="text-[var(--ink-300)] text-sm">
                        {msg.response.simplified_version}
                      </p>
                    </div>
                  )}
                </div>

                {/* Follow-ups + simplify chips */}
                {msg.response && (
                  <div className="flex flex-wrap gap-2 pl-1">
                    <button
                      onClick={() => send("Can you explain that more simply?")}
                      className="text-xs px-3 py-1.5 bg-[var(--ink-800)] border border-[var(--ink-600)] text-[var(--ink-400)] rounded-full hover:border-[var(--sage)] hover:text-[var(--sage-light)] transition-colors"
                    >
                      Explain simpler ↓
                    </button>
                    {msg.response.follow_up_questions.map((q, j) => (
                      <button
                        key={j}
                        onClick={() => send(q)}
                        className="text-xs px-3 py-1.5 bg-[var(--ink-800)] border border-[var(--ink-600)] text-[var(--ink-400)] rounded-full hover:border-[var(--amber)] hover:text-[var(--amber)] transition-colors text-left"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-[var(--ink-500)] text-sm pl-1">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 bg-[var(--ink-500)] rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            Professor is thinking…
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="flex gap-3 pt-3 border-t border-[var(--ink-800)]">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
          placeholder="Ask a question about the paper…"
          disabled={loading}
          className="flex-1 bg-[var(--ink-900)] border border-[var(--ink-700)] text-[var(--ink-100)] placeholder:text-[var(--ink-600)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[var(--amber)] transition-colors disabled:opacity-50"
        />
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          className="px-4 py-3 bg-[var(--amber)] text-[var(--ink-950)] rounded-xl hover:bg-[var(--amber-light)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
