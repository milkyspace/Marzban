from fastapi.testclient import TestClient
from decouple import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app import app
from app.db import get_db
from app.db.crud import create_admin
from app.db.base import Base
from app.models.admin import AdminCreate

TEST_FROM = config("TEST_FROM", default="local")

if TEST_FROM == "local":
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

    class GetTestDB:
        def __init__(self):
            self.db = TestSession()

        async def __aenter__(self):
            return self.db

        async def __aexit__(self, exc_type, exc_value, traceback):
            if isinstance(exc_value, SQLAlchemyError):
                await self.db.rollback()  # rollback on exception

            await self.db.close()

    async def get_test_db():
        async with GetTestDB() as db:
            yield db

    # Create tables for test database
    async def init_test_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            # Create a test admin user
            async with TestSession() as session:
                admin = AdminCreate(
                    username="testadmin",
                    password="TestAdmin#11",
                    is_sudo=True,
                )
                await create_admin(session, admin)

    app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)
