from __future__ import annotations

from memory_stack.brain_models import RememberRequest
from memory_stack.config import Settings
from memory_stack.ingestion.rule_compiler import CompiledInput, compile_input


def compile_memory(request: RememberRequest, settings: Settings) -> CompiledInput:
    return compile_input(request, settings)
