"""WAV recording listing, serving, and deletion."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import settings

router = APIRouter()


@router.get("/recordings")
async def list_recordings():
    rec_dir = settings.recordings_path
    files = sorted(rec_dir.glob("*.wav"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [f.name for f in files]


@router.get("/recordings/{filename}")
async def get_recording(filename: str):
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Ungültiger Dateiname")

    filepath = settings.recordings_path / filename
    if not filepath.is_file():
        raise HTTPException(404, "Aufnahme nicht gefunden")

    return FileResponse(
        path=str(filepath),
        media_type="audio/wav",
        filename=filename,
    )


@router.delete("/recordings/{filename}")
async def delete_recording(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Ungültiger Dateiname")

    filepath = settings.recordings_path / filename
    if not filepath.is_file():
        raise HTTPException(404, "Aufnahme nicht gefunden")

    filepath.unlink()
    return {"ok": True}
