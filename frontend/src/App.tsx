import { useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import InputPanel from "./components/InputPanel/InputPanel";
import AnalysisPanel from "./components/AnalysisPanel/AnalysisPanel";
import StreamingIndicator from "./components/StreamingIndicator";
import StreamLog from "./components/StreamLog";
import { useAnalyze } from "./hooks/useAnalyze";
import { useStream } from "./hooks/useStream";

type Tab = "upload" | "record" | "paste";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("record");
  const [showLog, setShowLog] = useState(false);
  const { isAnalyzing, report, error, submitAudio, submitTranscript } = useAnalyze();
  const { isRecording, partialResults, finalResult, error: streamError, audioLevel, startRecording, stopRecording } = useStream();

  // Compute deterministic values from partial results
  const lastResult = partialResults[partialResults.length - 1];
  const cumulativeScore = lastResult?.cumulative_score;

  // Peak score across all chunks
  const peakScore = partialResults.length > 0
    ? Math.max(...partialResults.map(r => r.scam_score ?? 0))
    : 0;

  // Effective score: 60% peak + 40% cumulative average (peak-weighted)
  const effectiveScore = cumulativeScore !== undefined
    ? peakScore * 0.6 + cumulativeScore * 0.4
    : undefined;

  // Deterministic verdict from effective score
  const cumulativeVerdict = effectiveScore !== undefined
    ? effectiveScore < 0.3 ? "SAFE"
      : effectiveScore < 0.6 ? "SUSPICIOUS"
      : effectiveScore < 0.85 ? "LIKELY_SCAM"
      : "SCAM"
    : undefined;

  // Recommendation from the highest-scoring chunk
  const highestChunk = partialResults.length > 0
    ? partialResults.reduce((max, r) => (r.scam_score ?? 0) > (max.scam_score ?? 0) ? r : max, partialResults[0])
    : undefined;
  const bestRecommendation = highestChunk?.recommendation || lastResult?.recommendation;

  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-white">
      <Header />

      {/* How It Works */}
      <section className="max-w-4xl mx-auto w-full px-4 pt-8 pb-2">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-3xl mb-2">{"\uD83C\uDFA4"}</div>
            <h3 className="text-white font-semibold text-sm">Record or Upload</h3>
            <p className="text-gray-400 text-xs mt-1">Speak live, upload a WAV, or paste a transcript</p>
          </div>
          <div className="bg-gray-900 border border-blue-500/30 rounded-lg p-4">
            <div className="text-3xl mb-2">{"\uD83E\uDDE0"}</div>
            <h3 className="text-white font-semibold text-sm">Voxtral Analyzes Audio Directly</h3>
            <p className="text-gray-400 text-xs mt-1">No transcription step — Voxtral reasons about audio natively</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-3xl mb-2">{"\uD83D\uDEE1\uFE0F"}</div>
            <h3 className="text-white font-semibold text-sm">Real-time Verdict</h3>
            <p className="text-gray-400 text-xs mt-1">Get a scam score, signals, and recommendation instantly</p>
          </div>
        </div>
      </section>

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8 space-y-8">
        <InputPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onFileSelect={submitAudio}
          onTranscriptSubmit={submitTranscript}
          disabled={isAnalyzing || isRecording}
          isRecording={isRecording}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          cumulativeScore={effectiveScore}
          verdict={cumulativeVerdict}
          recommendation={bestRecommendation}
          audioLevel={audioLevel}
          hasResults={partialResults.length > 0}
        />

        {error && (
          <div role="alert" className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {streamError && (
          <div role="alert" className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400 text-sm">
            {streamError}
          </div>
        )}

        <StreamLog
          results={partialResults}
          isRecording={isRecording}
          visible={showLog}
          onToggle={() => setShowLog((v) => !v)}
        />

        {/* Final summary card after recording stops */}
        {!isRecording && finalResult && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4">
            <h3 className="text-lg font-bold text-white text-center">Analysis Complete</h3>
            <div className="flex flex-col items-center space-y-3">
              <span className={`text-3xl font-bold ${
                (finalResult.combined_score ?? 0) < 0.3 ? "text-green-400" :
                (finalResult.combined_score ?? 0) < 0.6 ? "text-yellow-400" :
                (finalResult.combined_score ?? 0) < 0.85 ? "text-orange-400" :
                "text-red-400"
              }`}>
                {Math.round((finalResult.combined_score ?? 0) * 100)}%
              </span>
              <span className={`text-sm font-bold px-3 py-1 rounded ${
                finalResult.verdict === "SAFE" ? "bg-green-900 text-green-300" :
                finalResult.verdict === "SUSPICIOUS" ? "bg-yellow-900 text-yellow-300" :
                finalResult.verdict === "LIKELY_SCAM" ? "bg-orange-900 text-orange-300" :
                "bg-red-900 text-red-300"
              }`}>
                {finalResult.verdict?.replace("_", " ")}
              </span>
              <p className="text-gray-400 text-xs">
                {finalResult.total_chunks} chunk{finalResult.total_chunks !== 1 ? "s" : ""} analyzed
                {finalResult.max_score !== undefined && ` | Peak: ${Math.round(finalResult.max_score * 100)}%`}
              </p>
            </div>
            {finalResult.transcript_summary && (
              <div className="bg-gray-700/50 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Transcript Summary</h4>
                <p className="text-gray-200 text-sm">{finalResult.transcript_summary}</p>
              </div>
            )}
            {finalResult.signals && finalResult.signals.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">All Signals</h4>
                <ul className="space-y-1">
                  {finalResult.signals.map((s, i) => (
                    <li key={i} className="text-xs text-gray-400">
                      <span className={`font-semibold ${
                        s.severity === "high" ? "text-red-400" :
                        s.severity === "medium" ? "text-yellow-400" :
                        "text-gray-300"
                      }`}>[{s.category}]</span>{" "}
                      {s.detail}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {finalResult.recommendation && (
              <p className="text-sm text-blue-400 italic text-center">
                {finalResult.recommendation}
              </p>
            )}
          </div>
        )}

        <AnalysisPanel report={report} isLoading={isAnalyzing} />
      </main>
      <Footer />
      <StreamingIndicator isRecording={isRecording} cumulativeScore={partialResults[partialResults.length - 1]?.cumulative_score} />
    </div>
  );
}
