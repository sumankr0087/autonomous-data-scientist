"use client";

import { FiEdit3 } from "react-icons/fi";

export function EditButton({ onEdit }: { onEdit: () => void }) {
  return (
    <button
      onClick={onEdit}
      title="Edit prompt"
      className="hover:text-violet-600 flex items-center gap-1 text-xs"
    >
      <FiEdit3 size={13} /> Edit
    </button>
  );
}
