"use client";

import { useState } from "react";
import { FiCopy, FiCheck } from "react-icons/fi";

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard?.writeText(text).then(
      () => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      },
      () => {},
    );
  };

  return (
    <button
      onClick={copy}
      title="Copy prompt"
      className="hover:text-violet-600 flex items-center gap-1 text-xs"
    >
      {copied ? <FiCheck size={13} /> : <FiCopy size={13} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}
