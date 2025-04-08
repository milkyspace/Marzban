from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.models.admin import AdminDetails
from app.telegram.keyboards.admin import AdminPanel, AdminPanelAction
from app.telegram.utils.filters import IsAdminfilter

from . import router


@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.create_user),
    IsAdminfilter(),
)
async def create_user(query: CallbackQuery, admin: AdminDetails | None, callback_data: AdminPanel.Callback):
    print(callback_data)
    await query.message.reply("create user")


@router.message(Command(commands=("user")))
async def admin_panel(message: Message):
    await message.reply("hello admin from user")
