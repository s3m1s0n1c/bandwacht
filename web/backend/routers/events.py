"""Detection event history, filters, stats, CSV export."""

import csv
import io
import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..database import get_db
from ..schemas import EventRead, EventStats, PaginatedResponse

router = APIRouter()


@router.get("/events")
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    instance_id: int | None = None,
    freq_min: float | None = None,
    freq_max: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    label: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    events, total = await crud.get_events(
        db,
        page=page,
        page_size=page_size,
        instance_id=instance_id,
        freq_min=freq_min,
        freq_max=freq_max,
        date_from=date_from,
        date_to=date_to,
        label=label,
    )
    return {
        "items": [EventRead.model_validate(e) for e in events],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)),
    }


@router.get("/events/stats", response_model=EventStats)
async def event_stats(db: AsyncSession = Depends(get_db)):
    return await crud.get_event_stats(db)


@router.get("/events/export")
async def export_events_csv(
    instance_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    events, _ = await crud.get_events(
        db,
        page=1,
        page_size=100_000,
        instance_id=instance_id,
        date_from=date_from,
        date_to=date_to,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "freq_mhz", "peak_db", "bandwidth_hz", "duration_s", "label", "recording"])

    for ev in events:
        writer.writerow([
            ev.timestamp.isoformat() if ev.timestamp else "",
            f"{ev.freq_hz / 1e6:.4f}",
            f"{ev.peak_db:.1f}",
            f"{ev.bandwidth_hz:.0f}",
            f"{ev.duration_s:.1f}",
            ev.target_label,
            ev.recording_file or "",
        ])

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bandwacht_events.csv"},
    )
