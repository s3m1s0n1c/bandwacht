"""Watch target CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..database import get_db
from ..schemas import TargetCreate, TargetRead, TargetUpdate

router = APIRouter()


@router.get("/targets", response_model=list[TargetRead])
async def list_targets(
    instance_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_targets(db, instance_id=instance_id)


@router.post("/targets", response_model=TargetRead, status_code=201)
async def create_target(data: TargetCreate, db: AsyncSession = Depends(get_db)):
    if data.instance_id is not None:
        inst = await crud.get_instance(db, data.instance_id)
        if not inst:
            raise HTTPException(404, "SDR-Instanz nicht gefunden")
    return await crud.create_target(db, data)


@router.get("/targets/{target_id}", response_model=TargetRead)
async def get_target(target_id: int, db: AsyncSession = Depends(get_db)):
    target = await crud.get_target(db, target_id)
    if not target:
        raise HTTPException(404, "Ziel nicht gefunden")
    return target


@router.put("/targets/{target_id}", response_model=TargetRead)
async def update_target(target_id: int, data: TargetUpdate, db: AsyncSession = Depends(get_db)):
    target = await crud.update_target(db, target_id, data)
    if not target:
        raise HTTPException(404, "Ziel nicht gefunden")
    return target


@router.delete("/targets/{target_id}")
async def delete_target(target_id: int, db: AsyncSession = Depends(get_db)):
    if not await crud.delete_target(db, target_id):
        raise HTTPException(404, "Ziel nicht gefunden")
    return {"ok": True}
