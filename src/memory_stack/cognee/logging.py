"""Keep Cognee's logging from parking the event loop.

Cognee configures a structlog ``ConsoleRenderer`` on the root logger without
an explicit exception formatter, so structlog's default applies:
``RichTracebackFormatter(show_locals=True, max_frames=100)``. Every exception
raised inside a Cognee task is then rendered by Rich as nested tables of
locals, synchronously, on the thread that logged it, and that thread is the
Cognee event loop. With document-sized locals one render takes minutes
(2026-10-26 prod py-spy dump: the ``brain-cognee-asyncio`` thread at 100% CPU
inside ``rich/console.py`` under ``cognee/shared/logging_utils.py emit``).
While it renders, the loop services no I/O: Neo4j terminates the driver's new
Bolt connections after its 30 s authentication timeout, the next query fails
with ``Failed to read from defunct connection``, that exception is rendered
too, and the service stalls for the length of the storm (137k journal lines
in ten minutes, two restarts).

``tame_cognee_logging`` swaps every ``ConsoleRenderer`` found on the root
logger's handlers for one that prints plain tracebacks without locals. The
traceback text is unchanged in content; only the locals tables and colours
go. It is idempotent and cheap, so it runs on every Cognee import.
"""

from __future__ import annotations

import logging
from typing import Any

PLAIN_MARKER = "_brain_plain_tracebacks"


def plain_console_renderer() -> Any:
    import structlog

    renderer = structlog.dev.ConsoleRenderer(
        colors=False,
        exception_formatter=structlog.dev.plain_traceback,
    )
    setattr(renderer, PLAIN_MARKER, True)
    return renderer


def install_plain_renderer_default() -> bool:
    """Make every future ``ConsoleRenderer`` default to plain tracebacks.

    Cognee calls ``setup_logging()`` again at runtime
    (``cognee/shared/graph_model_utils.py`` does so from inside cognify) and
    each call adds a fresh stream handler with a fresh renderer, so patching
    the handlers present at import time is not enough: on 2026-10-26, after
    the import-time patch shipped in v2.0.32, cognify errors were still
    rendered with 98 locals panels per traceback. Wrapping the constructor
    catches renderers created by any caller, however late. An explicit
    ``exception_formatter`` passed by a caller is respected.

    Returns True when the wrapper was installed by this call.
    """
    try:
        import structlog
    except Exception:
        return False
    renderer_cls = structlog.dev.ConsoleRenderer
    original_init = renderer_cls.__init__
    if getattr(original_init, PLAIN_MARKER, False):
        return False

    def plain_default_init(self: Any, *args: Any, **kwargs: Any) -> None:
        if "exception_formatter" not in kwargs:
            kwargs["exception_formatter"] = structlog.dev.plain_traceback
            setattr(self, PLAIN_MARKER, True)
        original_init(self, *args, **kwargs)

    setattr(plain_default_init, PLAIN_MARKER, True)
    renderer_cls.__init__ = plain_default_init  # type: ignore[method-assign]
    return True


def tame_cognee_logging(root: logging.Logger | None = None) -> int:
    """Replace rich-with-locals exception rendering on Cognee's handlers.

    Patches the handlers already installed and makes every renderer created
    afterwards plain by default (``install_plain_renderer_default``).
    Returns the number of handlers patched (0 when structlog is absent or
    nothing needed patching).
    """
    try:
        import structlog
    except Exception:
        return 0
    install_plain_renderer_default()
    logger = root if root is not None else logging.getLogger()
    patched = 0
    for handler in list(logger.handlers):
        formatter = handler.formatter
        if not isinstance(formatter, structlog.stdlib.ProcessorFormatter):
            continue
        processors = list(getattr(formatter, "processors", ()))
        changed = False
        for index, processor in enumerate(processors):
            if isinstance(processor, structlog.dev.ConsoleRenderer) and not getattr(
                processor, PLAIN_MARKER, False
            ):
                processors[index] = plain_console_renderer()
                changed = True
        if changed:
            formatter.processors = tuple(processors)
            patched += 1
    return patched
