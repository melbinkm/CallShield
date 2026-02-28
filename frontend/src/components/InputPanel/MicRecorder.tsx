interface Props {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  cumulativeScore?: number;
}

export default function MicRecorder({ isRecording, onStart, onStop, cumulativeScore }: Props) {
  return (
    <div className="flex flex-col items-center space-y-6 py-8">
      <button
        onClick={isRecording ? onStop : onStart}
        className={`w-24 h-24 rounded-full flex items-center justify-center text-white text-lg font-bold transition-all ${
          isRecording
            ? "bg-red-600 hover:bg-red-700 animate-pulse"
            : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {isRecording ? "STOP" : "REC"}
      </button>
      <p className="text-gray-400 text-sm">
        {isRecording
          ? "Recording... Click to stop and get final analysis."
          : "Click to start recording from your microphone."}
      </p>
      {isRecording && cumulativeScore !== undefined && (
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
      )}
    </div>
  );
}
