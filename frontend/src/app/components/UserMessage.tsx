"use client";

import { CopyButton } from "./CopyButton";
import { EditButton } from "./EditButton";

export function UserMessage({ text, onEdit }: { text: string; onEdit: () => void }) {
  return (
    <div className="flex flex-col items-end gap-1">
      <div className="bg-violet-600 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm max-w-[85%]">
        {text}
      </div>
      <div className="flex gap-3 text-neutral-500 pr-1">
        <CopyButton text={text} />
        <EditButton onEdit={onEdit} />
      </div>
    </div>
  );
}
