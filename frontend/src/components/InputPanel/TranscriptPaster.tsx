import { useState } from "react";

interface Props {
  onTranscriptSubmit: (text: string) => void;
  disabled?: boolean;
}

const SAMPLE_SCAM_TRANSCRIPT = `Caller: Hello, this is Agent Michael Brown from the Internal Revenue Service. We've been trying to reach you regarding a serious matter with your federal tax account.

Recipient: The IRS? What's going on?

Caller: Our records indicate that you owe $4,827 in back taxes from 2023 and 2024. Due to repeated non-payment, a federal arrest warrant has been issued in your name. Local law enforcement has been notified and officers may arrive at your address within the next 45 minutes.

Recipient: An arrest warrant? That can't be right, I filed my taxes...

Caller: Ma'am, this is a time-sensitive legal matter. The good news is we can resolve this right now and cancel the warrant before it's executed. You need to make an immediate payment to settle the account.

Recipient: How would I even pay right now?

Caller: For urgent cases like this, we require payment via gift cards — either Apple or Google Play gift cards. You'll need to purchase $4,827 worth and read me the redemption codes over the phone. This is standard IRS emergency procedure.

Recipient: Gift cards? That sounds unusual...

Caller: I understand your concern, but this is a secure government payment channel. If you don't comply within the hour, I cannot stop the arrest. Do not contact your bank or anyone else — this is a confidential federal matter and discussing it could result in additional charges. Can you get to a store right now?`;

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
        <div className="flex gap-2">
          <button
            onClick={() => setText(SAMPLE_SCAM_TRANSCRIPT)}
            disabled={disabled}
            className="bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Try Sample
          </button>
          <button
            onClick={() => onTranscriptSubmit(text)}
            disabled={disabled || !text.trim() || isOverLimit}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
}
