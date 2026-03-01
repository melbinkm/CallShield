import base64
import json
import asyncio
import functools
import struct
import time
import urllib.request
from config import MISTRAL_API_KEY, AUDIO_MODEL
from prompts.templates import SCAM_AUDIO_PROMPT
from services.response_formatter import extract_json


def is_silent(audio_bytes: bytes, threshold=500) -> bool:
    """Check if WAV audio chunk is silence by looking at PCM amplitude."""
    # Skip 44-byte WAV header
    pcm_data = audio_bytes[44:]
    if len(pcm_data) < 2:
        return True
    try:
        num_samples = len(pcm_data) // 2
        if num_samples == 0:
            return True
        samples = struct.unpack(f"<{num_samples}h", pcm_data[:num_samples * 2])
        rms = (sum(s * s for s in samples) / num_samples) ** 0.5
        return rms < threshold
    except (struct.error, ValueError):
        # Corrupted header or invalid data - treat as silent
        return True

class StreamProcessor:
    def __init__(self):
        self.chunk_index = 0
        self.cumulative_score = 0.0
        self.max_score = 0.0
        self.all_signals = []
        self.last_recommendation = ""
        self.last_transcript_summary = ""
        self.start_time = time.time()
        self.seen_signal_categories: set = set()
        self.prev_cumulative = 0.0

    async def process_chunk(self, audio_chunk: bytes) -> dict:
        """Process a single audio chunk and return partial result."""
        # Always increment chunk_index to avoid duplicates
        self.chunk_index += 1
        
        timestamp_ms = int((time.time() - self.start_time) * 1000)

        if is_silent(audio_chunk):
            return {
                "type": "partial_result",
                "chunk_index": self.chunk_index,
                "timestamp_ms": timestamp_ms,
                "score_delta": 0.0,
                "new_signals": [],
                "scam_score": 0.0,
                "cumulative_score": round(self.cumulative_score, 4),
                "verdict": "SAFE",
                "signals": [{"category": "SILENCE", "detail": "No speech detected in this chunk",
 "severity": "low"}],
            }
        
        audio_b64 = base64.b64encode(audio_chunk).decode("utf-8")

        payload = json.dumps({
            "model": AUDIO_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": "wav",
                        },
                    },
                    {
                        "type": "text",
                        "text": SCAM_AUDIO_PROMPT,
                    },
                ],
            }],
            "temperature": 0.3,
            "top_p": 0.9,
            "response_format": {"type": "json_object"},
        }).encode()

        req = urllib.request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            functools.partial(urllib.request.urlopen, req, timeout=120),
        )

        try:
            body = json.loads(resp.read().decode())
            choices = body.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                raise ValueError(f"Unexpected API response structure: no choices")
            raw = choices[0].get("message", {}).get("content", "")
            if not raw:
                raise ValueError("Empty content in API response")
            data = extract_json(raw)
        finally:
            resp.close()

        chunk_score = float(data.get("scam_score", 0.0))
        signals = data.get("signals", [])
        self.last_recommendation = data.get("recommendation", "")
        self.last_transcript_summary = data.get("transcript_summary", "")

        # Compute score_delta before updating cumulative
        score_delta = chunk_score - self.prev_cumulative

        # Compute new_signals (categories not seen before)
        new_signals = [s for s in signals if s.get("category") not in self.seen_signal_categories]
        self.seen_signal_categories.update(s.get("category") for s in signals)

        # Update peak score
        if chunk_score > self.max_score:
            self.max_score = chunk_score

        # Exponential weighting: recent/severe chunks weighted more
        self.cumulative_score = 0.7 * chunk_score + 0.3 * self.cumulative_score
        self.prev_cumulative = self.cumulative_score
        self.all_signals.extend(signals)

        return {
            "type": "partial_result",
            "chunk_index": self.chunk_index,
            "timestamp_ms": timestamp_ms,
            "score_delta": round(score_delta, 4),
            "new_signals": new_signals,
            "scam_score": round(chunk_score, 4),
            "cumulative_score": round(self.cumulative_score, 4),
            "max_score": round(self.max_score, 4),
            "confidence": round(float(data.get("confidence", 0.0)), 4),
            "verdict": data.get("verdict", "SAFE"),
            "signals": signals,
            "recommendation": data.get("recommendation", ""),
            "transcript_summary": data.get("transcript_summary", ""),
        }

    def get_final_result(self) -> dict:
        """Return the final aggregated result.

        Uses the same peak-weighted formula as the frontend live score:
        combined = 0.6 * max_score + 0.4 * cumulative_score
        This ensures the final verdict is consistent with what the user saw
        during recording.
        """
        from services.response_formatter import score_to_verdict
        combined_score = round(0.6 * self.max_score + 0.4 * self.cumulative_score, 4)
        verdict = score_to_verdict(combined_score)

        in_band = 0.35 <= combined_score <= 0.65
        low_conf = self.cumulative_score < 0.55 and self.max_score < 0.55  # rough proxy
        review_required = in_band or low_conf
        review_reason = (
            "Score in ambiguous range — human judgement recommended" if in_band else
            "Low model confidence" if low_conf else None
        )

        return {
            "type": "final_result",
            "total_chunks": self.chunk_index,
            "combined_score": combined_score,
            "max_score": round(self.max_score, 4),
            "verdict": verdict,
            "signals": self.all_signals,
            "recommendation": self.last_recommendation,
            "transcript_summary": self.last_transcript_summary,
            "review_required": review_required,
            "review_reason": review_reason,
            "text_score": None,
        }
