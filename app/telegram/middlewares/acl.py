from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, Update

from app.db import GetDB, crud
from app.models.admin import AdminDetails


class ACLMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]], event: Update, data: Dict[str, Any]
    ) -> Any:
        user_id = (event.message or event.callback_query).from_user.id
        async with GetDB() as db:
            admin = await crud.get_admin_by_telegram_id(db, user_id)
            if admin:
                admin = AdminDetails.model_validate(admin)
                data["admin"] = admin
            else:
                data["admin"] = None
        return await handler(event, data)
