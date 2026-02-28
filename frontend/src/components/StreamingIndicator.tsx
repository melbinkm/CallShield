interface Props {
  isRecording: boolean;
  cumulativeScore?: number;
}

export default function StreamingIndicator({ isRecording, cumulativeScore }: Props) {
  if (!isRecording) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 rounded-lg p-3 shadow-lg">
      <div className="flex items-center space-x-2">
        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
        <span className="text-white text-sm font-medium">Recording</span>
        {cumulativeScore !== undefined && (
          <span
            className={`text-sm font-bold ${
              cumulativeScore < 0.3
                ? "text-green-400"
                : cumulativeScore < 0.6
                ? "text-yellow-400"
                : cumulativeScore < 0.85
                ? "text-orange-400"
                : "text-red-400"
            }`}
          >
            {Math.round(cumulativeScore * 100)}%
          </span>
        )}
      </div>
    </div>
  );
}
