import { useState, useRef, useCallback, useEffect } from "react";
import { createStreamSocket } from "../api/client";
import type { Signal } from "../types/scamReport";

interface PartialResult {
  type: string;
  chunk_index?: number;
  scam_score?: number;
  cumulative_score?: number;
  confidence?: number;
  verdict?: string;
  signals?: Signal[];
  recommendation?: string;
  transcript_summary?: string;
  timestamp_ms?: number;
  score_delta?: number;
  new_signals?: Signal[];
  [key: string]: unknown;
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
  const [isProcessingFinal, setIsProcessingFinal] = useState(false);
  const [partialResults, setPartialResults] = useState<PartialResult[]>([]);
  const [finalResult, setFinalResult] = useState<{
    type: string;
    total_chunks?: number;
    combined_score?: number;
    max_score?: number;
    verdict?: string;
    signals?: Signal[];
    recommendation?: string;
    transcript_summary?: string;
    review_required?: boolean;
    review_reason?: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const streamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const intentionalCloseRef = useRef(false);

  useEffect(() => {
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
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
    intentionalCloseRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          noiseSuppression: false,   // preserve call-center noise Voxtral can detect
          echoCancellation: false,   // preserve TTS/robocall audio artifacts
          autoGainControl: false,    // preserve natural volume dynamics
        },
      });
      streamRef.current = stream;
      const ws = createStreamSocket();
      wsRef.current = ws;

      ws.onopen = async () => {
        setIsRecording(true);

        const audioCtx = new AudioContext({ sampleRate: 16000 });
        const source = audioCtx.createMediaStreamSource(stream);

        // Audio level visualization via AnalyserNode
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        source.connect(analyser);
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const updateLevel = () => {
          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          setAudioLevel(sum / dataArray.length / 255);
          animFrameRef.current = requestAnimationFrame(updateLevel);
        };
        animFrameRef.current = requestAnimationFrame(updateLevel);

        // AudioWorkletNode replaces the deprecated ScriptProcessorNode
        await audioCtx.audioWorklet.addModule("/pcm-processor.js");
        const worklet = new AudioWorkletNode(audioCtx, "pcm-processor");

        worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
          const wavBytes = encodeWAV(e.data, 16000);
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(wavBytes);
          }
        };

        // Silent sink — gain=0 prevents echo; destination connection keeps worklet active
        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 0;
        gainNode.connect(audioCtx.destination);

        source.connect(worklet);
        worklet.connect(gainNode);
        audioCtxRef.current = audioCtx;
        workletRef.current = worklet;
      };

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (!data.type) return;

          if (data.type === "partial_result") {
            setPartialResults((prev) => [...prev, data]);
          } else if (data.type === "final_result") {
            setFinalResult(data);
            setIsProcessingFinal(false);
            ws.close();
          } else if (data.type === "error") {
            setError(data.detail);
          }
        } catch {
          setError("Invalid message from server");
        }
      };

      ws.onerror = () => setError("WebSocket connection failed. Is the backend running?");
      ws.onclose = () => {
        setIsRecording(false);
        setIsProcessingFinal(false);
        if (!intentionalCloseRef.current) {
          setError("Connection lost. Recording stopped.");
        }
      };
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not access microphone");
    }
  }, []);

  const stopRecording = useCallback(() => {
    intentionalCloseRef.current = true;
    setIsRecording(false);
    setIsProcessingFinal(true);

    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    analyserRef.current = null;
    setAudioLevel(0);

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    const ws = wsRef.current;
    wsRef.current = null;
    const worklet = workletRef.current;
    workletRef.current = null;
    const audioCtx = audioCtxRef.current;
    audioCtxRef.current = null;

    const finish = () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "end_stream" }));
        // Give the backend up to 30s to respond with final_result;
        // ws.close() is called in onmessage once final_result arrives.
        setTimeout(() => ws.close(), 30000);
      }
      audioCtx?.close();
    };

    if (worklet) {
      // Flush any samples accumulated in the worklet that haven't reached 5s yet
      const fallback = setTimeout(finish, 300);
      worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
        clearTimeout(fallback);
        if (e.data.length > 0 && ws && ws.readyState === WebSocket.OPEN) {
          ws.send(encodeWAV(e.data, 16000));
        }
        finish();
      };
      worklet.port.postMessage({ type: "flush" });
    } else {
      finish();
    }
  }, []);

  const clearStream = useCallback(() => {
    setPartialResults([]);
    setFinalResult(null);
    setIsProcessingFinal(false);
    setError(null);
  }, []);

  return { isRecording, isProcessingFinal, partialResults, finalResult, error, audioLevel, startRecording, stopRecording, clearStream };
}
