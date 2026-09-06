"""The Prelegal application.

One ASGI app serves both halves of the product: the API under `/api`, and the
statically exported frontend at `/`.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from .db import reset_database
from .routers import auth, health
from .static import mount_frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Recreates the database from scratch on every startup."""
    reset_database()
    logger.info("Database initialized.")
    yield


def create_app() -> FastAPI:
    """Builds the application.

    A factory rather than a module-level instance so tests can build an app
    against their own settings instead of sharing one process-wide.
    """
    app = FastAPI(
        title="Prelegal",
        description="Draft legal agreements from curated templates.",
        version="0.1.0",
        lifespan=lifespan,
    )

    api = APIRouter(prefix="/api")
    api.include_router(health.router)
    api.include_router(auth.router)
    app.include_router(api)

    # Last: the frontend mount matches every path, so it must not shadow the API.
    mount_frontend(app)
    return app


app = create_app()
