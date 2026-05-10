from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from memory_stack.model_registry import (
    capability_definitions,
    deterministic_roles,
    disabled_roles,
    eligible_role_models,
    mandatory_capabilities,
    role_enabled,
    role_model,
)


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "brain_model_registry.yaml"


def test_brain_model_registry_loads() -> None:
    registry = load_registry()

    assert registry["version"] == 1
    assert registry["roles"]
    assert registry["providers"]
    assert registry["core_eval_matrix"]


def test_brain_model_registry_references_known_models() -> None:
    registry = load_registry()
    known_models = model_refs(registry)
    skipped_models = skipped_model_refs(registry)

    for role, config in registry["roles"].items():
        for model in config.get("preferred_models", []):
            assert model in known_models, f"{role} references unknown model {model}"
            assert model not in skipped_models, f"{role} references skipped model {model}"

    for role, models in registry["core_eval_matrix"].items():
        assert role in registry["roles"], f"core matrix references unknown role {role}"
        for model in models:
            assert model in known_models, f"{role} core matrix references unknown model {model}"
            assert model not in skipped_models, f"{role} core matrix references skipped model {model}"


def test_groq_and_mistral_removed_from_fine_grained_matrix() -> None:
    registry = load_registry()
    matrix = registry["fine_grained_eval_matrix"]
    blocked_prefixes = (
        "groq:",
        "aws-bedrock:mistral.",
    )

    for role, models in matrix.items():
        for model in models:
            assert not model.startswith(blocked_prefixes), f"{role} still references blocked provider model {model}"


def test_gpt55_high_in_benchmark_roles_only() -> None:
    matrix = load_registry()["fine_grained_eval_matrix"]
    allowed_roles = {
        "atomic_card_extractor",
        "source_takeaway_extractor",
        "entity_candidate_ranker",
        "conflict_candidate_detector",
        "conflict_policy_decider",
        "recall_synthesizer",
        "groundedness_checker",
        "eval_judge",
    }

    for role, models in matrix.items():
        if "openai:gpt-5.5-high" in models:
            assert role in allowed_roles


def test_registry_owns_fine_grained_capability_topology() -> None:
    registry = load_registry()
    capabilities = capability_definitions(registry)

    assert capabilities["slack_intake"]["required_model_roles"] == [
        "source_classifier",
        "durability_filter",
        "memory_kind_classifier",
        "repair_option_generator",
        "commit_policy_decider",
        "success_receipt_generator",
    ]
    assert deterministic_roles("slack_intake", registry) == [
        "zero_tolerance_validator",
    ]
    assert "entity_final_resolver" in capabilities["entity_resolution"]["required_model_roles"]
    assert deterministic_roles("entity_resolution", registry) == []
    assert "conflict_policy_decider" in capabilities["conflict_handling"]["required_model_roles"]
    assert deterministic_roles("conflict_handling", registry) == []
    assert "recall_relevance_filter" in capabilities["recall"]["required_model_roles"]
    assert deterministic_roles("recall", registry) == []
    assert "slack_intake" in mandatory_capabilities(registry)
    assert "debug" not in mandatory_capabilities(registry)
    assert "success_receipt_generator" in registry["fine_grained_eval_matrix"]


def test_registry_exposes_runtime_deployment_decisions() -> None:
    registry = load_registry()

    assert eligible_role_models(registry)["debug_explainer"] == "google:gemini-2.5-flash-lite"
    assert role_model("eval_judge", registry) == "openai:gpt-5.5"
    assert role_enabled("recall_synthesizer", registry) is False
    assert "atomic_card_extractor" in disabled_roles(registry)


def test_registry_includes_google_embedding_candidates() -> None:
    registry = load_registry()
    embeddings = registry["providers"]["embeddings"]["models"]
    by_ref = {f"{model['provider']}:{model['id']}": model for model in embeddings}

    assert registry["roles"]["embeddings"]["preferred_models"][0] == (
        "fastembed:intfloat/multilingual-e5-large"
    )
    assert registry["core_eval_matrix"]["embeddings"][0] == (
        "fastembed:intfloat/multilingual-e5-large"
    )
    assert by_ref["fastembed:intfloat/multilingual-e5-large"]["enabled_by_default"] is True
    assert by_ref["fastembed:intfloat/multilingual-e5-large"]["dimensions"] == 1024
    assert by_ref["google:gemini-embedding-001"]["price_per_1m"]["input"] == 0.15
    assert by_ref["google:gemini-embedding-001"]["price_per_1m"]["batch_input"] == 0.075
    assert by_ref["google:gemini-embedding-2"]["price_per_1m"]["input"] == 0.20
    assert by_ref["google-vertex:multilingual-e5-small"]["price_per_1m"]["input"] == 0.015
    assert by_ref["google-vertex:multilingual-e5-large"]["price_per_1m"]["input"] == 0.025
    assert by_ref["google-vertex:text-embedding-005"]["price_per_1m"]["input_approx"] == 0.10
    assert by_ref["google-vertex:text-multilingual-embedding-002"]["price_per_1m"]["input_approx"] == 0.10
    assert by_ref["google-vertex:multimodalembedding"]["price_per_1m"]["input_approx"] == 0.80
    assert by_ref["google-vertex:multilingual-e5-small"]["skip_reason"]


def test_hierarchy_generator_does_not_read_eval_scoring_source() -> None:
    script = (
        REGISTRY_PATH.parent
        / "skills"
        / "brain-model-eval-role-hierarchy"
        / "scripts"
        / "generate_model_eval_role_hierarchy.py"
    )
    text = script.read_text(encoding="utf-8")

    assert "fine_grained_capabilities" in text
    assert "COARSE_CAPABILITIES" not in text
    assert "src/memory_stack/evals/scoring.py" not in text


def load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def model_refs(registry: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for provider, config in registry["providers"].items():
        for model in config.get("models", []):
            if provider == "embeddings":
                model_provider = model["provider"]
            else:
                model_provider = provider

            refs.add(f"{model_provider}:{model['id']}")
            if alias := model.get("alias"):
                refs.add(f"{model_provider}:{alias}")
    return refs


def skipped_model_refs(registry: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for provider, config in registry["providers"].items():
        for model in config.get("models", []):
            if not model.get("skip_reason"):
                continue
            if provider == "embeddings":
                model_provider = model["provider"]
            else:
                model_provider = provider

            refs.add(f"{model_provider}:{model['id']}")
            if alias := model.get("alias"):
                refs.add(f"{model_provider}:{alias}")
    return refs
