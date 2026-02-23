"""Global detection settings."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..database import get_db
from ..schemas import SettingsRead, SettingsUpdate

router = APIRouter()


@router.get("/settings", response_model=SettingsRead)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await crud.get_settings(db)


@router.put("/settings", response_model=SettingsRead)
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    return await crud.update_settings(db, data)
