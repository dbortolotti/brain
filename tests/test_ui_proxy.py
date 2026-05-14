from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def test_rewrite_backend_absolute_redirect(monkeypatch) -> None:
    ui_proxy = load_ui_proxy(monkeypatch)

    rewritten = ui_proxy.rewrite_redirect_location(
        "https://127.0.0.1:8001/api/v1/datasets?range=24h",
        ui_proxy.backend_base_url(),
    )

    assert rewritten == "/ui-api/api/v1/datasets?range=24h"


def test_rewrite_backend_relative_redirect(monkeypatch) -> None:
    ui_proxy = load_ui_proxy(monkeypatch)

    rewritten = ui_proxy.rewrite_redirect_location(
        "/api/v1/datasets",
        ui_proxy.backend_base_url(),
    )

    assert rewritten == "/ui-api/api/v1/datasets"


def test_rewrite_frontend_absolute_redirect(monkeypatch) -> None:
    ui_proxy = load_ui_proxy(monkeypatch)

    rewritten = ui_proxy.rewrite_redirect_location(
        "http://127.0.0.1:3000/dashboard?tab=data",
        ui_proxy.frontend_base_url(),
    )

    assert rewritten == "/dashboard?tab=data"


def test_rewrite_external_redirect_leaves_location_unchanged(monkeypatch) -> None:
    ui_proxy = load_ui_proxy(monkeypatch)

    location = "https://example.com/login"

    assert ui_proxy.rewrite_redirect_location(location, ui_proxy.backend_base_url()) == location


def test_icon_routes_do_not_require_ui_session(monkeypatch) -> None:
    ui_proxy = load_ui_proxy(monkeypatch)
    client = TestClient(ui_proxy.app)

    response = client.get("/icon.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def load_ui_proxy(monkeypatch):
    monkeypatch.setenv("BRAIN_AUTH_PASSWORD", "test-password")
    monkeypatch.setenv("BRAIN_PUBLIC_BASE_URL", "https://brain.dceb.net")
    monkeypatch.setenv("BRAIN_PUBLIC_UI_API_PATH", "/ui-api")

    import memory_stack.ui_proxy as ui_proxy

    return importlib.reload(ui_proxy)
