import { useState, useRef, useCallback } from "react";
import { createStreamSocket } from "../api/client";

interface PartialResult {
  type: string;
  chunk_index?: number;
  scam_score?: number;
  cumulative_score?: number;
  verdict?: string;
  signals?: any[];
}

export function useStream() {
  const [isRecording, setIsRecording] = useState(false);
  const [partialResults, setPartialResults] = useState<PartialResult[]>([]);
  const [finalResult, setFinalResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);

  const startRecording = useCallback(async () => {
    setError(null);
    setPartialResults([]);
    setFinalResult(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ws = createStreamSocket();
      wsRef.current = ws;

      ws.onopen = () => {
        setIsRecording(true);

        const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
        recorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(e.data);
          }
        };

        // Send chunks every 5 seconds
        recorder.start(5000);
      };

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === "partial_result") {
          setPartialResults((prev) => [...prev, data]);
        } else if (data.type === "final_result") {
          setFinalResult(data);
        } else if (data.type === "error") {
          setError(data.detail);
        }
      };

      ws.onerror = () => setError("WebSocket connection failed");
      ws.onclose = () => setIsRecording(false);
    } catch (err: any) {
      setError(err.message || "Could not access microphone");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
      recorderRef.current.stream.getTracks().forEach((t) => t.stop());
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_stream" }));
    }
  }, []);

  return { isRecording, partialResults, finalResult, error, startRecording, stopRecording };
}
