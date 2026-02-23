"""WebSocket endpoints for live FFT and event streaming."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .monitor_manager import manager

logger = logging.getLogger("bandwacht.web.ws")
router = APIRouter()


@router.websocket("/ws/spectrum/{instance_id}")
async def ws_spectrum(websocket: WebSocket, instance_id: int):
    """Stream live FFT data for an instance."""
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=5)

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
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        manager.unsubscribe_fft(instance_id, on_fft)


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    """Stream live detection events globally."""
    await websocket.accept()
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
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        manager.unsubscribe_events(on_event)
