"""Runtime configuration, resolved once at import time.

Every value has a default that works for a developer running the backend
straight out of a checkout, and an environment variable that the Docker image
sets to point at the paths it actually uses.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# `backend/app/config.py` -> `backend/` -> repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# The repo-root `.env` holds OPENROUTER_API_KEY. It is gitignored and absent in
# the Docker image, where compose injects the same variable from the host's
# copy instead, so a missing file here is normal rather than an error.
load_dotenv(REPO_ROOT / ".env")


def _path_from_env(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).resolve() if value else default


class Settings:
    """Where the app's two pieces of state live on disk.

    Read as attributes rather than a dict so a typo is an AttributeError at
    startup instead of a silently missing setting.
    """

    def __init__(self) -> None:
        #: SQLite file. Deleted and recreated on every startup — see `db.py`.
        self.database_path = _path_from_env(
            "PRELEGAL_DATABASE_PATH", REPO_ROOT / "prelegal.db"
        )
        #: The statically exported frontend (`next build` output), served at `/`.
        self.frontend_dir = _path_from_env(
            "PRELEGAL_FRONTEND_DIR", REPO_ROOT / "frontend" / "out"
        )
        #: The curated legal templates listed in catalog.json.
        self.templates_dir = _path_from_env(
            "PRELEGAL_TEMPLATES_DIR", REPO_ROOT / "templates"
        )
        #: Read by LiteLLM. Checked at startup — see `main.lifespan`.
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")


settings = Settings()
