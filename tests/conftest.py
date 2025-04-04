import os
import sys
import pytest
import asyncio
import warnings
from pydantic import PydanticDeprecatedSince20

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import the init_test_db function from tests.api
from tests.api import init_test_db  # noqa


# Filter out all warnings
@pytest.fixture(autouse=True)
def ignore_all_warnings():
    warnings.filterwarnings("ignore")
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up the test database before running any tests."""
    # Initialize the database
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_test_db())
