from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app import on_startup, on_shutdown
from config import TELEGRAM_API_TOKEN, TELEGRAM_WEBHOOK_SECRET_KEY, TELEGRAM_WEBHOOK_URL
from .routers import admin, base

routes = (admin.router, base.router)

bot = None
dp = None
if TELEGRAM_API_TOKEN:
    bot = Bot(token=TELEGRAM_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()


@on_startup
async def initial_telegram_bot():
    if not TELEGRAM_API_TOKEN:
        return

    dp.include_routers(*routes)

    webhook_address = f"{TELEGRAM_WEBHOOK_URL}/api/tghook/{TELEGRAM_API_TOKEN}"
    print(webhook_address)
    await bot.set_webhook(webhook_address, secret_token=TELEGRAM_WEBHOOK_SECRET_KEY)


@on_shutdown
async def bot_down():
    if not TELEGRAM_API_TOKEN:
        return
    await bot.delete_webhook()
    await dp.storage.close()
