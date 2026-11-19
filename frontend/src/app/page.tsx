"use client";

import { useEffect, useRef, useState } from "react";
import { AboutModal } from "./components/AboutModal";
import { AnswerCard } from "./components/AnswerCard";
import { ChatInput } from "./components/ChatInput";
import { EmptyState } from "./components/EmptyState";
import { Header } from "./components/Header";
import { SettingsPanel } from "./components/SettingsPanel";
import { Sidebar } from "./components/Sidebar";
import { UserMessage } from "./components/UserMessage";
import { DEFAULT_API, getProviders, postRun } from "./lib/api";
import type { Conversation, ModelOption, Msg } from "./lib/types";

export default function Home() {
  const [apiBase, setApiBase] = useState(DEFAULT_API);
  const [showSettings, setShowSettings] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [models, setModels] = useState<ModelOption[]>([]);
  const [sel, setSel] = useState<string>(""); // "provider|model"
  const inputRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Load selectable models from the backend.
  useEffect(() => {
    getProviders(apiBase)
      .then((d) => {
        const list = d.providers || [];
        setModels(list);
        if (!list.length) return;
        // Priority: Groq first (stronger SQL), then backend default, then first listed.
        const groq = list.find((m) => m.provider === "groq");
        const def = `${d.default_provider}|${d.default_model}`;
        const hasDef = list.some((m) => `${m.provider}|${m.model}` === def);
        if (groq) setSel(`${groq.provider}|${groq.model}`);
        else setSel(hasDef ? def : `${list[0].provider}|${list[0].model}`);
      })
      .catch(() => {});
  }, [apiBase]);

  // Restore saved API base + conversations.
  useEffect(() => {
    try {
      const savedApi = localStorage.getItem("ads_api_base");
      if (savedApi) setApiBase(savedApi);
      const saved = localStorage.getItem("ads_convs");
      if (saved) {
        const c: Conversation[] = JSON.parse(saved);
        setConvs(c);
        if (c.length) setActiveId(c[0].id);
      }
    } catch {}
  }, []);

  function persist(c: Conversation[]) {
    try {
      localStorage.setItem("ads_convs", JSON.stringify(c.slice(0, 30)));
    } catch {}
  }
  function saveApiBase(v: string) {
    setApiBase(v);
    try {
      localStorage.setItem("ads_api_base", v);
    } catch {}
  }

  const active = convs.find((c) => c.id === activeId) || null;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [active?.messages.length, loading]);

  async function run(q?: string) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    setLoading(true);
    setError("");
    setQuestion("");
    setPending(text);
    try {
      const [provider, model] = sel.includes("|") ? sel.split("|") : [undefined, undefined];
      const data = await postRun(apiBase, text, provider, model);
      if (data.status === "rate_limited") {
        setError(`⏳ ${data.message || "The AI usage limit has been reached. Please try again later."}`);
        return;
      }
      if (data.status === "error") {
        setError(`Backend error: ${data.error}`);
        return;
      }
      if (data.fell_back_to === "gemini") {
        setError("⏳ Groq limit reached — answered with Gemini (Flash-Lite) instead.");
      }
      const msg: Msg = { id: crypto.randomUUID(), question: text, result: data };
      setConvs((prev) => {
        let next: Conversation[];
        if (activeId && prev.some((c) => c.id === activeId)) {
          next = prev.map((c) =>
            c.id === activeId ? { ...c, messages: [...c.messages, msg], ts: Date.now() } : c,
          );
        } else {
          const conv: Conversation = { id: crypto.randomUUID(), title: text, messages: [msg], ts: Date.now() };
          setActiveId(conv.id);
          next = [conv, ...prev];
        }
        persist(next);
        return next;
      });
    } catch {
      setError(
        `Could not reach the backend at ${apiBase}. It may be waking up (free tier sleeps ~15 min — first call takes ~50s). Try again, or set the URL (⚙).`,
      );
    } finally {
      setLoading(false);
      setPending(null);
    }
  }

  function newChat() {
    setActiveId(null);
    setError("");
    setQuestion("");
    setSidebarOpen(false);
  }
  function deleteConv(id: string) {
    const c = convs.filter((x) => x.id !== id);
    setConvs(c);
    persist(c);
    if (activeId === id) setActiveId(c[0]?.id ?? null);
  }
  function editPrompt(text: string) {
    setQuestion(text);
    inputRef.current?.focus();
  }

  return (
    <div className="flex h-[100dvh] overflow-hidden text-neutral-800">
      <Sidebar
        convs={convs}
        activeId={activeId}
        open={sidebarOpen}
        onNew={newChat}
        onSelect={(id) => {
          setActiveId(id);
          setSidebarOpen(false);
        }}
        onDelete={deleteConv}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col h-full min-w-0">
        <Header
          onMenu={() => setSidebarOpen(true)}
          onAbout={() => setShowAbout(true)}
          onToggleSettings={() => setShowSettings((v) => !v)}
        />

        {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
        {showSettings && <SettingsPanel apiBase={apiBase} onChange={saveApiBase} />}

        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-5">
            {!active && !loading && !pending && <EmptyState onPick={(ex) => run(ex)} />}

            {active?.messages.map((m) => (
              <div key={m.id} className="space-y-3">
                <UserMessage text={m.question} onEdit={() => editPrompt(m.question)} />
                <AnswerCard result={m.result} />
              </div>
            ))}

            {loading && (
              <div className="space-y-3">
                {pending && (
                  <div className="flex justify-end">
                    <div className="bg-violet-600 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm max-w-[85%]">
                      {pending}
                    </div>
                  </div>
                )}
                <div className="flex justify-start">
                  <div className="card rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-neutral-500">
                    <span className="inline-block animate-pulse">
                      Agents working: planning → SQL → EDA → ML → chart → report…
                    </span>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div
                className={`card p-4 text-sm ${
                  error.startsWith("⏳")
                    ? "text-amber-700 border-amber-300 bg-amber-50"
                    : "text-red-600 border-red-200"
                }`}
              >
                {error}
              </div>
            )}
            <div ref={endRef} />
          </div>
        </div>

        <ChatInput
          value={question}
          onChange={setQuestion}
          onSend={() => run()}
          loading={loading}
          hasActiveChat={!!active}
          models={models}
          selectedModel={sel}
          onSelectModel={setSel}
          inputRef={inputRef}
        />
      </div>
    </div>
  );
}
