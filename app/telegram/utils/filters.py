from aiogram.filters import Filter


class IsAdminfilter(Filter):
    async def __call__(self, *args, **kwargs) -> bool:
        return bool(kwargs.get("admin"))


class IsAdminSUDO(Filter):
    async def __call__(self, *args, **kwargs) -> bool:
        if admin := kwargs.get("admin"):
            return admin.is_sudo
        return False
