"""Notification config CRUD + test send."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..database import get_db
from ..schemas import NotificationCreate, NotificationRead, NotificationUpdate

router = APIRouter()


def _serialize_config(cfg) -> dict:
    """Deserialize config_json from DB string to dict for response."""
    data = {
        "id": cfg.id,
        "backend": cfg.backend,
        "enabled": cfg.enabled,
        "config_json": json.loads(cfg.config_json) if isinstance(cfg.config_json, str) else cfg.config_json,
        "created_at": cfg.created_at,
        "updated_at": cfg.updated_at,
    }
    return data


@router.get("/notifications")
async def list_notifications(db: AsyncSession = Depends(get_db)):
    configs = await crud.get_notification_configs(db)
    return [_serialize_config(c) for c in configs]


@router.post("/notifications", status_code=201)
async def create_notification(data: NotificationCreate, db: AsyncSession = Depends(get_db)):
    valid_backends = {"console", "gotify", "telegram", "ntfy", "webhook"}
    if data.backend not in valid_backends:
        raise HTTPException(400, f"Backend muss eines von {valid_backends} sein")
    cfg = await crud.create_notification_config(db, data)
    return _serialize_config(cfg)


@router.put("/notifications/{config_id}")
async def update_notification(config_id: int, data: NotificationUpdate, db: AsyncSession = Depends(get_db)):
    cfg = await crud.update_notification_config(db, config_id, data)
    if not cfg:
        raise HTTPException(404, "Benachrichtigungskonfiguration nicht gefunden")
    return _serialize_config(cfg)


@router.delete("/notifications/{config_id}")
async def delete_notification(config_id: int, db: AsyncSession = Depends(get_db)):
    if not await crud.delete_notification_config(db, config_id):
        raise HTTPException(404, "Benachrichtigungskonfiguration nicht gefunden")
    return {"ok": True}


@router.post("/notifications/{config_id}/test")
async def test_notification(config_id: int, db: AsyncSession = Depends(get_db)):
    cfg = await crud.get_notification_config(db, config_id)
    if not cfg:
        raise HTTPException(404, "Benachrichtigungskonfiguration nicht gefunden")

    from ..services.monitor_manager import manager
    success = await manager.test_notification(cfg)
    if not success:
        raise HTTPException(500, "Testbenachrichtigung fehlgeschlagen")
    return {"ok": True, "message": "Testbenachrichtigung gesendet"}
