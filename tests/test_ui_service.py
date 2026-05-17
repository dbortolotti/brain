from __future__ import annotations

from pathlib import Path

from memory_stack.ui_service import isolate_frontend_cache


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


def test_dashboard_login_asks_for_username_without_autosuggest() -> None:
    html = Path("src/memory_stack/static/brain_app/index.html").read_text(encoding="utf-8")

    assert 'id="loginForm"' in html
    assert 'autocomplete="off"' in html
    assert 'id="loginUserId"' in html
    assert 'aria-label="Username"' in html
    assert 'placeholder="username"' in html
    assert 'autocomplete="username"' not in html


def test_dashboard_layout_constrains_work_surface_width() -> None:
    css = Path("src/memory_stack/static/brain_app/app.css").read_text(encoding="utf-8")

    assert "--content-max: 1280px;" in css
    assert "max-width: var(--content-max);" in css
    assert "margin-inline: auto;" in css
    assert ".content-head > div" in css
    assert "overflow-wrap: anywhere;" in css
    assert ".form-row > .field.inline" in css
    assert "flex-basis: 100%;" in css
