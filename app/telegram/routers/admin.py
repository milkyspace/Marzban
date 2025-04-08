from aiogram import Router, types
from aiogram.filters import Command
from app.models.admin import AdminDetails

router = Router(name="admin")



@router.message(Command(commands=("admin"), prefix="/"))
async def admin_panel(message: types.Message, admin: AdminDetails | None):
    await message.reply("hello admin")
