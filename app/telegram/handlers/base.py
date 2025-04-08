from aiogram import Router, types,F
from aiogram.filters import CommandStart
from app.models.admin import AdminDetails
from app.telegram.keyboards.admin import AdminPanel
from app.telegram.keyboards.base import Cancelkeyboard
from aiogram.fsm.context import FSMContext

router = Router(name="base")


@router.message(F.text.casefold() == Cancelkeyboard.cancel)
@router.message(CommandStart())
async def command_start_handler(
    message: types.Message,
    admin: AdminDetails | None,
    state: FSMContext | None = None,
) -> None:
    """
    This handler receives messages with `/start` command
    """
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
    if admin:
        await message.reply(text="Hello, adnin!", reply_markup=AdminPanel().as_markup())
    else:
        await message.answer(f"Hello, {message.from_user.full_name}!")
