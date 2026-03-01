import { useState, useEffect, useRef } from "react";

interface Props {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  cumulativeScore?: number;
  verdict?: string;
  recommendation?: string;
  audioLevel?: number;
  hasResults?: boolean;
}

export default function MicRecorder({ isRecording, onStart, onStop, cumulativeScore, verdict, recommendation, audioLevel = 0, hasResults = false }: Props) {
  const [countdown, setCountdown] = useState(5);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Countdown timer for first chunk wait
  useEffect(() => {
    if (isRecording && !hasResults) {
      // Defer the reset to avoid synchronous setState inside an effect body
      const init = setTimeout(() => setCountdown(5), 0);
      timerRef.current = setInterval(() => {
        setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
      return () => {
        clearTimeout(init);
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      };
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [isRecording, hasResults]);

  // Generate audio level bars
  const bars = 5;
  const barHeights = Array.from({ length: bars }, (_, i) => {
    const threshold = (i + 1) / bars;
    return audioLevel >= threshold ? 1 : audioLevel >= threshold - 0.1 ? 0.5 : 0.2;
  });

  return (
    <div className="flex flex-col items-center space-y-6 py-8">
      <button
        onClick={isRecording ? onStop : onStart}
        className={`w-24 h-24 rounded-full flex items-center justify-center text-white text-lg font-bold transition-all ${
          isRecording
            ? "bg-red-600 hover:bg-red-700 animate-pulse"
            : "bg-blue-600 hover:bg-blue-700"
        }`}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
      >
        {isRecording ? "STOP" : "REC"}
      </button>

      {/* Audio level visualization */}
      {isRecording && (
        <div className="flex items-end gap-1 h-8">
          {barHeights.map((h, i) => (
            <div
              key={i}
              className="w-2 rounded-sm transition-all duration-100"
              style={{
                height: `${Math.max(4, h * 32)}px`,
                backgroundColor: audioLevel > 0.5
                  ? "#f59e0b"
                  : audioLevel > 0.2
                  ? "#22c55e"
                  : "#6b7280",
              }}
            />
          ))}
        </div>
      )}

      <p className="text-gray-400 text-sm">
        {isRecording
          ? "Recording... Click to stop and get final analysis."
          : "Click to start recording from your microphone."}
      </p>

      {/* Countdown timer while waiting for first chunk */}
      {isRecording && !hasResults && (
        <p className="text-blue-400 text-sm animate-pulse">
          Analyzing first chunk... {countdown}s
        </p>
      )}

      {isRecording && cumulativeScore !== undefined && (
        <div className="flex flex-col items-center space-y-3">
          <p className="text-lg font-mono">
            Live Score:{" "}
            <span
              className={
                cumulativeScore < 0.3
                  ? "text-green-400"
                  : cumulativeScore < 0.6
                  ? "text-yellow-400"
                  : cumulativeScore < 0.85
                  ? "text-orange-400"
                  : "text-red-400"
              }
            >
              {Math.round(cumulativeScore * 100)}%
            </span>
          </p>
          {verdict && (
            <span className={`text-sm font-bold px-3 py-1 rounded ${
              verdict === "SAFE" ? "bg-green-900 text-green-300" :
              verdict === "SUSPICIOUS" ? "bg-yellow-900 text-yellow-300" :
              verdict === "LIKELY_SCAM" ? "bg-orange-900 text-orange-300" :
              "bg-red-900 text-red-300"
            }`}>
              {verdict.replace("_", " ")}
            </span>
          )}
          {recommendation && (
            <p className="text-sm text-blue-400 italic text-center max-w-md">
              {recommendation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
