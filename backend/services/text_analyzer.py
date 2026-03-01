import asyncio
import functools
from config import client, TEXT_MODEL
from prompts.templates import SCAM_TEXT_PROMPT

async def analyze_transcript(transcript: str) -> str:
    """Send transcript to Mistral chat completions and return raw response text."""
    loop = asyncio.get_event_loop()
    response = await asyncio.wait_for(
        loop.run_in_executor(
            None,
            functools.partial(
                client.chat.complete,
                model=TEXT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": SCAM_TEXT_PROMPT + "\n\nTranscript:\n" + transcript,
                    }
                ],
                response_format={"type": "json_object"},
            ),
        ),
        timeout=120,
    )
    return response.choices[0].message.content
