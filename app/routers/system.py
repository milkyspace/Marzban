from fastapi import APIRouter, Depends, HTTPException, Request
from aiogram.types import Update
from fastapi.responses import JSONResponse
from app import backend
from app.telegram import bot, dp
from app.db import AsyncSession, get_db
from app.models.admin import AdminDetails
from app.models.system import SystemStats
from config import TELEGRAM_API_TOKEN, TELEGRAM_WEBHOOK_SECRET_KEY
from .authentication import get_current
from app.utils import responses
from app.operation import OperatorType
from app.operation.system import SystemOperator


system_operator = SystemOperator(operator_type=OperatorType.API)
router = APIRouter(tags=["System"], prefix="/api", responses={401: responses._401})


@router.get("/system", response_model=SystemStats)
async def get_system_stats(db: AsyncSession = Depends(get_db), admin: AdminDetails = Depends(get_current)):
    """Fetch system stats including memory, CPU, and user metrics."""
    return await system_operator.get_system_stats(db, admin=admin)


@router.get("/inbounds", response_model=list[str])
async def get_inbounds(_: AdminDetails = Depends(get_current)):
    """Retrieve inbound configurations grouped by protocol."""
    return backend.config.inbounds


@router.post(f"/tghook/{TELEGRAM_API_TOKEN}", include_in_schema=False)
async def webhook_handler(request: Request):
    """Telegram webhook handler"""

    if TELEGRAM_WEBHOOK_SECRET_KEY:
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_token != TELEGRAM_WEBHOOK_SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid secret key")

    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return JSONResponse(status_code=200, content={"status": "ok"})
