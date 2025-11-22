"""Application factory and FastAPI app setup for FRAGAZ.
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from .controllers import router as controllers_router

logger = logging.getLogger("fragaz.app")


def create_app() -> FastAPI:
    app = FastAPI(title="FRAGAZ Backend", version="0.1")

    # CORS middleware
    from fastapi.middleware.cors import CORSMiddleware

    _origins_env = os.environ.get("FRONTEND_ORIGINS")
    if _origins_env:
        try:
            import json as _json

            origins = _json.loads(_origins_env) if (_origins_env.strip().startswith("[")) else [o.strip() for o in _origins_env.split(",")]
        except Exception:
            origins = [o.strip() for o in _origins_env.split(",")]
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include controllers
    app.include_router(controllers_router)

    return app


app = create_app()
