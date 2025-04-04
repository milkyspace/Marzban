import os
import sys
import pytest
import warnings
from pydantic import PydanticDeprecatedSince20

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


# Filter out all warnings
@pytest.fixture(autouse=True)
def ignore_all_warnings():
    warnings.filterwarnings("ignore")
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)




# @pytest.mark.skipif(TEST_FROM != "local", reason="Skipping database setup for remote tests")
# @pytest.mark.asyncio(scope="session")
# async def init_test_db():
#     """Initialize the test database before running any tests."""
#     from tests.api import create_tables

#     await create_tables()
