from aiogram import Router, types
from aiogram.filters import CommandStart

from app.models.admin import AdminDetails

router = Router(name="base")


@router.message(CommandStart())
async def command_start_handler(message: types.Message, admin: AdminDetails | None) -> None:
    """
    This handler receives messages with `/start` command
    """
    if admin:
        await message.answer("Hello, adnin!")
    else:
        await message.answer(f"Hello, {message.from_user.full_name}!")
