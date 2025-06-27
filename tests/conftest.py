import pytest
from fastapi.testclient import TestClient
from main import app  # Импортируй объект FastAPI

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
