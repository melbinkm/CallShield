export type Severity = "low" | "medium" | "high";
export type Verdict = "SAFE" | "SUSPICIOUS" | "LIKELY_SCAM" | "SCAM";

export interface Signal {
  category: string;
  detail: string;
  severity: Severity;
}

export interface AnalysisResult {
  scam_score: number;
  confidence: number;
  verdict: Verdict;
  signals: Signal[];
  transcript_summary?: string;
  recommendation: string;
  review_required?: boolean;
  review_reason?: string;
}

export interface ScamReport {
  id: string;
  mode: "audio" | "text" | "stream";
  audio_analysis: AnalysisResult | null;
  text_analysis: AnalysisResult | null;
  combined_score: number;
  processing_time_ms: number;
  review_required?: boolean;
  review_reason?: string;
  analyzed_at?: string;
}

export interface ErrorResponse {
  error: string;
  detail: string;
}
