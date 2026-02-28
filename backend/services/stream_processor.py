import base64
import json
from config import client, AUDIO_MODEL
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

        response = client.chat.complete(
            model=AUDIO_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "audio_url",
                            "audio_url": f"data:audio/wav;base64,{audio_b64}",
                        },
                        {
                            "type": "text",
                            "text": SCAM_AUDIO_PROMPT,
                        },
                    ],
                }
            ],
        )

        raw = response.choices[0].message.content
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
        if self.cumulative_score < 0.3:
            verdict = "SAFE"
        elif self.cumulative_score < 0.6:
            verdict = "SUSPICIOUS"
        elif self.cumulative_score < 0.85:
            verdict = "LIKELY_SCAM"
        else:
            verdict = "SCAM"

        return {
            "type": "final_result",
            "total_chunks": self.chunk_index,
            "combined_score": round(self.cumulative_score, 4),
            "verdict": verdict,
            "signals": self.all_signals,
        }
