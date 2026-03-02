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
  const [copied, setCopied] = useState(false);

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-12 text-center">
        <div className="animate-spin w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
        <p className="text-gray-400 mt-4">Analyzing for scam signals...</p>
      </div>
    );
  }

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

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "callshield-report.json";
    a.click();
    URL.revokeObjectURL(url);
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
          {report.review_required && (
            <div className="flex items-center gap-2 bg-yellow-900/40 border border-yellow-600/50 rounded px-3 py-1.5 text-yellow-300 text-xs font-medium">
              {"\u26A0"} Needs Human Review — {report.review_reason}
            </div>
          )}
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

      {/* Side-by-side comparison panel */}
      {report.audio_analysis && report.text_analysis && (() => {
        const delta = Math.round((report.audio_analysis.scam_score - report.text_analysis.scam_score) * 100);
        const audioWins = delta > 0;
        const tied = Math.abs(delta) < 1;
        return (
          <div className="bg-gray-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">
              {tied ? "Audio vs Text Comparison" : audioWins ? "Why Audio-Native Wins" : "Audio vs Text Comparison"}
            </h3>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <p className="text-xs text-gray-400 mb-1">Voxtral (audio-native)</p>
                <p className={`text-2xl font-bold ${report.audio_analysis.scam_score >= 0.6 ? "text-red-400" : report.audio_analysis.scam_score >= 0.3 ? "text-yellow-400" : "text-green-400"}`}>
                  {Math.round(report.audio_analysis.scam_score * 100)}%
                </p>
                <p className="text-xs text-gray-400 mt-1">{report.audio_analysis.verdict.replace("_", " ")}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1">Mistral Large (second opinion)</p>
                <p className={`text-2xl font-bold ${report.text_analysis.scam_score >= 0.6 ? "text-red-400" : report.text_analysis.scam_score >= 0.3 ? "text-yellow-400" : "text-green-400"}`}>
                  {Math.round(report.text_analysis.scam_score * 100)}%
                </p>
                <p className="text-xs text-gray-400 mt-1">{report.text_analysis.verdict.replace("_", " ")}</p>
              </div>
            </div>
            {!tied && (
              <p className={`text-xs text-center mt-3 font-medium ${audioWins ? "text-red-400" : "text-blue-400"}`}>
                Delta: {audioWins ? `+${delta}pp` : `${delta}pp`} — {audioWins ? "audio detected more risk than second opinion" : "second opinion detected more risk than audio"}
              </p>
            )}
            <p className="text-xs text-gray-500 text-center mt-2 italic">
              {audioWins
                ? "Audio-native analysis caught paralinguistic cues the transcript alone missed."
                : tied
                ? "Both models reached the same conclusion."
                : "Combined score weighs both models: 60% audio + 40% text."}
            </p>
          </div>
        );
      })()}

      {/* Trust Panel */}
      <div className="bg-gray-900/60 border border-gray-700/50 rounded-lg px-4 py-3 space-y-1.5">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Analysis Details</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-1 text-xs text-gray-400">
          <div>
            <span className="text-gray-600">Model</span>{" "}
            <span className="text-gray-300 font-mono">
              {report.mode === "audio"
                ? "voxtral-mini-latest"
                : report.mode === "text"
                ? "mistral-large-latest"
                : "voxtral-mini-latest + mistral-large-latest"}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Report ID</span>{" "}
            <span className="text-gray-300 font-mono truncate" title={report.id}>
              {report.id.slice(0, 20)}…
            </span>
          </div>
          {report.analyzed_at && (
            <div>
              <span className="text-gray-600">Analyzed</span>{" "}
              <span className="text-gray-300">{report.analyzed_at.replace("T", " ").replace("Z", " UTC")}</span>
            </div>
          )}
        </div>
      </div>

      {/* Copy / Export buttons */}
      <div className="flex justify-center gap-2 pt-2">
        <button
          onClick={handleCopy}
          className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
        >
          {copied ? "Copied!" : "Copy Results"}
        </button>
        <button
          onClick={handleExportJSON}
          className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
        >
          Export JSON
        </button>
      </div>
    </div>
  );
}
