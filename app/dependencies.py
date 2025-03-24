from app import on_startup
from app.utils import jwt
from app.db import GetDB, get_jwt_secret_key


@on_startup
async def set_secret_key():
    async with GetDB() as db:
        jwt.key = await get_jwt_secret_key(db=db)
