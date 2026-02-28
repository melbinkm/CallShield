import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.stream_processor import StreamProcessor

router = APIRouter()

MAX_CHUNK_SIZE = 512 * 1024  # 512KB
MAX_CHUNKS = 60

@router.websocket("/ws/stream")
async def stream_audio(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"type": "connected"})

    processor = StreamProcessor()
    chunk_count = 0

    try:
        while chunk_count < MAX_CHUNKS:
            try:
                message = await asyncio.wait_for(ws.receive(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_json({
                    "type": "error",
                    "detail": "Chunk timeout: no data received",
                })
                break

            # Check for text message (end signal)
            if "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "end_stream":
                    final = processor.get_final_result()
                    await ws.send_json(final)
                    break

            # Binary audio chunk
            if "bytes" in message:
                audio_chunk = message["bytes"]
                if len(audio_chunk) > MAX_CHUNK_SIZE:
                    await ws.send_json({
                        "type": "error",
                        "detail": "Chunk too large",
                    })
                    continue

                try:
                    partial = await processor.process_chunk(audio_chunk)
                    await ws.send_json(partial)
                    chunk_count += 1
                except Exception:
                    await ws.send_json({
                        "type": "error",
                        "detail": "Failed to process audio chunk",
                    })

    except WebSocketDisconnect:
        pass
    finally:
        await ws.close()
