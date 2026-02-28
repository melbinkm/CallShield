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
    try:
        await ws.send_json({"type": "connected"})
    except Exception:
        pass

    processor = StreamProcessor()
    chunk_count = 0

    try:
        while chunk_count < MAX_CHUNKS:
            try:
                message = await asyncio.wait_for(ws.receive(), timeout=30.0)
            except asyncio.TimeoutError:
                try:
                    await ws.send_json({
                        "type": "error",
                        "detail": "Chunk timeout: no data received",
                    })
                except Exception:
                    pass
                break

            # Check for text message (end signal)
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError as e:
                    import logging
                    logging.getLogger(__name__).warning("Invalid JSON received: %s", e)
                    continue
                if data.get("type") == "end_stream":
                    final = processor.get_final_result()
                    try:
                        await ws.send_json(final)
                    except Exception:
                        pass
                    break

            # Binary audio chunk
            if "bytes" in message:
                audio_chunk = message["bytes"]
                if len(audio_chunk) > MAX_CHUNK_SIZE:
                    try:
                        await ws.send_json({
                            "type": "error",
                            "detail": "Chunk too large",
                        })
                    except Exception:
                        pass
                    continue

                try:
                    partial = await processor.process_chunk(audio_chunk)
                    try:
                        await ws.send_json(partial)
                    except Exception:
                        pass
                    chunk_count += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).exception("Chunk processing failed: %s", e)
                    try:
                        await ws.send_json({
                            "type": "error",
                            "detail": f"Failed to process audio chunk: {e}",
                        })
                    except Exception:
                        pass

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
