import { useState, useRef, useCallback, useEffect } from "react";
import { createStreamSocket } from "../api/client";
import type { Signal } from "../types/scamReport";

interface PartialResult {
  type: string;
  chunk_index?: number;
  scam_score?: number;
  cumulative_score?: number;
  verdict?: string;
  signals?: Signal[];
  recommendation?: string;
  transcript_summary?: string;
}

// WAV encoder helpers
function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

function encodeWAV(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  // RIFF header
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, "WAVE");

  // fmt chunk
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);          // PCM
  view.setUint16(22, 1, true);          // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);         // 16-bit

  // data chunk
  writeString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  // PCM samples (float32 → int16)
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  return buffer;
}

export function useStream() {
  const [isRecording, setIsRecording] = useState(false);
  const [partialResults, setPartialResults] = useState<PartialResult[]>([]);
  const [finalResult, setFinalResult] = useState<{
    type: string;
    total_chunks?: number;
    combined_score?: number;
    verdict?: string;
    signals?: Signal[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    return () => {
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

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

        const audioCtx = new AudioContext({ sampleRate: 16000 });
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        let pcmBuffer: Float32Array[] = [];
        let sampleCount = 0;
        const CHUNK_SAMPLES = 16000 * 5; // 5 seconds

        processor.onaudioprocess = (e) => {
          const pcm = new Float32Array(e.inputBuffer.getChannelData(0));
          pcmBuffer.push(pcm);
          sampleCount += pcm.length;

          if (sampleCount >= CHUNK_SAMPLES) {
            // Merge buffers
            const merged = new Float32Array(sampleCount);
            let offset = 0;
            for (const buf of pcmBuffer) {
              merged.set(buf, offset);
              offset += buf.length;
            }
            const wavBytes = encodeWAV(merged, 16000);
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(wavBytes);
            }
            pcmBuffer = [];
            sampleCount = 0;
          }
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);
        audioCtxRef.current = audioCtx;
      };

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (!data.type) return;

          if (data.type === "partial_result") {
            setPartialResults((prev) => [...prev, data]);
          } else if (data.type === "final_result") {
            setFinalResult(data);
          } else if (data.type === "error") {
            setError(data.detail);
          }
        } catch (err) {
          setError("Invalid message from server");
        }
      };

      ws.onerror = () => setError("WebSocket connection failed");
      ws.onclose = () => setIsRecording(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not access microphone");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_stream" }));
      wsRef.current.close();
    }
  }, []);

  return { isRecording, partialResults, finalResult, error, startRecording, stopRecording };
}
