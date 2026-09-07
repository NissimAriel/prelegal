# prelegal

A platform for drafting common legal agreements.

**Status:** 🚧 In progress — expected completion in 1 week.

## Running it

Docker is the only prerequisite, plus an `OPENROUTER_API_KEY` in a repo-root
`.env` file — the assistant that fills in the agreement needs it, and the app
refuses to start without it. The scripts build the image and wait for the app
to answer before returning.

```bash
# Mac
scripts/start-mac.sh
scripts/stop-mac.sh

# Linux
scripts/start-linux.sh
scripts/stop-linux.sh
```

```powershell
# Windows
scripts\start-windows.ps1
scripts\stop-windows.ps1
```

Then open <http://localhost:8000>. Sign in with any email address — there is no
authentication yet, and the session it creates lasts until the app restarts.
Describe what you need in your own words: the assistant picks the right
template from the eleven below and fills it in as you talk. Ask for something
it has no template for and it will say so, and offer the closest thing it can
draft.

## How it fits together

One container, one port. The frontend is exported to static HTML at build time
and served by the same FastAPI process that answers the API, so there is no
Node at runtime and no CORS to configure.

| Path | Directory | What it is |
| --- | --- | --- |
| `/api/*` | `backend/` | FastAPI, a [uv](https://docs.astral.sh/uv/) project |
| `/*` | `frontend/` | Next.js, built with `output: 'export'` |
| — | `templates/` | The Common Paper agreements, served by the API |

Each document type is described by a spec in `backend/app/documents/`, listing
the values it needs and how they render onto a cover page. Those specs drive
everything: the assistant's prompt, the live preview, and what counts as
complete. Adding a document type means adding a spec, not writing components.

The assistant runs on `openai/gpt-oss-120b` via OpenRouter, pinned to Cerebras
as the inference provider. Conversations are not stored: the browser holds the
transcript and sends it with each turn.

The SQLite database is **recreated from scratch on every start**. Nothing a
user enters survives a restart; that is deliberate while the product is being
built, and is why no volume is mounted for it.

## Developing

```bash
cd backend  && uv run pytest            # backend tests
cd frontend && npm test                 # frontend tests
cd frontend && npm ci && npm run build  # produces frontend/out
cd backend  && uv run uvicorn app.main:app --reload --port 8000
```

Run the frontend build before the backend and it will serve the result at `/`;
skip it and the backend still runs, serving build instructions there instead.
