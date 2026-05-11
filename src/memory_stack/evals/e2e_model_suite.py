from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import ingest_source, recall, remember
from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings
from memory_stack.evals.fixtures.golden import ARTICLE_TEXT, LONG_CHAT_SUMMARY, PREFERENCE_TABLE
from memory_stack.evals.model_fixtures import ModelEvalFixture, fixture_prompt
from memory_stack.evals.model_matrix import ModelCandidate, candidate_from_ref
from memory_stack.evals.model_runner import validate_against_schema
from memory_stack.evals.provider_client import LiveProviderClient, ModelCallResult
from memory_stack.evals.scoring import score_model_output
from memory_stack.model_selection import configured_llm


E2E_MODEL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
        "memory_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "citations", "memory_ids"],
    "additionalProperties": False,
}


class E2EModelClient(Protocol):
    def complete_json(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict[str, Any],
    ) -> ModelCallResult:
        """Return a JSON model response for one E2E prompt."""


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
    client: E2EModelClient | None = None,
) -> dict[str, Any]:
    seed = seed_e2e_database(settings)
    candidate = candidate_from_ref(model_ref or configured_llm(settings).ref, roles={"recall_synthesizer"})
    active_client = client or LiveProviderClient(settings)
    started = time.perf_counter()
    records = [
        run_e2e_case(
            case,
            settings=settings,
            seed=seed,
            candidate=candidate,
            client=active_client,
        )
        for case in cases
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
    client: E2EModelClient,
) -> dict[str, Any]:
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
    fixture = ModelEvalFixture(
        id=case.id,
        scenario_group="e2e_runtime_recall",
        role="recall_synthesizer",
        input_text=e2e_model_prompt(case, runtime_response.model_dump(mode="json"), seed),
        expected=case.expected,
        zero_tolerance_checks=case.zero_tolerance_checks,
    )
    model_result = client.complete_json(
        candidate,
        prompt=fixture_prompt(fixture),
        schema=E2E_MODEL_OUTPUT_SCHEMA,
    )
    schema_errors = (
        validate_against_schema(model_result.payload, E2E_MODEL_OUTPUT_SCHEMA, path="$")
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
    recall_quality = scores.get("recall_quality")
    passed = scoring_status == "ok" and recall_quality == 1.0 and not zero_tolerance

    return {
        "fixture_id": case.id,
        "query": case.query,
        "mode": case.mode,
        "status": "pass" if passed else "fail",
        "model_status": model_result.status,
        "schema_errors": schema_errors,
        "scores": scores,
        "zero_tolerance": zero_tolerance,
        "notes": notes,
        "prompt": fixture_prompt(fixture),
        "runtime_response": runtime_response.model_dump(mode="json"),
        "model_response": model_result.payload,
        "raw_model_text": model_result.raw_text,
        "latency_ms": model_result.latency_ms,
        "input_tokens": model_result.input_tokens,
        "output_tokens": model_result.output_tokens,
        "estimated_cost_usd": model_result.estimated_cost_usd,
    }


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
