from __future__ import annotations

from pathlib import Path


def test_brain_agent_memory_script_defaults_to_portable_session() -> None:
    script = Path("scripts/brain_agent_memory.py").read_text(encoding="utf-8")

    assert 'DEFAULT_SESSION_ID = "portable_agent_session"' in script
    assert "brain_cognee_agent_memory_dataset" in script
    assert "session_ids=[session_id]" in script
