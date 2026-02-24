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
    yield
    # Shutdown: stop all monitors
    from .services.monitor_manager import manager
    await manager.stop_all()


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
