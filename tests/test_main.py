from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

@pytest.mark.parametrize("id", [1, 2, 3])
def test_test(id: int):
    response = client.get(f"/test/{id}")
    assert response.status_code == 200
