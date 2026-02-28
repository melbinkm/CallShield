import { useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
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
        {/* InputPanel will go here */}
        <div className="bg-gray-800 rounded-lg p-6 text-center text-gray-400">
          Input Panel placeholder (Phase 7)
        </div>

        {/* AnalysisPanel will go here */}
        <div className="bg-gray-800 rounded-lg p-6 text-center text-gray-400">
          Analysis Panel placeholder (Phase 8)
        </div>
      </main>
      <Footer />
    </div>
  );
}
