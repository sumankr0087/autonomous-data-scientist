"use client";

import { RefObject } from "react";
import { FiSend } from "react-icons/fi";
import type { ModelOption } from "../lib/types";

export function ChatInput({
  value,
  onChange,
  onSend,
  loading,
  hasActiveChat,
  models,
  selectedModel,
  onSelectModel,
  inputRef,
}: {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  loading: boolean;
  hasActiveChat: boolean;
  models: ModelOption[];
  selectedModel: string;
  onSelectModel: (value: string) => void;
  inputRef: RefObject<HTMLInputElement>;
}) {
  return (
    <div className="border-t border-black/10 bg-white/70 backdrop-blur px-4 py-3">
      <div className="max-w-3xl mx-auto">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSend()}
            placeholder={hasActiveChat ? "Ask a follow-up in this chat…" : "Ask a business question…"}
            className="flex-1 card rounded-full px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
          />
          <button
            onClick={onSend}
            disabled={loading || !value.trim()}
            className="btn-primary !rounded-full !px-4 flex items-center gap-2"
          >
            <FiSend />
          </button>
        </div>
        {models.length > 0 && (
          <div className="flex items-center gap-2 mt-2 px-1">
            <span className="text-[0.7rem] text-neutral-400">AI model:</span>
            <select
              value={selectedModel}
              onChange={(e) => onSelectModel(e.target.value)}
              title="Choose the AI model"
              className="text-xs bg-white border border-black/10 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-violet-300"
            >
              {models.map((m) => (
                <option key={m.label} value={`${m.provider}|${m.model}`}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
