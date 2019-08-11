import pytest

from service.__main__ import spawn_app


@pytest.fixture
async def client(aiohttp_client):
    app = spawn_app()
    return await aiohttp_client(app)
