import { useState } from "react";
import type { ScamReport } from "../../types/scamReport";
import ScamGauge from "./ScamGauge";
import VerdictBadge from "./VerdictBadge";
import SignalList from "./SignalList";
import RecommendationBox from "./RecommendationBox";

interface Props {
  report: ScamReport | null;
  isLoading?: boolean;
}

function formatReportForClipboard(report: ScamReport): string {
  const analysis = report.audio_analysis || report.text_analysis;
  if (!analysis) return "";

  const lines: string[] = [
    `CallShield Analysis Results`,
    `===========================`,
    `Score: ${Math.round(report.combined_score * 100)}%`,
    `Verdict: ${analysis.verdict}`,
    `Confidence: ${Math.round(analysis.confidence * 100)}%`,
    ``,
  ];

  if (analysis.transcript_summary) {
    lines.push(`Summary: ${analysis.transcript_summary}`, ``);
  }

  if (analysis.signals.length > 0) {
    lines.push(`Signals:`);
    for (const s of analysis.signals) {
      lines.push(`  [${s.severity.toUpperCase()}] ${s.category}: ${s.detail}`);
    }
    lines.push(``);
  }

  lines.push(`Recommendation: ${analysis.recommendation}`);
  return lines.join("\n");
}

export default function AnalysisPanel({ report, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-12 text-center">
        <div className="animate-spin w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
        <p className="text-gray-400 mt-4">Analyzing for scam signals...</p>
      </div>
    );
  }

  const [copied, setCopied] = useState(false);

  if (!report) return null;

  const analysis = report.audio_analysis || report.text_analysis;
  if (!analysis) return null;

  const handleCopy = async () => {
    try {
      const text = formatReportForClipboard(report);
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      {/* Score and verdict row */}
      <div className="flex flex-col items-center space-y-4 sm:flex-row sm:justify-around sm:space-y-0">
        <div className="relative">
          <ScamGauge score={report.combined_score} />
        </div>
        <div className="text-center space-y-2">
          <VerdictBadge verdict={analysis.verdict} />
          <p className="text-gray-500 text-xs">
            Confidence: {Math.round(analysis.confidence * 100)}%
          </p>
          <p className="text-gray-500 text-xs">
            Processed in {Math.round(report.processing_time_ms)}ms
          </p>
        </div>
      </div>

      {/* Transcript summary (audio mode only) */}
      {analysis.transcript_summary && (
        <div className="bg-gray-700/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-2">
            Call Summary
          </h3>
          <p className="text-gray-200 text-sm">{analysis.transcript_summary}</p>
        </div>
      )}

      {/* Signals */}
      <SignalList signals={analysis.signals} />

      {/* Recommendation */}
      <RecommendationBox recommendation={analysis.recommendation} />

      {/* Copy Results button */}
      <div className="flex justify-center pt-2">
        <button
          onClick={handleCopy}
          className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
        >
          {copied ? "Copied!" : "Copy Results"}
        </button>
      </div>
    </div>
  );
}
