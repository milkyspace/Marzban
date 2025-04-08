from aiogram import Dispatcher

from . import admin, base

handlers = (
    admin,
    base,
)


def include_routers(dp: Dispatcher) -> None:
    for handler in handlers:
        if hasattr(handler, "init_handler"):
            handler.init_handler()
        if hasattr(handler, "router"):
            dp.include_router(handler.router)
