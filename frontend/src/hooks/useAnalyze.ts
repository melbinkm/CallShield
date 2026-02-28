import { useState, useRef } from "react";
import { analyzeAudio, analyzeTranscript } from "../api/client";
import type { ScamReport } from "../types/scamReport";

export function useAnalyze() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState<ScamReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function submitAudio(file: File) {
    setIsAnalyzing(true);
    setError(null);
    setReport(null);

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await analyzeAudio(file, controller.signal);
      setReport(result);
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message || "Audio analysis failed");
      }
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function submitTranscript(text: string) {
    setIsAnalyzing(true);
    setError(null);
    setReport(null);

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await analyzeTranscript(text, controller.signal);
      setReport(result);
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message || "Transcript analysis failed");
      }
    } finally {
      setIsAnalyzing(false);
    }
  }

  function clearResults() {
    setReport(null);
    setError(null);
  }

  return { isAnalyzing, report, error, submitAudio, submitTranscript, clearResults };
}
