from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.exceptions import TelegramNetworkError
from aiogram.client.session.aiohttp import AiohttpSession
from app import on_startup, on_shutdown
from config import TELEGRAM_API_TOKEN, TELEGRAM_PROXY_URL, TELEGRAM_WEBHOOK_SECRET_KEY, TELEGRAM_WEBHOOK_URL
from .routers import admin, base
from .middlewares.acl import AclMiddleware

routes = (admin.router, base.router)

bot = None
dp = None
if TELEGRAM_API_TOKEN:
    session = AiohttpSession(proxy=TELEGRAM_PROXY_URL)
    bot = Bot(token=TELEGRAM_API_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()


def register_middlewares():
    dp.message.middleware.register(ChatActionMiddleware())
    dp.message.middleware.register(AclMiddleware())


@on_startup
async def initial_telegram_bot():
    if not TELEGRAM_API_TOKEN:
        return

    # register handlers
    dp.include_routers(*routes)

    register_middlewares()
    # register webhook
    webhook_address = f"{TELEGRAM_WEBHOOK_URL}/api/tghook/{TELEGRAM_API_TOKEN}"
    print(webhook_address)
    try:
        await bot.set_webhook(webhook_address, secret_token=TELEGRAM_WEBHOOK_SECRET_KEY)
    except TelegramNetworkError as err:
        print(err.message)


@on_shutdown
async def bot_down():
    if not TELEGRAM_API_TOKEN:
        return
    try:
        await bot.delete_webhook()
    except TelegramNetworkError:
        pass
    await dp.storage.close()
