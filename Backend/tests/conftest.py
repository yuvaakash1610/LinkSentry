import pytest
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client using starlette/httpx."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncClient:
    """Asynchronous test client using httpx."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def settings():
    """Application settings fixture."""
    return get_settings()
