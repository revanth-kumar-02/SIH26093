import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db
from app.db.seed import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    asyncio.run(init_db())
    asyncio.run(seed_database())

@pytest.fixture
def client():
    return TestClient(app)
