"use client";

import { FiPlus, FiTrash2 } from "react-icons/fi";
import type { Conversation } from "../lib/types";

export function Sidebar({
  convs,
  activeId,
  open,
  onNew,
  onSelect,
  onDelete,
  onClose,
}: {
  convs: Conversation[];
  activeId: string | null;
  open: boolean;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}) {
  return (
    <>
      <aside
        className={`${
          open ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 fixed md:static z-30 w-64 h-[100dvh] bg-white/80 backdrop-blur border-r border-black/10 flex flex-col transition-transform`}
      >
        <div className="p-3">
          <button onClick={onNew} className="w-full flex items-center justify-center gap-2 btn-primary">
            <FiPlus /> New analysis
          </button>
        </div>
        <div className="px-3 text-[0.65rem] uppercase tracking-widest text-neutral-400">Conversations</div>
        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
          {convs.length === 0 && <p className="text-xs text-neutral-400 px-2 py-3">No conversations yet.</p>}
          {convs.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center gap-1 rounded-lg px-2 py-2 cursor-pointer text-sm ${
                c.id === activeId ? "bg-violet-100 text-violet-800" : "hover:bg-black/5"
              }`}
              onClick={() => onSelect(c.id)}
            >
              <span className="flex-1 truncate">{c.title}</span>
              <span className="text-[0.6rem] text-neutral-400">{c.messages.length}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(c.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-neutral-400 hover:text-red-500"
              >
                <FiTrash2 size={13} />
              </button>
            </div>
          ))}
        </div>
        <div className="p-3 border-t border-black/10 text-[0.65rem] text-neutral-400">
          Built by Suman Kumar ·{" "}
          <a className="text-violet-600" target="_blank" rel="noreferrer" href="https://github.com/sumankr0087/autonomous-data-scientist">
            GitHub
          </a>
        </div>
      </aside>

      {open && <div className="fixed inset-0 bg-black/20 z-20 md:hidden" onClick={onClose} />}
    </>
  );
}
