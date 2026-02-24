"""WebSocket endpoints for live FFT and event streaming."""

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..auth import verify_ws_token
from .monitor_manager import manager

logger = logging.getLogger("bandwacht.web.ws")
router = APIRouter()


@router.websocket("/ws/spectrum/{instance_id}")
async def ws_spectrum(websocket: WebSocket, instance_id: int, token: str = Query(default="")):
    """Stream live FFT data for an instance."""
    user = verify_ws_token(token)
    if not user:
        await websocket.close(code=1008, reason="Nicht autorisiert")
        return

    await websocket.accept()
    logger.info(f"WS spectrum client connected for instance {instance_id}")
    queue: asyncio.Queue = asyncio.Queue(maxsize=5)
    msg_count = 0

    async def on_fft(fft_data: list):
        try:
            queue.put_nowait(fft_data)
        except asyncio.QueueFull:
            # Drop oldest, keep newest
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(fft_data)
            except asyncio.QueueFull:
                pass

    manager.subscribe_fft(instance_id, on_fft)
    try:
        while True:
            fft_data = await queue.get()
            await websocket.send_text(json.dumps(fft_data))
            msg_count += 1
            if msg_count == 1:
                logger.info(f"WS spectrum: first FFT frame sent to client (instance {instance_id}, {len(fft_data)} bins)")
    except (WebSocketDisconnect, Exception) as e:
        logger.info(f"WS spectrum client disconnected for instance {instance_id} ({type(e).__name__}, sent {msg_count} frames)")
    finally:
        manager.unsubscribe_fft(instance_id, on_fft)


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: str = Query(default="")):
    """Stream live detection events globally."""
    user = verify_ws_token(token)
    if not user:
        await websocket.close(code=1008, reason="Nicht autorisiert")
        return

    await websocket.accept()
    logger.info("WS events client connected")
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    async def on_event(event_data: dict):
        try:
            queue.put_nowait(event_data)
        except asyncio.QueueFull:
            pass

    manager.subscribe_events(on_event)
    try:
        while True:
            event_data = await queue.get()
            await websocket.send_text(json.dumps(event_data))
    except (WebSocketDisconnect, Exception) as e:
        logger.info(f"WS events client disconnected ({type(e).__name__})")
    finally:
        manager.unsubscribe_events(on_event)
