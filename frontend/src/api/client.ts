const API_URL = import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:8001`;
import type { ScamReport } from "../types/scamReport";

export async function analyzeAudio(file: File, signal?: AbortSignal): Promise<ScamReport> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/api/analyze/audio`, {
    method: "POST",
    body: formData,
    signal,
  });
  if (!response.ok) {
    try {
      const err = await response.json();
      throw new Error(err.detail?.detail || err.detail || "Audio analysis failed");
    } catch {
      throw new Error(response.statusText || "Audio analysis failed");
    }
  }
  return response.json();
}

export async function analyzeTranscript(transcript: string, signal?: AbortSignal): Promise<ScamReport> {
  const response = await fetch(`${API_URL}/api/analyze/transcript`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript }),
    signal,
  });
  if (!response.ok) {
    try {
      const err = await response.json();
      throw new Error(err.detail?.detail || err.detail || "Transcript analysis failed");
    } catch {
      throw new Error(response.statusText || "Transcript analysis failed");
    }
  }
  return response.json();
}

export async function checkHealth(): Promise<{ demo_mode: boolean }> {
  const response = await fetch(`${API_URL}/api/health`);
  return response.json();
}

export function createStreamSocket(): WebSocket {
  const wsUrl = API_URL.replace(/^http/, "ws");
  return new WebSocket(`${wsUrl}/ws/stream`);
}
