from __future__ import annotations

import ast
from pathlib import Path

from memory_stack.agents.role_specs import (
    REQUIRED_ROLE_SPEC_SECTIONS,
    markdown_heading_positions,
    markdown_section_lines,
    role_spec_markdown,
    role_spec_role_names,
)
from memory_stack.evals.model_fixtures import FINE_GRAINED_ROLE_FIXTURE_SOURCES, ModelEvalFixture, fixture_prompt


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_every_fine_grained_role_has_agent_spec() -> None:
    expected_roles = set(FINE_GRAINED_ROLE_FIXTURE_SOURCES)
    spec_roles = role_spec_role_names()

    assert spec_roles == expected_roles


def test_agent_role_specs_follow_required_contract_shape() -> None:
    for role in sorted(role_spec_role_names()):
        text = role_spec_markdown(role)
        assert text is not None
        lines = text.splitlines()

        assert lines[0] == f"# {role}"

        headings = markdown_heading_positions(lines)
        expected_positions = [headings.get(section) for section in REQUIRED_ROLE_SPEC_SECTIONS]
        assert None not in expected_positions, f"{role} missing required section"
        assert expected_positions == sorted(expected_positions), f"{role} required sections are out of order"

        for section in REQUIRED_ROLE_SPEC_SECTIONS:
            assert markdown_section_lines(text, section), f"{role} has empty {section} section"


def test_fine_grained_fixture_prompts_include_agent_spec() -> None:
    for role in sorted(FINE_GRAINED_ROLE_FIXTURE_SOURCES):
        fixture = ModelEvalFixture(
            id=f"{role}_agent_spec_contract",
            scenario_group="agent_spec_contract",
            role=role,
            input_text="Contract smoke input.",
            expected={},
        )

        prompt = fixture_prompt(fixture)

        assert f"Role markdown from src/memory_stack/agents/roles/{role}.md" in prompt
        assert "## Purpose" in prompt
        assert "## Decision Procedure" in prompt
        assert "## Must Not Do" in prompt


def test_entity_candidate_ranker_contract_requires_unique_disambiguating_evidence() -> None:
    text = role_spec_markdown("entity_candidate_ranker")
    assert text is not None

    assert "only when the evidence identifies one specific supplied candidate" in text
    assert "exact surface-text match is not sufficient" in text
    assert "compressed punctuation lists as ambiguous" in text
    assert "Do not infer \"no competing candidates\"" in text
    assert "Prefer a false clarification over a false merge" in text


def test_eval_role_llm_calls_use_central_fixture_prompt() -> None:
    violations: list[str] = []
    eval_dir = REPO_ROOT / "src" / "memory_stack" / "evals"
    for path in eval_dir.glob("*.py"):
        if path.name == "provider_client.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "complete_json":
                continue
            prompt_keywords = [keyword for keyword in node.keywords if keyword.arg == "prompt"]
            if not prompt_keywords:
                continue
            prompt_value = prompt_keywords[0].value
            if (
                isinstance(prompt_value, ast.Call)
                and isinstance(prompt_value.func, ast.Name)
                and prompt_value.func.id == "fixture_prompt"
            ):
                continue
            violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")

    assert violations == []
