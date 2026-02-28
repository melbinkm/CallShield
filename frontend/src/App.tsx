import { useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import InputPanel from "./components/InputPanel/InputPanel";
import type { ScamReport } from "./types/scamReport";

type Tab = "upload" | "record" | "paste";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("upload");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentReport, setCurrentReport] = useState<ScamReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-white">
      <Header />
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8 space-y-8">
        <InputPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onFileSelect={(file) => {
            console.log("File selected:", file.name);
            // Phase 9 will connect this to the API
          }}
          onTranscriptSubmit={(text) => {
            console.log("Transcript submitted:", text.substring(0, 50));
            // Phase 9 will connect this to the API
          }}
          disabled={isAnalyzing}
        />

        {/* AnalysisPanel will go here */}
        <div className="bg-gray-800 rounded-lg p-6 text-center text-gray-400">
          Analysis Panel placeholder (Phase 8)
        </div>
      </main>
      <Footer />
    </div>
  );
}
