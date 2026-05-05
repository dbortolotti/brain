"""Legacy Cognee query-case reader.

New Brain eval fixtures live under memory_stack.evals.fixtures.
"""
from __future__ import annotations

from pathlib import Path

from memory_stack.io import load_eval_queries
from memory_stack.models import EvalQuery


def read_queries(path: str | Path = "eval/queries.yaml") -> list[EvalQuery]:
    return load_eval_queries(path)
