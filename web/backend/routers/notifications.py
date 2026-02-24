"""Notification config (read-only from env vars) + test send."""

from fastapi import APIRouter, HTTPException

from ..config import settings

router = APIRouter()


@router.get("/notifications")
async def list_notifications():
    return settings.configured_notifications()


@router.post("/notifications/{backend}/test")
async def test_notification(backend: str):
    configured = {n["backend"] for n in settings.configured_notifications()}
    if backend not in configured:
        raise HTTPException(404, f"Backend '{backend}' ist nicht konfiguriert")

    from ..services.monitor_manager import manager
    success = await manager.test_notification(backend)
    if not success:
        raise HTTPException(500, "Testbenachrichtigung fehlgeschlagen")
    return {"ok": True, "message": "Testbenachrichtigung gesendet"}
