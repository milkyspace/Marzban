from aiogram import Router, types
from aiogram.filters import CommandStart

from app.models.admin import AdminDetails
from app.telegram.keyboards.admin import AdminPanel

router = Router(name="base")


@router.message(CommandStart())
async def command_start_handler(message: types.Message, admin: AdminDetails | None) -> None:
    """
    This handler receives messages with `/start` command
    """
    if admin:
        await message.reply(text="Hello, adnin!", reply_markup=AdminPanel().as_markup())
    else:
        await message.answer(f"Hello, {message.from_user.full_name}!")
