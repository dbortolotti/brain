from __future__ import annotations

import ast
from pathlib import Path


SCRIPT = Path("scripts/staging_e2e_suite.py")


def script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_staging_e2e_script_is_opt_in_and_targets_staging() -> None:
    text = script_text()

    assert "https://brain-staging.dceb.net" in text
    assert "brain-auth-e2e-password" in text
    assert 'parser.add_argument("--test-user", default="brain-e2e")' in text
    assert 'parser.add_argument("--judge-model", default="gpt-5.5")' in text
    assert 'parser.add_argument("--judge-reasoning-effort", default="high")' in text


def test_staging_e2e_script_primes_memory_sources_and_palate_organically() -> None:
    text = script_text()

    assert "brain_remember" in text
    assert "brain_ingest_source" in text
    assert "brain_palate_confirm" in text
    assert "remember 2016 Cuvee Sasha in palate" in text
    assert "Mayfair Food Fayre Caesar salad wrap" in text
    assert "Kind of Blue" in text
    assert "confirmed_by_user" in text


def test_staging_e2e_script_uses_llm_judge_schema() -> None:
    tree = ast.parse(script_text())
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    assert "score_case" in function_names
    assert "build_judge" in function_names
    assert "run_isolation_check" in function_names
    assert "complete_json" in script_text()
    assert "brain_staging_e2e_judgement" in script_text()


def test_staging_e2e_script_does_not_belong_to_default_pytest_mutation_path() -> None:
    text = script_text()

    assert "if __name__ == \"__main__\"" in text
    assert "pytest" not in text
