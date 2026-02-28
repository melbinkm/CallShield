import { useState } from "react";

interface Props {
  onTranscriptSubmit: (text: string) => void;
  disabled?: boolean;
}

export default function TranscriptPaster({ onTranscriptSubmit, disabled }: Props) {
  const [text, setText] = useState("");

  const charCount = text.length;
  const isOverLimit = charCount > 10000;

  return (
    <div className="space-y-3">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste a phone call transcript here..."
        disabled={disabled}
        rows={8}
        className="w-full bg-gray-700 border border-gray-600 rounded-lg p-4 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500 disabled:opacity-50"
      />
      <div className="flex justify-between items-center">
        <span className={`text-xs ${isOverLimit ? "text-red-400" : "text-gray-500"}`}>
          {charCount} / 10,000 characters
        </span>
        <button
          onClick={() => onTranscriptSubmit(text)}
          disabled={disabled || !text.trim() || isOverLimit}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Analyze
        </button>
      </div>
    </div>
  );
}
