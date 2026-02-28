import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.stream_processor import StreamProcessor

router = APIRouter()

@router.websocket("/ws/stream")
async def stream_audio(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"type": "connected"})

    processor = StreamProcessor()

    try:
        while True:
            message = await ws.receive()

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
                try:
                    partial = await processor.process_chunk(audio_chunk)
                    await ws.send_json(partial)
                except Exception as e:
                    await ws.send_json({
                        "type": "error",
                        "detail": f"Chunk processing failed: {str(e)}",
                    })

    except WebSocketDisconnect:
        pass
    finally:
        await ws.close()
