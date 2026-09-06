"""Liveness endpoint.

Used by the start scripts to know when the container is actually serving, and
by anything watching the deployment later.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str


@router.get("/health")
def health() -> Health:
    return Health(status="ok")
