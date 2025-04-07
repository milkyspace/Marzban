from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router(name="base")


@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {message.from_user.full_name}!")
