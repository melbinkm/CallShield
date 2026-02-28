import base64
import asyncio
import functools
import json
import urllib.request
from config import MISTRAL_API_KEY, AUDIO_MODEL
from prompts.templates import SCAM_AUDIO_PROMPT

async def analyze_audio(audio_bytes: bytes) -> str:
    """Send audio to Voxtral chat completions and return raw response text."""
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

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

    try:
        body = json.loads(resp.read().decode())
        return body["choices"][0]["message"]["content"]
    finally:
        resp.close()
