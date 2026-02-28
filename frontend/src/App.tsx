import { useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import InputPanel from "./components/InputPanel/InputPanel";
import AnalysisPanel from "./components/AnalysisPanel/AnalysisPanel";
import { useAnalyze } from "./hooks/useAnalyze";

type Tab = "upload" | "record" | "paste";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("upload");
  const { isAnalyzing, report, error, submitAudio, submitTranscript } = useAnalyze();

  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-white">
      <Header />
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8 space-y-8">
        <InputPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onFileSelect={submitAudio}
          onTranscriptSubmit={submitTranscript}
          disabled={isAnalyzing}
        />

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        <AnalysisPanel report={report} isLoading={isAnalyzing} />
      </main>
      <Footer />
    </div>
  );
}
