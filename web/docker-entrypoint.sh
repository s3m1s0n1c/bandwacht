#!/bin/sh
set -e

# Start the FastAPI server (DB tables created automatically on startup)
exec python -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8000
