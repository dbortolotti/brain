from __future__ import annotations

import io
import logging
import time

import structlog

from memory_stack.cognee.logging import PLAIN_MARKER, tame_cognee_logging


def _cognee_style_handler(stream: io.StringIO) -> logging.Handler:
    # Mirrors cognee/shared/logging_utils.py: a ConsoleRenderer with the
    # structlog default exception formatter (rich, show_locals=True).
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True, force_colors=True),
        )
    )
    return handler


def test_tame_cognee_logging_replaces_rich_locals_renderer_idempotently() -> None:
    root = logging.Logger("cognee-test-root")
    stream = io.StringIO()
    handler = _cognee_style_handler(stream)
    root.addHandler(handler)

    assert tame_cognee_logging(root) == 1
    renderer = [
        p
        for p in handler.formatter.processors  # type: ignore[union-attr]
        if isinstance(p, structlog.dev.ConsoleRenderer)
    ][0]
    assert getattr(renderer, PLAIN_MARKER, False) is True
    assert renderer._exception_formatter is structlog.dev.plain_traceback
    # Second call finds nothing left to patch.
    assert tame_cognee_logging(root) == 0


def test_plain_tracebacks_omit_locals_and_render_fast() -> None:
    root = logging.Logger("cognee-test-root-2")
    stream = io.StringIO()
    handler = _cognee_style_handler(stream)
    root.addHandler(handler)
    tame_cognee_logging(root)

    document_text = "SENTINEL-LOCAL " * 20_000  # a document-sized local

    def fail() -> None:
        payload = {"chunks": [document_text] * 50}  # noqa: F841 - must be a local
        raise RuntimeError("Failed to read from defunct connection")

    started = time.perf_counter()
    try:
        fail()
    except RuntimeError:
        root.exception("Coroutine task errored")
    elapsed = time.perf_counter() - started

    rendered = stream.getvalue()
    assert "Failed to read from defunct connection" in rendered
    assert "Traceback" in rendered
    assert "SENTINEL-LOCAL" not in rendered, "locals must not be rendered"
    assert elapsed < 2.0, f"plain traceback took {elapsed:.1f}s"
