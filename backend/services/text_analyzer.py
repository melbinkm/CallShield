import asyncio
from config import client, TEXT_MODEL
from prompts.templates import SCAM_TEXT_PROMPT

async def analyze_transcript(transcript: str) -> str:
    """Send transcript to Mistral chat completions and return raw response text."""
    response = await asyncio.to_thread(
        client.chat.complete,
        model=TEXT_MODEL,
        messages=[
            {
                "role": "user",
                "content": SCAM_TEXT_PROMPT + "\n\nTranscript:\n" + transcript,
            }
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content
