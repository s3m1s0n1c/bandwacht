"""SDR instance CRUD + start/stop monitoring."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..database import get_db
from ..schemas import InstanceCreate, InstanceRead, InstanceUpdate

router = APIRouter()


@router.get("/instances", response_model=list[InstanceRead])
async def list_instances(db: AsyncSession = Depends(get_db)):
    return await crud.get_instances(db)


@router.post("/instances", response_model=InstanceRead, status_code=201)
async def create_instance(data: InstanceCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_instance(db, data)


@router.get("/instances/{instance_id}", response_model=InstanceRead)
async def get_instance(instance_id: int, db: AsyncSession = Depends(get_db)):
    inst = await crud.get_instance(db, instance_id)
    if not inst:
        raise HTTPException(404, "Instanz nicht gefunden")
    return inst


@router.put("/instances/{instance_id}", response_model=InstanceRead)
async def update_instance(instance_id: int, data: InstanceUpdate, db: AsyncSession = Depends(get_db)):
    inst = await crud.update_instance(db, instance_id, data)
    if not inst:
        raise HTTPException(404, "Instanz nicht gefunden")
    return inst


@router.delete("/instances/{instance_id}")
async def delete_instance(instance_id: int, db: AsyncSession = Depends(get_db)):
    if not await crud.delete_instance(db, instance_id):
        raise HTTPException(404, "Instanz nicht gefunden")
    return {"ok": True}


@router.post("/instances/{instance_id}/start")
async def start_instance(instance_id: int, db: AsyncSession = Depends(get_db)):
    inst = await crud.get_instance(db, instance_id)
    if not inst:
        raise HTTPException(404, "Instanz nicht gefunden")
    from ..services.monitor_manager import manager
    await manager.start_instance(instance_id, db)
    return {"ok": True, "message": f"Instanz '{inst.name}' gestartet"}


@router.post("/instances/{instance_id}/stop")
async def stop_instance(instance_id: int, db: AsyncSession = Depends(get_db)):
    inst = await crud.get_instance(db, instance_id)
    if not inst:
        raise HTTPException(404, "Instanz nicht gefunden")
    from ..services.monitor_manager import manager
    await manager.stop_instance(instance_id, db)
    return {"ok": True, "message": f"Instanz '{inst.name}' gestoppt"}


@router.get("/instances/{instance_id}/status")
async def instance_status(instance_id: int, db: AsyncSession = Depends(get_db)):
    inst = await crud.get_instance(db, instance_id)
    if not inst:
        raise HTTPException(404, "Instanz nicht gefunden")
    from ..services.monitor_manager import manager
    running = manager.is_running(instance_id)
    return {
        "id": inst.id,
        "name": inst.name,
        "is_connected": inst.is_connected,
        "running": running,
        "center_freq": inst.center_freq,
        "bandwidth": inst.bandwidth,
        "fft_size": inst.fft_size,
    }
