import type { Signal } from "../types/scamReport";

interface PartialResult {
  type: string;
  chunk_index?: number;
  scam_score?: number;
  cumulative_score?: number;
  verdict?: string;
  signals?: Signal[];
  recommendation?: string;
  transcript_summary?: string;
  timestamp_ms?: number;
  score_delta?: number;
  new_signals?: Signal[];
}

interface Props {
  results: PartialResult[];
  isRecording: boolean;
  visible: boolean;
  onToggle: () => void;
}

export default function StreamLog({ results, isRecording, visible, onToggle }: Props) {
  if (results.length === 0 && !isRecording) return null;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg">
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-center p-4 text-left"
      >
        <h3 className="text-white font-semibold">Live Analysis Log ({results.length} chunks)</h3>
        <span className="text-gray-400 text-sm">{visible ? "Hide" : "Show"}</span>
      </button>

      {visible && (
        <div className="px-4 pb-4 max-h-96 overflow-y-auto">
          {isRecording && results.length === 0 && (
            <p className="text-gray-400 text-sm animate-pulse">Waiting for first audio chunk (5
seconds)...</p>
          )}

          {results.map((r, i) => (
            <div key={i} className="border-b border-gray-800 pb-3 mb-3 last:border-0">
              <div className="flex justify-between items-center mb-1">
                <span className="text-gray-400 text-xs">Chunk #{r.chunk_index}</span>
                {r.timestamp_ms !== undefined && (
                  <span className="text-gray-500 text-xs">{(r.timestamp_ms / 1000).toFixed(1)}s</span>
                )}
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                  r.verdict === "SAFE" ? "bg-green-900 text-green-300" :
                  r.verdict === "SUSPICIOUS" ? "bg-yellow-900 text-yellow-300" :
                  r.verdict === "LIKELY_SCAM" ? "bg-orange-900 text-orange-300" :
                  "bg-red-900 text-red-300"
                }`}>
                  {r.verdict}
                </span>
              </div>
              <div className="flex gap-4 text-sm mb-2 items-center">
                <span className="text-gray-300">Score: <b>{Math.round((r.scam_score ?? 0) *
  100)}%</b></span>
                <span className="text-gray-300">Cumulative: <b>{Math.round((r.cumulative_score ?? 0)
  * 100)}%</b></span>
                {r.score_delta !== undefined && Math.abs(r.score_delta) > 0.05 && (
                  <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${r.score_delta > 0 ? "bg-red-900/50 text-red-300" : "bg-green-900/50 text-green-300"}`}>
                    {r.score_delta > 0 ? `\u25B2 +${Math.round(r.score_delta * 100)}%` : `\u25BC ${Math.round(r.score_delta * 100)}%`}
                  </span>
                )}
              </div>
              {r.transcript_summary && (
                <p className="text-xs text-gray-300 bg-gray-800 rounded px-2 py-1 mb-2 italic">
                  "{r.transcript_summary}"
                </p>
              )}
              {r.signals && r.signals.length > 0 && (
                <ul className="space-y-1">
                  {r.signals.map((s, j) => {
                    const isNew = r.new_signals?.some(ns => ns.category === s.category);
                    return (
                      <li key={j} className="text-xs text-gray-400 flex items-center gap-1">
                        <span className={`font-semibold ${
                          s.severity === "high" ? "text-red-400" :
                          s.severity === "medium" ? "text-yellow-400" :
                          "text-gray-300"
                        }`}>[{s.category}]</span>
                        {isNew && <span className="bg-blue-700 text-blue-200 text-xs px-1 rounded font-bold">NEW</span>}
                        {" "}{s.detail}
                      </li>
                    );
                  })}
                </ul>
              )}
              {r.recommendation && (
                <p className="text-xs text-blue-400 mt-2 italic">
                  {r.recommendation}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}