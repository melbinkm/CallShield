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
  const [activeTab, setActiveTab] = useState<Tab>("upload");
  const [showLog, setShowLog] = useState(false);
  const { isAnalyzing, report, error, submitAudio, submitTranscript } = useAnalyze();
  const { isRecording, partialResults, error: streamError, startRecording, stopRecording } = useStream();

  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-white">
      <Header />
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
          cumulativeScore={partialResults[partialResults.length - 1]?.cumulative_score}
          verdict={partialResults[partialResults.length - 1]?.verdict}
          recommendation={partialResults[partialResults.length - 1]?.recommendation}
        />

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {streamError && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400 text-sm">
            {streamError}
          </div>
        )}

        <StreamLog
          results={partialResults}
          isRecording={isRecording}
          visible={showLog}
          onToggle={() => setShowLog((v) => !v)}
        />

        <AnalysisPanel report={report} isLoading={isAnalyzing} />
      </main>
      <Footer />
      <StreamingIndicator isRecording={isRecording} cumulativeScore={partialResults[partialResults.length - 1]?.cumulative_score} />
    </div>
  );
}
