import base64
import json
import asyncio
import functools
import urllib.request
from config import MISTRAL_API_KEY, AUDIO_MODEL
from prompts.templates import SCAM_AUDIO_PROMPT
from services.response_formatter import extract_json

class StreamProcessor:
    def __init__(self):
        self.chunk_index = 0
        self.cumulative_score = 0.0
        self.all_signals = []

    async def process_chunk(self, audio_chunk: bytes) -> dict:
        """Process a single audio chunk and return partial result."""
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

        body = json.loads(resp.read().decode())
        raw = body["choices"][0]["message"]["content"]
        data = extract_json(raw)

        chunk_score = float(data.get("scam_score", 0.0))
        signals = data.get("signals", [])

        # Update cumulative score with running average
        self.chunk_index += 1
        self.cumulative_score = (
            (self.cumulative_score * (self.chunk_index - 1) + chunk_score)
            / self.chunk_index
        )
        self.all_signals.extend(signals)

        return {
            "type": "partial_result",
            "chunk_index": self.chunk_index,
            "scam_score": round(chunk_score, 4),
            "cumulative_score": round(self.cumulative_score, 4),
            "verdict": data.get("verdict", "SAFE"),
            "signals": signals,
        }

    def get_final_result(self) -> dict:
        """Return the final aggregated result."""
        from services.response_formatter import score_to_verdict
        verdict = score_to_verdict(self.cumulative_score)

        return {
            "type": "final_result",
            "total_chunks": self.chunk_index,
            "combined_score": round(self.cumulative_score, 4),
            "verdict": verdict,
            "signals": self.all_signals,
        }
