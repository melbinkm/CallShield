import base64
import asyncio
import functools
from config import client, AUDIO_MODEL
from prompts.templates import SCAM_AUDIO_PROMPT

async def analyze_audio(audio_bytes: bytes) -> str:
    """Send audio to Voxtral chat completions and return raw response text."""
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        functools.partial(
            client.chat.complete,
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
        ),
    )
    return response.choices[0].message.content
