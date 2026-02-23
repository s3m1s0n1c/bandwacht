"""Database CRUD operations."""

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import DetectionEvent, GlobalSetting, NotificationConfig, SdrInstance, WatchTarget
from .schemas import (
    InstanceCreate,
    InstanceUpdate,
    NotificationCreate,
    NotificationUpdate,
    SettingsRead,
    SettingsUpdate,
    TargetCreate,
    TargetUpdate,
)


# --- SDR Instances ---

async def get_instances(db: AsyncSession) -> list[SdrInstance]:
    result = await db.execute(select(SdrInstance).order_by(SdrInstance.id))
    return list(result.scalars().all())


async def get_instance(db: AsyncSession, instance_id: int) -> SdrInstance | None:
    return await db.get(SdrInstance, instance_id)


async def create_instance(db: AsyncSession, data: InstanceCreate) -> SdrInstance:
    inst = SdrInstance(**data.model_dump())
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return inst


async def update_instance(db: AsyncSession, instance_id: int, data: InstanceUpdate) -> SdrInstance | None:
    inst = await db.get(SdrInstance, instance_id)
    if not inst:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(inst, key, val)
    await db.commit()
    await db.refresh(inst)
    return inst


async def delete_instance(db: AsyncSession, instance_id: int) -> bool:
    inst = await db.get(SdrInstance, instance_id)
    if not inst:
        return False
    await db.delete(inst)
    await db.commit()
    return True


async def update_instance_connection(db: AsyncSession, instance_id: int, connected: bool,
                                      center_freq: float | None = None,
                                      bandwidth: float | None = None,
                                      fft_size: int | None = None):
    values: dict = {"is_connected": connected}
    if center_freq is not None:
        values["center_freq"] = center_freq
    if bandwidth is not None:
        values["bandwidth"] = bandwidth
    if fft_size is not None:
        values["fft_size"] = fft_size
    await db.execute(update(SdrInstance).where(SdrInstance.id == instance_id).values(**values))
    await db.commit()


# --- Watch Targets ---

async def get_targets(db: AsyncSession, instance_id: int | None = None) -> list[WatchTarget]:
    q = select(WatchTarget).order_by(WatchTarget.id)
    if instance_id is not None:
        q = q.where(WatchTarget.instance_id == instance_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_target(db: AsyncSession, target_id: int) -> WatchTarget | None:
    return await db.get(WatchTarget, target_id)


async def create_target(db: AsyncSession, data: TargetCreate) -> WatchTarget:
    target = WatchTarget(**data.model_dump())
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


async def update_target(db: AsyncSession, target_id: int, data: TargetUpdate) -> WatchTarget | None:
    target = await db.get(WatchTarget, target_id)
    if not target:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(target, key, val)
    await db.commit()
    await db.refresh(target)
    return target


async def delete_target(db: AsyncSession, target_id: int) -> bool:
    target = await db.get(WatchTarget, target_id)
    if not target:
        return False
    await db.delete(target)
    await db.commit()
    return True


# --- Detection Events ---

async def get_events(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    instance_id: int | None = None,
    freq_min: float | None = None,
    freq_max: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    label: str | None = None,
) -> tuple[list[DetectionEvent], int]:
    q = select(DetectionEvent)

    if instance_id is not None:
        q = q.where(DetectionEvent.instance_id == instance_id)
    if freq_min is not None:
        q = q.where(DetectionEvent.freq_hz >= freq_min)
    if freq_max is not None:
        q = q.where(DetectionEvent.freq_hz <= freq_max)
    if date_from is not None:
        q = q.where(DetectionEvent.timestamp >= date_from)
    if date_to is not None:
        q = q.where(DetectionEvent.timestamp <= date_to)
    if label:
        q = q.where(DetectionEvent.target_label.ilike(f"%{label}%"))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(DetectionEvent.timestamp.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)

    return list(result.scalars().all()), total


async def create_event(db: AsyncSession, **kwargs) -> DetectionEvent:
    event = DetectionEvent(**kwargs)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_event_stats(db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    total = (await db.execute(select(func.count(DetectionEvent.id)))).scalar() or 0
    today = (await db.execute(
        select(func.count(DetectionEvent.id)).where(DetectionEvent.timestamp >= today_start)
    )).scalar() or 0
    week = (await db.execute(
        select(func.count(DetectionEvent.id)).where(DetectionEvent.timestamp >= week_start)
    )).scalar() or 0

    # Top frequencies
    top_q = (
        select(
            DetectionEvent.freq_hz,
            DetectionEvent.target_label,
            func.count(DetectionEvent.id).label("count"),
        )
        .group_by(DetectionEvent.freq_hz, DetectionEvent.target_label)
        .order_by(func.count(DetectionEvent.id).desc())
        .limit(10)
    )
    top_rows = (await db.execute(top_q)).all()
    top_frequencies = [
        {"freq_hz": r.freq_hz, "label": r.target_label, "count": r.count}
        for r in top_rows
    ]

    return {
        "total_events": total,
        "events_today": today,
        "events_this_week": week,
        "top_frequencies": top_frequencies,
        "hourly_distribution": [],
    }


# --- Notification Configs ---

async def get_notification_configs(db: AsyncSession) -> list[NotificationConfig]:
    result = await db.execute(select(NotificationConfig).order_by(NotificationConfig.id))
    return list(result.scalars().all())


async def get_notification_config(db: AsyncSession, config_id: int) -> NotificationConfig | None:
    return await db.get(NotificationConfig, config_id)


async def create_notification_config(db: AsyncSession, data: NotificationCreate) -> NotificationConfig:
    cfg = NotificationConfig(
        backend=data.backend,
        enabled=data.enabled,
        config_json=json.dumps(data.config_json),
    )
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return cfg


async def update_notification_config(db: AsyncSession, config_id: int, data: NotificationUpdate) -> NotificationConfig | None:
    cfg = await db.get(NotificationConfig, config_id)
    if not cfg:
        return None
    if data.enabled is not None:
        cfg.enabled = data.enabled
    if data.config_json is not None:
        cfg.config_json = json.dumps(data.config_json)
    await db.commit()
    await db.refresh(cfg)
    return cfg


async def delete_notification_config(db: AsyncSession, config_id: int) -> bool:
    cfg = await db.get(NotificationConfig, config_id)
    if not cfg:
        return False
    await db.delete(cfg)
    await db.commit()
    return True


# --- Global Settings ---

DEFAULT_SETTINGS = {
    "threshold_db": "-55.0",
    "hysteresis_db": "5.0",
    "hold_time_s": "2.0",
    "cooldown_s": "10.0",
    "record_enabled": "false",
    "scan_full_band": "false",
}


async def get_settings(db: AsyncSession) -> SettingsRead:
    result = await db.execute(select(GlobalSetting))
    rows = {r.key: r.value for r in result.scalars().all()}
    merged = {**DEFAULT_SETTINGS, **rows}
    return SettingsRead(
        threshold_db=float(merged["threshold_db"]),
        hysteresis_db=float(merged["hysteresis_db"]),
        hold_time_s=float(merged["hold_time_s"]),
        cooldown_s=float(merged["cooldown_s"]),
        record_enabled=merged["record_enabled"].lower() == "true",
        scan_full_band=merged["scan_full_band"].lower() == "true",
    )


async def update_settings(db: AsyncSession, data: SettingsUpdate) -> SettingsRead:
    for key, val in data.model_dump(exclude_unset=True).items():
        str_val = str(val).lower() if isinstance(val, bool) else str(val)
        existing = await db.get(GlobalSetting, key)
        if existing:
            existing.value = str_val
        else:
            db.add(GlobalSetting(key=key, value=str_val))
    await db.commit()
    return await get_settings(db)
