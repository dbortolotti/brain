from __future__ import annotations

from fastapi.testclient import TestClient

from memory_stack.mcp_server import app


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["service"] == "Brain"


def test_mcp_initialize() -> None:
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "brain"

