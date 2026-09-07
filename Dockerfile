# The whole product in one image: the frontend is built to static HTML, then
# handed to the FastAPI process that also serves the API. Nothing but Python
# runs at runtime — Node is confined to the build stage.

# ---------- Build the frontend ----------
FROM node:22-alpine AS frontend

WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

# ---------- Runtime ----------
FROM python:3.12-slim AS runtime

# uv rather than pip: the backend is a uv project, and `--frozen` installs
# exactly what backend/uv.lock pins.
COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PRELEGAL_FRONTEND_DIR=/app/frontend/out \
    PRELEGAL_TEMPLATES_DIR=/app/templates \
    PRELEGAL_DATABASE_PATH=/app/data/prelegal.db

WORKDIR /app/backend

# Dependencies first, so editing application code does not reinstall them.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend ./
COPY --from=frontend /src/frontend/out /app/frontend/out

# The legal templates are read at request time now, not baked into the export:
# there are eleven documents, and serving one should not mean shipping a quarter
# of a megabyte of contract text to every visitor.
COPY templates /app/templates

ENV PATH="/app/backend/.venv/bin:$PATH"

# `/app/data` holds the SQLite file, which app.main recreates on every start —
# no volume is mounted for it, so a restart is a clean slate by design.
RUN mkdir -p /app/data && useradd --create-home --uid 1000 prelegal \
    && chown -R prelegal /app/data
USER prelegal

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
