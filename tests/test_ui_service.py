from __future__ import annotations

import os

from memory_stack.ui_service import (
    frontend_dependencies_ready,
    isolate_frontend_cache,
    prepare_frontend,
)


def test_isolate_frontend_cache_copies_frontend_without_runtime_dirs(tmp_path) -> None:
    source = tmp_path / "source-frontend"
    source.mkdir()
    (source / "package.json").write_text("{}", encoding="utf-8")
    (source / ".next").mkdir()
    (source / ".next" / "lock").write_text("locked", encoding="utf-8")
    (source / "node_modules").mkdir()
    (source / "node_modules" / "dep").write_text("installed", encoding="utf-8")

    target = isolate_frontend_cache(source, cache_root=tmp_path / "cache", version="1.2.3")

    assert target == tmp_path / "cache" / "frontend"
    assert (target / "package.json").exists()
    assert not (target / ".next").exists()
    assert not (target / "node_modules").exists()
    assert (tmp_path / "cache" / "version.txt").read_text(encoding="utf-8").strip() == "1.2.3"


def test_isolate_frontend_cache_refreshes_on_version_change(tmp_path) -> None:
    source = tmp_path / "source-frontend"
    source.mkdir()
    (source / "package.json").write_text('{"version":"new"}', encoding="utf-8")
    cache_root = tmp_path / "cache"
    target = cache_root / "frontend"
    target.mkdir(parents=True)
    (target / "package.json").write_text('{"version":"old"}', encoding="utf-8")
    (cache_root / "version.txt").write_text("old\n", encoding="utf-8")

    isolate_frontend_cache(source, cache_root=cache_root, version="new")

    assert (target / "package.json").read_text(encoding="utf-8") == '{"version":"new"}'
    assert (cache_root / "version.txt").read_text(encoding="utf-8").strip() == "new"


def test_prepare_frontend_uses_explicit_cache_dir(monkeypatch, tmp_path) -> None:
    original_env = os.environ.copy()
    source = tmp_path / "source-frontend"
    source.mkdir()
    (source / "package.json").write_text("{}", encoding="utf-8")
    cache_root = tmp_path / "local-ui-cache"

    import memory_stack.ui_service as ui_service

    monkeypatch.setattr(
        "cognee.api.v1.ui.ui.download_frontend_assets",
        lambda force=False: True,
    )
    monkeypatch.setattr("cognee.api.v1.ui.ui.find_frontend_path", lambda: source)
    monkeypatch.setattr("cognee.version.get_cognee_version", lambda: "test-version")
    monkeypatch.setattr(ui_service, "run", lambda command, *, cwd: None)

    class Settings:
        brain_ui_cache_dir = str(cache_root)
        brain_prod_root = str(tmp_path / "external-root")

    try:
        assert prepare_frontend(Settings()) == cache_root / "frontend"
        assert (cache_root / "frontend" / "package.json").exists()
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_prepare_frontend_skips_npm_install_when_dependencies_exist(monkeypatch, tmp_path) -> None:
    source = tmp_path / "source-frontend"
    source.mkdir()
    (source / "package.json").write_text("{}", encoding="utf-8")
    cache_root = tmp_path / "local-ui-cache"
    frontend = cache_root / "frontend"
    next_bin = frontend / "node_modules" / ".bin" / "next"
    next_bin.parent.mkdir(parents=True)
    next_bin.write_text("", encoding="utf-8")
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    (cache_root / "version.txt").write_text("test-version\n", encoding="utf-8")

    import memory_stack.ui_service as ui_service

    monkeypatch.setattr(
        "cognee.api.v1.ui.ui.download_frontend_assets",
        lambda force=False: True,
    )
    monkeypatch.setattr("cognee.api.v1.ui.ui.find_frontend_path", lambda: source)
    monkeypatch.setattr("cognee.version.get_cognee_version", lambda: "test-version")
    monkeypatch.setattr(
        ui_service,
        "run",
        lambda command, *, cwd: (_ for _ in ()).throw(AssertionError("unexpected npm install")),
    )

    class Settings:
        brain_ui_cache_dir = str(cache_root)
        brain_prod_root = str(tmp_path / "external-root")

    assert frontend_dependencies_ready(frontend)
    assert prepare_frontend(Settings()) == frontend

