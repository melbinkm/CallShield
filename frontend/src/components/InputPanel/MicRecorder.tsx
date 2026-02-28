interface Props {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  cumulativeScore?: number;
  verdict?: string;
  recommendation?: string;
}

export default function MicRecorder({ isRecording, onStart, onStop, cumulativeScore, verdict, recommendation }: Props) {
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
      <p className="text-gray-400 text-sm">
        {isRecording
          ? "Recording... Click to stop and get final analysis."
          : "Click to start recording from your microphone."}
      </p>
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
