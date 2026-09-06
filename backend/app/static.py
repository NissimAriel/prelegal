"""Serving the statically exported frontend.

The frontend is built with Next's `output: 'export'`, which produces a tree of
plain HTML and assets in `frontend/out`. FastAPI serves that tree at `/`, so
the whole product is one process on one port with no CORS and no Node at
runtime.
"""

import logging

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .config import settings

logger = logging.getLogger(__name__)

BUILD_INSTRUCTIONS = (
    "The frontend has not been built.\n\n"
    "Run the app with scripts/start-<platform>, which builds it, or build it "
    "by hand with `npm ci && npm run build` in frontend/.\n"
)


def mount_frontend(app: FastAPI) -> None:
    """Mounts the exported frontend at `/`, if it has been built.

    Must be called after every API route is registered: a mount at `/` matches
    every path, so anything added afterwards would be shadowed by it.

    A missing build is not fatal. The backend is useful on its own — running
    its tests, or working on the API — and failing to start would make that
    impossible for the sake of a static file tree.
    """
    if not (settings.frontend_dir / "index.html").is_file():
        logger.warning(
            "No frontend build at %s; serving build instructions at / instead.",
            settings.frontend_dir,
        )

        @app.get("/{_path:path}", include_in_schema=False)
        def frontend_missing(_path: str) -> PlainTextResponse:
            return PlainTextResponse(BUILD_INSTRUCTIONS, status_code=503)

        return

    # `html=True` resolves a directory to its index.html, which is what Next's
    # export emits for each route, and serves out/404.html for unknown paths.
    app.mount(
        "/",
        StaticFiles(directory=settings.frontend_dir, html=True),
        name="frontend",
    )
