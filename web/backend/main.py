"""FastAPI application entry point."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import get_current_user
from .config import settings
from .database import init_db

# Add bandwacht module to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Seed default global targets if none exist
    await _seed_targets()
    # Auto-start all enabled instances
    await _autostart_instances()
    yield
    # Shutdown: stop all monitors
    from .services.monitor_manager import manager
    await manager.stop_all()


async def _seed_targets():
    """Seed default global targets on first run."""
    import logging
    from . import crud
    from .database import async_session

    try:
        async with async_session() as db:
            count = await crud.seed_global_targets(db)
            if count:
                logging.getLogger("bandwacht.web").info(f"Seeded {count} global targets")
    except Exception as e:
        logging.getLogger("bandwacht.web").error(f"Global target seeding failed: {e}")


async def _autostart_instances():
    """Start monitoring for all enabled SDR instances on boot."""
    import logging
    from . import crud
    from .database import async_session
    from .services.monitor_manager import manager

    logger = logging.getLogger("bandwacht.web")
    try:
        async with async_session() as db:
            instances = await crud.get_instances(db)
            started = 0
            for inst in instances:
                if not inst.enabled:
                    continue
                try:
                    await manager.start_instance(inst.id, db)
                    started += 1
                    logger.info(f"Auto-started instance '{inst.name}'")
                except Exception as e:
                    logger.warning(f"Failed to auto-start instance '{inst.name}': {e}")
            if started:
                logger.info(f"Auto-started {started} instance(s)")
    except Exception as e:
        logging.getLogger("bandwacht.web").error(f"Auto-start failed: {e}")


app = FastAPI(title="BandWacht Web", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from .routers import auth as auth_router  # noqa: E402
from .routers import events, instances, notifications, recordings, settings as settings_router, targets  # noqa: E402
from .services.ws_bridge import router as ws_router  # noqa: E402

# Auth router (public)
app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])

# Protected routers — require valid JWT
_auth = [Depends(get_current_user)]
app.include_router(instances.router, prefix="/api/v1", tags=["instances"], dependencies=_auth)
app.include_router(targets.router, prefix="/api/v1", tags=["targets"], dependencies=_auth)
app.include_router(events.router, prefix="/api/v1", tags=["events"], dependencies=_auth)
app.include_router(recordings.router, prefix="/api/v1", tags=["recordings"], dependencies=_auth)
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"], dependencies=_auth)
app.include_router(settings_router.router, prefix="/api/v1", tags=["settings"], dependencies=_auth)
app.include_router(ws_router)


@app.get("/api/v1/health")
async def health():
    from .services.monitor_manager import manager
    running = sum(1 for t in manager._tasks.values() if not t.done())
    return {"status": "ok", "version": "0.1.0", "monitors_running": running}


# Serve built frontend as static files (production)
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
