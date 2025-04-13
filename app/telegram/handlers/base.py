from aiogram import Router, types, F
from aiogram.filters import CommandStart
from app.models.admin import AdminDetails
from app.telegram.keyboards.admin import AdminPanel
from app.telegram.keyboards.base import CancelAction, Cancelkeyboard
from aiogram.fsm.context import FSMContext

router = Router(name="base")


@router.callback_query(Cancelkeyboard.Callback.filter(F.action == CancelAction.cancel))
@router.message(CommandStart())
async def command_start_handler(
    qmsg: types.Message | types.CallbackQuery,
    admin: AdminDetails | None,
    state: FSMContext | None = None,
) -> None:
    """
    This handler receives messages with `/start` command
    """
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
    if admin:
        await (qmsg.message if isinstance(qmsg, types.CallbackQuery) else qmsg).reply(
            text="Hello, adnin!", reply_markup=AdminPanel().as_markup()
        )
    else:
        await (qmsg.message if isinstance(qmsg, types.CallbackQuery) else qmsg).reply(
            f"Hello, {qmsg.from_user.full_name}!"
        )
