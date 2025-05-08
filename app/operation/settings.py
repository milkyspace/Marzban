from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Settings
from app.db.crud import get_settings, modify_settings
from app.models.settings import SettingsSchema
from . import BaseOperation


class SettingsOperation(BaseOperation):
    async def get_settings(self, db: AsyncSession) -> Settings:
        return await get_settings(db)
    
    async def modify_settings(self, db: AsyncSession, modify: SettingsSchema) -> SettingsSchema:
        db_settings = await self.get_settings(db)

        db_settings = await modify_settings(db, db_settings, modify)

        return SettingsSchema.model_validate(db_settings)
