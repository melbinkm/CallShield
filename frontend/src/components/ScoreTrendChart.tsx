interface PartialResult {
  chunk_index?: number;
  scam_score?: number;
  cumulative_score?: number;
  verdict?: string;
}

interface Props {
  chunks: PartialResult[];
  isRecording?: boolean;
}

// Threshold lines as percentage heights in the chart
const SUSPICIOUS_PCT = 60;   // 0.60 threshold
const LIKELY_SCAM_PCT = 85;  // 0.85 threshold

function getBarColor(score: number): string {
  if (score < 0.3) return "bg-green-500";
  if (score < 0.6) return "bg-yellow-500";
  if (score < 0.85) return "bg-orange-500";
  return "bg-red-500";
}

export default function ScoreTrendChart({ chunks, isRecording }: Props) {
  // Show at most 20 most recent chunks
  const visible = chunks.length > 20 ? chunks.slice(chunks.length - 20) : chunks;
  const lastChunk = visible[visible.length - 1];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Score Trend
        </h3>
        {isRecording && (
          <span className="text-xs text-green-400 font-semibold">● Live</span>
        )}
      </div>

      {/* Chart area */}
      <div className="relative" style={{ height: "96px" }}>
        {/* Threshold lines — absolute positioned */}
        <div
          className="absolute left-0 right-0 border-t border-dashed border-orange-500/50"
          style={{ bottom: `${LIKELY_SCAM_PCT}%` }}
          title="LIKELY_SCAM threshold (85%)"
        >
          <span className="absolute right-0 -top-3 text-[9px] text-orange-500/70 font-mono">85%</span>
        </div>
        <div
          className="absolute left-0 right-0 border-t border-dashed border-yellow-500/40"
          style={{ bottom: `${SUSPICIOUS_PCT}%` }}
          title="SUSPICIOUS threshold (60%)"
        >
          <span className="absolute right-0 -top-3 text-[9px] text-yellow-500/60 font-mono">60%</span>
        </div>

        {/* Bars */}
        <div className="absolute inset-0 flex items-end gap-0.5 pr-6">
          {visible.map((chunk, i) => {
            const score = chunk.scam_score ?? 0;
            const heightPct = Math.max(2, Math.round(score * 100));
            const isLast = i === visible.length - 1;
            return (
              <div
                key={chunk.chunk_index ?? i}
                className="flex-1 flex flex-col items-center justify-end h-full group relative"
              >
                {/* Cumulative score label on last bar */}
                {isLast && lastChunk?.cumulative_score !== undefined && (
                  <span className="absolute -top-4 text-[9px] text-gray-400 font-mono whitespace-nowrap">
                    avg {Math.round(lastChunk.cumulative_score * 100)}%
                  </span>
                )}
                <div
                  className={`w-full rounded-sm transition-all duration-300 ${getBarColor(score)}`}
                  style={{ height: `${heightPct}%` }}
                  title={`Chunk #${chunk.chunk_index ?? i}: ${Math.round(score * 100)}%`}
                />
                {/* Chunk index label below bar */}
                <span className="text-[8px] text-gray-600 font-mono mt-0.5 leading-none">
                  {chunk.chunk_index ?? i + 1}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <p className="text-[10px] text-gray-600 mt-1 italic">
        Each bar = one 5s audio chunk · height = scam score
      </p>
    </div>
  );
}
