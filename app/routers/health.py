from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app import database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/alive")
def alive() -> PlainTextResponse:
    return PlainTextResponse("OK")


@router.get("/ready")
def ready() -> PlainTextResponse:
    if database.is_ready():
        return PlainTextResponse("OK")
    return PlainTextResponse("Database not available", status_code=500)
