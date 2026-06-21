"""Project-root uvicorn entry point.

This keeps `uvicorn app.main:app --reload --port 8000` working from the
repository root while the real backend source remains under `backend/app`.
"""

from backend.app.main import app

__all__ = ["app"]

