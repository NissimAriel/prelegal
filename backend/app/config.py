"""Runtime configuration, resolved once at import time.

Every value has a default that works for a developer running the backend
straight out of a checkout, and an environment variable that the Docker image
sets to point at the paths it actually uses.
"""

import os
from pathlib import Path

# `backend/app/config.py` -> `backend/` -> repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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


settings = Settings()
