"""The Prelegal application.

One ASGI app serves both halves of the product: the API under `/api`, and the
statically exported frontend at `/`.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from .config import settings
from .db import reset_database
from .routers import auth, chat, documents, health
from .static import mount_frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Recreates the database, and refuses to start without an API key.

    The chat is the only way to fill in an agreement, so a missing key means
    there is no product to serve. Better to say so on the way up than to let
    every conversation fail at its first message.
    """
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set, so the AI chat cannot run. Put it "
            "in the repo-root .env file (see README)."
        )

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
    api.include_router(chat.router)
    api.include_router(documents.router)
    app.include_router(api)

    # Last: the frontend mount matches every path, so it must not shadow the API.
    mount_frontend(app)
    return app


app = create_app()
