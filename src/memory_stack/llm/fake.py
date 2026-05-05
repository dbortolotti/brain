from __future__ import annotations

from typing import Any


class FakeLLMClient:
    def __init__(self, outputs: list[dict[str, Any]] | dict[str, Any]) -> None:
        self.outputs = outputs if isinstance(outputs, list) else [outputs]
        self.calls: list[dict[str, Any]] = []

    def complete_json(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, "schema": schema, "kwargs": kwargs})
        if not self.outputs:
            raise AssertionError("FakeLLMClient has no queued outputs.")
        return self.outputs.pop(0)
