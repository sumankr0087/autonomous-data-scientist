"use client";

import { CopyButton } from "./CopyButton";
import { EditButton } from "./EditButton";

export function UserMessage({ text, onEdit }: { text: string; onEdit: () => void }) {
  return (
    <div className="flex flex-col items-end gap-1 group">
      <div className="bg-violet-600 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm max-w-[85%]">
        {text}
      </div>
      <div className="flex gap-2 text-neutral-400 opacity-0 group-hover:opacity-100 transition">
        <CopyButton text={text} />
        <EditButton onEdit={onEdit} />
      </div>
    </div>
  );
}
