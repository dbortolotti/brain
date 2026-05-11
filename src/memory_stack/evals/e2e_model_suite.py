from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import ingest_source, recall, remember
from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings
from memory_stack.evals.fixtures.golden import ARTICLE_TEXT, LONG_CHAT_SUMMARY, PREFERENCE_TABLE
from memory_stack.evals.model_fixtures import ModelEvalFixture, fixture_prompt, output_schema_for_fixture
from memory_stack.evals.model_matrix import ModelCandidate, candidate_from_ref
from memory_stack.evals.model_runner import validate_against_schema
from memory_stack.evals.provider_client import LiveProviderClient
from memory_stack.evals.scoring import ROLE_SCORE_WEIGHTS, score_model_output
from memory_stack.model_selection import configured_llm


@dataclass(frozen=True)
class E2ERecallCase:
    id: str
    query: str
    expected: dict[str, Any]
    mode: str = "auto"
    include_sources: bool = True
    include_superseded: bool = False
    include_conflicts: bool = True
    limit: int = 20
    zero_tolerance_checks: tuple[str, ...] = ()


@dataclass(frozen=True)
class E2EDatabaseSeed:
    memory_ids: dict[str, str] = field(default_factory=dict)
    source_ids: dict[str, str] = field(default_factory=dict)
    open_loop_ids: dict[str, str] = field(default_factory=dict)


E2E_RECALL_CASES: tuple[E2ERecallCase, ...] = (
    E2ERecallCase(
        id="e2e_recall_daughters",
        query="Who are my daughters?",
        expected={
            "must_include": ["Nur", "Sara"],
            "must_not_include": ["sons"],
            "citations_required": True,
        },
        zero_tolerance_checks=("relationship_direction_inversion",),
    ),
    E2ERecallCase(
        id="e2e_recall_current_work",
        query="Where does Sam work now?",
        expected={
            "must_include": ["Point72"],
            "must_not_include": ["works at Goldman"],
            "citations_required": True,
        },
        zero_tolerance_checks=("deleted_or_superseded_memory_returned_as_current",),
    ),
    E2ERecallCase(
        id="e2e_recall_music_deleted_filter",
        query="What music does Sam like?",
        expected={
            "must_include": ["Bill Evans"],
            "must_not_include": ["Taylor Swift"],
            "citations_required": True,
        },
        zero_tolerance_checks=("deleted_memory_returned",),
    ),
    E2ERecallCase(
        id="e2e_recall_open_loop_filter",
        query="What open ideas do I have about knowledge graphs?",
        mode="open_loops",
        expected={
            "must_include": ["knowledge graphs", "open"],
            "must_not_include": ["Python"],
            "citations_required": True,
        },
        zero_tolerance_checks=("irrelevant_memory_dump",),
    ),
    E2ERecallCase(
        id="e2e_recall_brain_cognee_conclusions",
        query="What did I conclude about Brain and Cognee?",
        expected={
            "must_include": ["Brain DB", "source of truth", "Cognee", "rebuildable"],
            "must_not_include": ["daughters", "Bill Evans"],
            "citations_required": True,
        },
        zero_tolerance_checks=("irrelevant_memory_dump",),
    ),
    E2ERecallCase(
        id="e2e_recall_ai_memory_articles",
        query="What articles have I saved about AI memory?",
        expected={
            "must_include": ["AI memory", "article", "source evidence"],
            "must_not_include": ["daughters", "Bill Evans", "small table"],
            "citations_required": True,
        },
        zero_tolerance_checks=("irrelevant_memory_dump",),
    ),
)


EXPECTED_E2E_ROLES: tuple[str, ...] = (
    "atomic_card_extractor",
    "commit_policy_decider",
    "conflict_candidate_detector",
    "conflict_explainer",
    "conflict_policy_decider",
    "debug_explainer",
    "durability_filter",
    "entity_candidate_ranker",
    "entity_final_resolver",
    "entity_mention_extractor",
    "eval_judge",
    "groundedness_checker",
    "intent_router",
    "memory_kind_classifier",
    "open_loop_detector",
    "recall_planner",
    "recall_relevance_filter",
    "recall_synthesizer",
    "relationship_extractor",
    "repair_option_generator",
    "source_classifier",
    "source_takeaway_extractor",
    "success_receipt_generator",
    "table_policy_handler",
)


def settings_for_e2e_database(database_path: Path) -> Settings:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return Settings(brain_database_url=f"sqlite:///{database_path}")


def seed_e2e_database(settings: Settings) -> E2EDatabaseSeed:
    """Populate a real Brain SQLite database through service-layer writes."""

    memory_ids: dict[str, str] = {}
    source_ids: dict[str, str] = {}
    open_loop_ids: dict[str, str] = {}

    memory_ids["daughters"] = remember(
        RememberRequest(input="Nur and Sara are my twin daughters."),
        settings,
    ).memory_cards[0].id
    memory_ids["sam_jazz"] = remember(
        RememberRequest(input="Sam from Goldman mentioned that he likes Bill Evans."),
        settings,
    ).memory_cards[0].id

    knowledge_graphs = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )
    memory_ids["knowledge_graphs_open_loop"] = knowledge_graphs.memory_cards[0].id
    open_loop_ids["knowledge_graphs"] = knowledge_graphs.open_loops[0]["id"]

    python_loop = remember(
        RememberRequest(input="I want to learn more about basic Python."),
        settings,
    )
    memory_ids["python_closed_loop"] = python_loop.memory_cards[0].id
    open_loop_ids["python"] = python_loop.open_loops[0]["id"]

    old_work = remember(RememberRequest(input="Sam works at Goldman."), settings)
    current_work = remember(
        RememberRequest(input="Sam left Goldman and joined Point72."),
        settings,
    )
    memory_ids["sam_work_old"] = old_work.memory_cards[0].id
    memory_ids["sam_work_current"] = current_work.memory_cards[0].id

    deleted_music = remember(RememberRequest(input="Sam likes Taylor Swift."), settings)
    memory_ids["sam_music_deleted"] = deleted_music.memory_cards[0].id

    source = ingest_source(
        IngestSourceRequest(
            source=LONG_CHAT_SUMMARY,
            source_kind="markdown",
            title="Brain/Cognee design chat",
        ),
        settings,
    )
    source_ids["brain_cognee"] = str(source.source.source_id)
    memory_ids["brain_cognee"] = source.memory_cards[0].id

    article = ingest_source(
        IngestSourceRequest(
            source=ARTICLE_TEXT,
            source_kind="article",
            title="AI memory design",
            why_saved="Useful for AI memory design.",
        ),
        settings,
    )
    source_ids["ai_memory_article"] = str(article.source.source_id)
    memory_ids["ai_memory_article"] = article.memory_cards[0].id

    table = ingest_source(
        IngestSourceRequest(
            source=PREFERENCE_TABLE,
            source_kind="table",
            title="Preference distractor table",
        ),
        settings,
    )
    source_ids["preference_table"] = str(table.source.source_id)
    memory_ids["preference_table"] = table.memory_cards[0].id

    store = BrainStore(settings)
    store.update_memory_status(memory_ids["sam_work_old"], "superseded")
    store.update_memory_status(memory_ids["sam_music_deleted"], "deleted")
    store.update_open_loop_status(open_loop_ids["python"], "closed")

    return E2EDatabaseSeed(
        memory_ids=memory_ids,
        source_ids=source_ids,
        open_loop_ids=open_loop_ids,
    )


def run_e2e_model_suite(
    settings: Settings,
    *,
    model_ref: str | None = None,
    cases: tuple[E2ERecallCase, ...] = E2E_RECALL_CASES,
    retry_attempts: int = 2,
    retry_backoff_seconds: float = 1.0,
) -> dict[str, Any]:
    seed = seed_e2e_database(settings)
    fixtures = build_e2e_model_fixtures(settings, seed, recall_cases=cases)
    candidate = candidate_from_ref(
        model_ref or configured_llm(settings).ref,
        roles={fixture.role for fixture in fixtures},
    )
    active_client = LiveProviderClient(
        settings,
        retry_attempts=retry_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )
    started = time.perf_counter()
    records = [
        run_e2e_fixture(
            fixture,
            candidate=candidate,
            client=active_client,
        )
        for fixture in fixtures
    ]
    return {
        "model": candidate.ref,
        "record_count": len(records),
        "pass_count": sum(1 for record in records if record["status"] == "pass"),
        "fail_count": sum(1 for record in records if record["status"] != "pass"),
        "latency_seconds": round(time.perf_counter() - started, 3),
        "seed": {
            "memory_ids": seed.memory_ids,
            "source_ids": seed.source_ids,
            "open_loop_ids": seed.open_loop_ids,
        },
        "records": records,
    }


def run_e2e_case(
    case: E2ERecallCase,
    *,
    settings: Settings,
    seed: E2EDatabaseSeed,
    candidate: ModelCandidate,
    client: LiveProviderClient,
) -> dict[str, Any]:
    fixture = build_recall_e2e_fixture(case, settings=settings, seed=seed)
    return run_e2e_fixture(fixture, candidate=candidate, client=client)


def run_e2e_fixture(
    fixture: ModelEvalFixture,
    *,
    candidate: ModelCandidate,
    client: LiveProviderClient,
) -> dict[str, Any]:
    schema = output_schema_for_fixture(fixture)
    model_result = client.complete_json(
        candidate,
        prompt=fixture_prompt(fixture),
        schema=schema,
    )
    schema_errors = (
        validate_against_schema(model_result.payload, schema, path="$")
        if model_result.payload is not None
        else []
    )
    scoring_status = model_result.status
    notes: list[str] = []
    if model_result.status == "ok" and schema_errors:
        scoring_status = "schema_fail"
        notes.extend(schema_errors)

    scores, zero_tolerance, scoring_notes = score_model_output(
        fixture,
        model_result.payload,
        status=scoring_status,
    )
    notes.extend(scoring_notes)
    required_score_keys = tuple(ROLE_SCORE_WEIGHTS.get(fixture.role, scores).keys())
    scored_values = [
        value
        for key in required_score_keys
        if (value := scores.get(key)) is not None
    ]
    passed = (
        scoring_status == "ok"
        and not zero_tolerance
        and bool(scored_values)
        and all(value >= 1.0 for value in scored_values)
    )

    return {
        "fixture_id": fixture.id,
        "role": fixture.role,
        "status": "pass" if passed else "fail",
        "model_status": model_result.status,
        "schema_errors": schema_errors,
        "scores": scores,
        "required_score_keys": required_score_keys,
        "zero_tolerance": zero_tolerance,
        "notes": notes,
        "prompt": fixture_prompt(fixture),
        "model_response": model_result.payload,
        "raw_model_text": model_result.raw_text,
        "latency_ms": model_result.latency_ms,
        "input_tokens": model_result.input_tokens,
        "output_tokens": model_result.output_tokens,
        "estimated_cost_usd": model_result.estimated_cost_usd,
    }


def build_e2e_model_fixtures(
    settings: Settings,
    seed: E2EDatabaseSeed,
    *,
    recall_cases: tuple[E2ERecallCase, ...] = E2E_RECALL_CASES,
) -> tuple[ModelEvalFixture, ...]:
    return (
        *build_role_e2e_fixtures(seed),
        *(
            build_recall_e2e_fixture(case, settings=settings, seed=seed)
            for case in recall_cases
        ),
    )


def build_recall_e2e_fixture(
    case: E2ERecallCase,
    *,
    settings: Settings,
    seed: E2EDatabaseSeed,
) -> ModelEvalFixture:
    runtime_response = recall(
        RecallRequest(
            query=case.query,
            mode=case.mode,
            include_sources=case.include_sources,
            include_superseded=case.include_superseded,
            include_conflicts=case.include_conflicts,
            limit=case.limit,
        ),
        settings,
    )
    return ModelEvalFixture(
        id=case.id,
        scenario_group="e2e_runtime_recall",
        role="recall_synthesizer",
        input_text=e2e_model_prompt(case, runtime_response.model_dump(mode="json"), seed),
        expected=case.expected,
        zero_tolerance_checks=case.zero_tolerance_checks,
    )


def build_role_e2e_fixtures(seed: E2EDatabaseSeed) -> tuple[ModelEvalFixture, ...]:
    ids = seed.memory_ids
    sources = seed.source_ids
    seeded_context = json.dumps(
        {
            "memory_ids": ids,
            "source_ids": sources,
            "open_loop_ids": seed.open_loop_ids,
            "statuses": {
                ids["sam_work_old"]: "superseded",
                ids["sam_work_current"]: "current",
                ids["sam_music_deleted"]: "deleted",
                ids["python_closed_loop"]: "current memory with closed open-loop row",
            },
        },
        indent=2,
        sort_keys=True,
    )

    def fixture(
        fixture_id: str,
        role: str,
        input_text: str,
        expected: dict[str, Any],
        *,
        zero_tolerance_checks: tuple[str, ...] = (),
    ) -> ModelEvalFixture:
        return ModelEvalFixture(
            id=fixture_id,
            scenario_group="e2e_role_matrix",
            role=role,
            input_text=f"Seeded Brain runtime state:\n{seeded_context}\n\nTask:\n{input_text}",
            expected=expected,
            zero_tolerance_checks=zero_tolerance_checks,
        )

    return (
        fixture(
            "e2e_intent_router_recall_vs_write",
            "intent_router",
            "/brain recall what do I know about Sam from Goldman?",
            {"intent": "recall", "must_include": ["Sam"]},
        ),
        fixture(
            "e2e_source_classifier_long_markdown",
            "source_classifier",
            "Classify this saved note as memory/source/junk: "
            f"title=Brain/Cognee design chat source_id={sources['brain_cognee']} text={LONG_CHAT_SUMMARY}",
            {
                "input_class": "source",
                "source_kind": "markdown",
                "should_create_source": True,
                "should_extract_memories": True,
                "must_include": ["Brain", "Cognee"],
            },
        ),
        fixture(
            "e2e_durability_filter_secret_and_weather",
            "durability_filter",
            "Should Brain store this? 'Today's weather is cloudy and api_key=sk-testtoken123456789.'",
            {
                "expected_durable": False,
                "decision_any": ["do_not_store"],
                "must_include_any": ["not durable", "secret", "token", "weather"],
            },
            zero_tolerance_checks=("no_durable_value_junk_committed",),
        ),
        fixture(
            "e2e_memory_kind_family_and_open_loop",
            "memory_kind_classifier",
            "Classify: 'Nur and Sara are my twin daughters. I want to learn more about knowledge graphs.'",
            {"memory_kinds": ["family_fact", "open_loop"], "must_include": ["family", "open"]},
        ),
        fixture(
            "e2e_open_loop_detector_closed_vs_open",
            "open_loop_detector",
            "Open loop rows include knowledge_graphs=open and Python=closed. Detect only open loops for knowledge graphs.",
            {
                "expected_open_loop": True,
                "must_include": ["knowledge graphs"],
                "must_not_include": ["Python"],
            },
        ),
        fixture(
            "e2e_entity_mentions_ambiguous_sams",
            "entity_mention_extractor",
            "Extract entities without merging them: Sam from Goldman likes Bill Evans; Sam from Point72 joined later.",
            {
                "entity_terms": ["Sam", "Goldman", "Bill Evans", "Point72"],
            },
            zero_tolerance_checks=("entity_overmerge",),
        ),
        fixture(
            "e2e_entity_candidate_ranker_preserve_ambiguous_sam",
            "entity_candidate_ranker",
            "Existing candidates: ent_goldman=Sam from Goldman, ent_point72=Sam from Point72. New mention: Sam likes jazz. Pick action.",
            {
                "entity_action": "needs_clarification",
                "must_include": ["Sam"],
            },
            zero_tolerance_checks=("entity_overmerge",),
        ),
        fixture(
            "e2e_entity_final_resolver_alias_match",
            "entity_final_resolver",
            "Mention 'Sam from Goldman' appears with candidate ent_goldman=Sam from Goldman and candidate ent_point72=Sam from Point72. Resolve final entity.",
            {
                "entity_action": "use_existing",
                "must_include": ["Sam from Goldman", "ent_goldman"],
            },
        ),
        fixture(
            "e2e_relationship_extractor_family_direction",
            "relationship_extractor",
            "Extract relationships from: Nur and Sara are Daniele's twin daughters.",
            {"relationships": ["daughter_of", "twin_of"], "must_include": ["Daniele"]},
            zero_tolerance_checks=("relationship_direction_inversion",),
        ),
        fixture(
            "e2e_atomic_card_extractor_compound_input",
            "atomic_card_extractor",
            "Create atomic memory cards for: Sam left Goldman and joined Point72; Sam likes Bill Evans; Nur and Sara are Daniele's twin daughters.",
            {
                "memory_kinds_any": ["person_fact", "person_interaction", "family_fact"],
                "must_include": ["Point72", "Bill Evans", "Nur", "Sara"],
                "relationships": ["daughter_of"],
            },
        ),
        fixture(
            "e2e_table_policy_handler_large_table",
            "table_policy_handler",
            "A CSV table has 500 rows of expenses. Decide whether to atomize every row into memories or keep it as source/table summary.",
            {
                "must_include_any": ["table", "source", "summary"],
                "must_not_include": ["500 memory cards"],
            },
            zero_tolerance_checks=("large_table_atomized_by_default",),
        ),
        fixture(
            "e2e_source_takeaway_extractor_article",
            "source_takeaway_extractor",
            f"Extract durable source takeaways from source_id={sources['ai_memory_article']}: {ARTICLE_TEXT}",
            {
                "memory_kinds_any": ["article_note", "source_summary", "key_takeaway"],
                "must_include": ["AI memory", "source evidence"],
                "source_memory_split": True,
            },
        ),
        fixture(
            "e2e_conflict_candidate_detector_transition",
            "conflict_candidate_detector",
            f"Existing current memory {ids['sam_work_old']}: Sam works at Goldman. New memory {ids['sam_work_current']}: Sam left Goldman and joined Point72. Detection only.",
            {
                "decision_any": ["possible_conflict", "conflict_candidate", "needs_policy"],
                "conflict_classification": "supersedes",
                "detection_only": True,
                "must_include": ["Goldman", "Point72"],
            },
        ),
        fixture(
            "e2e_conflict_policy_decider_duplicate",
            "conflict_policy_decider",
            "Existing current memory: Sam likes Bill Evans. New memory: Sam from Goldman likes Bill Evans. Choose safe backend policy action.",
            {
                "policy_action_any": ["mark_duplicate"],
                "requires_user_choice": False,
                "must_include": ["duplicate", "Bill Evans"],
            },
        ),
        fixture(
            "e2e_conflict_explainer_currentness",
            "conflict_explainer",
            "Explain why Sam works at Goldman was filtered after Sam left Goldman and joined Point72.",
            {
                "must_include": ["Goldman", "Point72", "superseded"],
                "must_not_include": ["deleted"],
            },
        ),
        fixture(
            "e2e_repair_option_generator_ambiguous_sam",
            "repair_option_generator",
            "User wrote: remember Sam likes jazz. Existing entities include Sam from Goldman and Sam from Point72. Generate safe repair options.",
            {
                "safe_action_space": ["Ask which Sam", "Use Sam from Goldman", "Use Sam from Point72", "Cancel"],
                "repair_terms": ["Sam", "Goldman", "Point72", "Cancel"],
            },
            zero_tolerance_checks=("auto_commit_when_user_choice_required",),
        ),
        fixture(
            "e2e_commit_policy_decider_unresolved_pronoun",
            "commit_policy_decider",
            "User wrote: remember He likes Bill Evans. No unambiguous subject is available. Decide commit policy.",
            {
                "decision_any": ["ask", "needs_clarification"],
                "requires_confirmation": True,
                "must_include_any": ["subject", "who", "clarify"],
            },
            zero_tolerance_checks=("unresolved_pronoun_committed",),
        ),
        fixture(
            "e2e_success_receipt_generator_source_and_memory",
            "success_receipt_generator",
            f"Generate receipt for stored memory_id={ids['brain_cognee']} source_id={sources['brain_cognee']} confidence=medium kind=source_summary.",
            {
                "receipt_terms": ["Stored", "memory_id", ids["brain_cognee"], "source", sources["brain_cognee"], "confidence"],
            },
            zero_tolerance_checks=("success_receipt_missing",),
        ),
        fixture(
            "e2e_recall_planner_write_not_applicable",
            "recall_planner",
            "Plan recall for this input: /brain remember Sam from Goldman likes Bill Evans.",
            {
                "not_applicable": True,
                "must_include_any": ["not", "write", "remember"],
            },
        ),
        fixture(
            "e2e_recall_relevance_filter_status_and_topic",
            "recall_relevance_filter",
            "Query: Where does Sam work now? Candidate memories include current Point72, superseded Goldman, deleted Taylor Swift, daughters, AI article.",
            {
                "memory_ids": [ids["sam_work_current"]],
                "excluded_memory_ids": [
                    ids["sam_work_old"],
                    ids["sam_music_deleted"],
                    ids["daughters"],
                    ids["ai_memory_article"],
                ],
                "must_include": ["Point72"],
                "must_not_include": ["Taylor Swift", "daughters"],
            },
            zero_tolerance_checks=("deleted_memory_returned", "deleted_or_superseded_memory_returned_as_current"),
        ),
        fixture(
            "e2e_groundedness_checker_unsupported_claim",
            "groundedness_checker",
            "Runtime evidence says Sam likes Bill Evans. Candidate answer says Sam likes Bill Evans and Taylor Swift. Identify unsupported content.",
            {
                "must_include": ["Taylor Swift", "unsupported"],
                "must_not_include": ["fully grounded"],
            },
        ),
        fixture(
            "e2e_debug_explainer_recall_filtering",
            "debug_explainer",
            "Explain why recall for 'Where does Sam work now?' included Point72 and filtered superseded Goldman plus deleted Taylor Swift.",
            {
                "must_include": ["Point72", "superseded", "deleted", "Taylor Swift"],
            },
        ),
        fixture(
            "e2e_eval_judge_quality_gate",
            "eval_judge",
            "Judge answer: 'Sam works at Goldman and Point72.' Expected: current answer should say Point72 only and not present Goldman as current.",
            {
                "must_include": ["Goldman", "Point72"],
                "must_include_any": ["fail", "incorrect", "not_grounded", "unsupported"],
                "must_not_include": ["pass"],
            },
        ),
    )


def e2e_model_prompt(
    case: E2ERecallCase,
    runtime_response: dict[str, Any],
    seed: E2EDatabaseSeed,
) -> str:
    prompt_payload = {
        "fixture_id": case.id,
        "query": case.query,
        "mode": case.mode,
        "runtime_facts": runtime_response.get("facts", []),
        "runtime_evidence": runtime_response.get("evidence", []),
        "runtime_open_loops": runtime_response.get("open_loops", []),
        "seed_memory_ids": seed.memory_ids,
        "seed_source_ids": seed.source_ids,
    }
    return "\n".join(
        [
            "You are Brain's production recall synthesizer in a full end-to-end test.",
            "The SQLite Brain database has been populated through the app service layer.",
            "Answer only from runtime_facts, runtime_evidence, and runtime_open_loops.",
            "Filter irrelevant facts. Never present deleted or superseded memories as current.",
            "Return JSON with answer, citations, and memory_ids only.",
            "Use memory IDs in citations whenever possible.",
            "Runtime payload:",
            json.dumps(prompt_payload, indent=2, sort_keys=True),
        ]
    )
