const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export async function analyzeAudio(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/api/analyze/audio`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail?.detail || err.detail || "Audio analysis failed");
  }
  return response.json();
}

export async function analyzeTranscript(transcript: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/analyze/transcript`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail?.detail || err.detail || "Transcript analysis failed");
  }
  return response.json();
}

export function createStreamSocket(): WebSocket {
  const wsUrl = API_URL.replace(/^http/, "ws");
  return new WebSocket(`${wsUrl}/ws/stream`);
}
