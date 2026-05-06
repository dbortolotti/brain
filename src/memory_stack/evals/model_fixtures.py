from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelEvalFixture:
    id: str
    scenario_group: str
    role: str
    input_text: str
    expected: dict[str, Any]
    fixture_set: str = "production"
    zero_tolerance_checks: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)


BASE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "decision": {"type": "string"},
        "memory_cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "statement": {"type": "string"},
                    "confidence": {"type": "string"},
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "role": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "subject": {"type": "string"},
                                "predicate": {"type": "string"},
                                "object": {"type": "string"},
                            },
                            "required": ["subject", "predicate", "object"],
                        },
                    },
                },
                "required": ["kind", "statement"],
            },
        },
        "entity_resolution": {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "entity_id": {"type": ["string", "null"]},
                "reason": {"type": "string"},
            },
        },
        "conflict_classification": {"type": "string"},
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
        "repair_options": {"type": "array", "items": {"type": "string"}},
        "receipt": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "details": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    "additionalProperties": True,
}


MODEL_EVAL_FIXTURES: list[ModelEvalFixture] = [
    ModelEvalFixture(
        id="router_remember_plain",
        scenario_group="router_remember",
        role="router",
        fixture_set="smoke",
        input_text="remember Sam from Goldman likes Bill Evans",
        expected={"intent": "remember", "must_include": ["Sam", "Bill Evans"]},
    ),
    ModelEvalFixture(
        id="router_recall_question",
        scenario_group="router_recall",
        role="router",
        fixture_set="smoke",
        input_text="what do I know about Sam from Goldman?",
        expected={"intent": "recall", "must_include": ["Sam"]},
    ),
    ModelEvalFixture(
        id="slack_intake_family_twins",
        scenario_group="family_fact_twins",
        role="slack_intake",
        fixture_set="smoke",
        input_text="Nur and Sara are my twin daughters.",
        expected={
            "decision": "commit_success",
            "memory_kinds": ["family_fact"],
            "must_include": ["Nur", "Sara", "twin", "daughter"],
            "relationships": ["daughter_of", "twin_of"],
            "receipt_terms": ["family_fact", "Nur", "Sara", "confidence"],
        },
        zero_tolerance_checks=("must_not_split_twins_into_duplicate_cards",),
    ),
    ModelEvalFixture(
        id="memory_compiler_article_atomic",
        scenario_group="long_source_split",
        role="memory_compiler",
        fixture_set="development",
        input_text=(
            "AI memory systems need durable source evidence. Atomic memory cards should be "
            "small and traceable. A semantic index can improve recall, but the application "
            "database must own lifecycle and conflict state."
        ),
        expected={
            "decision": "commit_success",
            "memory_kinds": ["article_note", "source_summary"],
            "must_include": ["source evidence", "atomic", "lifecycle"],
            "must_not_include": ["one giant memory"],
            "source_memory_split": True,
        },
        zero_tolerance_checks=("long_source_as_single_memory_card",),
    ),
    ModelEvalFixture(
        id="memory_compiler_small_table",
        scenario_group="small_table_policy",
        role="memory_compiler",
        fixture_set="development",
        input_text=(
            "| Person | Preference |\n"
            "| --- | --- |\n"
            "| Sam | Bill Evans |\n"
            "| Daniele | Knowledge graphs |"
        ),
        expected={
            "decision": "commit_success",
            "memory_kinds": ["table_note"],
            "must_include": ["Bill Evans", "Knowledge graphs"],
            "source_memory_split": True,
        },
        zero_tolerance_checks=("small_table_must_not_drop_values",),
    ),
    ModelEvalFixture(
        id="entity_ambiguous_sam_two_people",
        scenario_group="ambiguous_sam",
        role="entity_resolution",
        fixture_set="development",
        input_text=(
            "Existing entities: Sam from Goldman (person), Sam from Point72 (person). "
            "New message: Sam likes early Coltrane."
        ),
        expected={
            "decision": "needs_clarification",
            "entity_action": "needs_clarification",
            "must_include": ["Sam", "Goldman", "Point72"],
        },
        zero_tolerance_checks=("entity_overmerge",),
    ),
    ModelEvalFixture(
        id="entity_alias_sam_goldman",
        scenario_group="entity_alias",
        role="entity_resolution",
        fixture_set="production",
        input_text=(
            "Existing entity: Sam from Goldman, aliases Sam G, Goldman Sam. "
            "New message: Sam G likes Bill Evans."
        ),
        expected={
            "entity_action": "use_existing",
            "must_include": ["Sam from Goldman", "Bill Evans"],
        },
    ),
    ModelEvalFixture(
        id="conflict_employment_transition",
        scenario_group="employment_transition",
        role="conflict_classifier",
        fixture_set="development",
        input_text=(
            "Existing current fact: Sam works at Goldman. "
            "New fact: Sam left Goldman and joined Point72."
        ),
        expected={
            "conflict_classification": "supersedes",
            "must_include": ["left Goldman", "Point72"],
            "must_not_include": ["duplicate"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    ),
    ModelEvalFixture(
        id="conflict_correction_like",
        scenario_group="correction_like",
        role="conflict_classifier",
        fixture_set="production",
        input_text=(
            "Existing current fact: Sam from Goldman likes Bill Evans. "
            "Correction: Sam from Goldman actually likes early Coltrane, not Bill Evans."
        ),
        expected={
            "conflict_classification": "correction",
            "must_include": ["early Coltrane", "Bill Evans"],
        },
        zero_tolerance_checks=("silent_high_confidence_overwrite",),
    ),
    ModelEvalFixture(
        id="recall_hide_superseded",
        scenario_group="recall_currentness",
        role="recall_synthesizer",
        fixture_set="development",
        input_text=(
            "Current facts: Sam left Goldman and joined Point72 [mem_new]. "
            "Superseded facts: Sam works at Goldman [mem_old]. "
            "Question: Where does Sam work now?"
        ),
        expected={
            "must_include": ["Point72"],
            "must_not_include": ["works at Goldman"],
            "citations_required": True,
        },
        zero_tolerance_checks=("deleted_or_superseded_memory_returned_as_current",),
    ),
    ModelEvalFixture(
        id="recall_absence_scoped",
        scenario_group="absence_claims",
        role="recall_synthesizer",
        fixture_set="production",
        input_text=(
            "Retrieved facts contain no current travel preferences for Sara. "
            "Question: Does Sara prefer morning flights?"
        ),
        expected={
            "must_include": ["no current", "not enough", "do not know"],
            "must_not_include": ["prefers morning flights"],
            "citations_required": False,
        },
        zero_tolerance_checks=("unsupported_absence_claim",),
    ),
    ModelEvalFixture(
        id="validator_reject_junk",
        scenario_group="junk_memory",
        role="validator_critic",
        fixture_set="production",
        input_text="lol ok sure whatever",
        expected={
            "decision": "hard_reject",
            "repair_terms": ["durable", "specific"],
        },
        zero_tolerance_checks=("no_durable_value_junk_committed",),
    ),
    ModelEvalFixture(
        id="debug_explain_recall_sam",
        scenario_group="debug_recall",
        role="debug_explainer",
        fixture_set="production",
        input_text=(
            "Explain why recall returned mem_new for Sam from Goldman and filtered "
            "mem_old because it is superseded."
        ),
        expected={
            "must_include": ["mem_new", "mem_old", "superseded"],
            "must_not_include": ["secret", "raw email"],
        },
    ),
]


FIXTURE_SET_ORDER = {
    "smoke": 0,
    "development": 1,
    "production": 2,
}


def select_fixtures(*, fixture_set: str, roles: set[str]) -> list[ModelEvalFixture]:
    if fixture_set not in FIXTURE_SET_ORDER:
        raise ValueError(f"unsupported fixture set: {fixture_set}")
    max_level = FIXTURE_SET_ORDER[fixture_set]
    fixtures = [
        fixture
        for fixture in MODEL_EVAL_FIXTURES
        if FIXTURE_SET_ORDER[fixture.fixture_set] <= max_level
    ]
    if roles:
        fixtures = [fixture for fixture in fixtures if fixture.role in roles]
    return fixtures


def fixture_prompt(fixture: ModelEvalFixture) -> str:
    return "\n".join(
        [
            "You are evaluating Brain, a personal memory system.",
            "Return only JSON matching the requested schema.",
            "Be strict on committing durable memory, preserve ambiguity, and never "
            "present superseded/deleted facts as current.",
            f"Role: {fixture.role}",
            f"Fixture ID: {fixture.id}",
            "Input:",
            fixture.input_text,
        ]
    )

