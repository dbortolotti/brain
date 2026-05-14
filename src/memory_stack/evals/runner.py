from __future__ import annotations

import time
from typing import Any

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import ingest_source, recall, remember
from memory_stack.cfg import Settings
from memory_stack.evals.fixtures import GOLDEN_INGESTION_FIXTURES, GoldenFixture
from memory_stack.evals.golden_queries import GOLDEN_RECALL_QUERIES, GoldenRecallQuery
from memory_stack.evals.metrics import groundedness, summarize_metrics, term_recall


def run_golden_evals(
    settings: Settings,
    *,
    fixtures: list[GoldenFixture] | None = None,
    queries: list[GoldenRecallQuery] | None = None,
    llm_client: Any = None,
    cognee_searcher: Any = None,
) -> dict[str, Any]:
    active_fixtures = fixtures or GOLDEN_INGESTION_FIXTURES
    active_queries = queries or GOLDEN_RECALL_QUERIES
    start = time.perf_counter()
    ingestion_results = [
        _ingest_fixture(fixture, settings=settings, llm_client=llm_client)
        for fixture in active_fixtures
    ]
    recall_results = [
        _run_query(query, settings=settings, cognee_searcher=cognee_searcher)
        for query in active_queries
    ]
    latency = time.perf_counter() - start
    return {
        "ingestion_results": ingestion_results,
        "recall_results": recall_results,
        "metrics": summarize_metrics(
            ingestion_results=ingestion_results,
            recall_results=recall_results,
            latency_seconds=latency,
        ),
    }


def _ingest_fixture(
    fixture: GoldenFixture,
    *,
    settings: Settings,
    llm_client: Any,
) -> dict[str, Any]:
    if fixture.source_kind is not None:
        receipt = ingest_source(
            IngestSourceRequest(
                source=fixture.input,
                source_kind=fixture.source_kind,
                title=fixture.title,
                why_saved=fixture.why_saved,
            ),
            settings,
            llm_client=llm_client,
        )
    else:
        receipt = remember(
            RememberRequest(input=fixture.input, input_type=fixture.input_type),
            settings,
            llm_client=llm_client,
        )
    payload = receipt.model_dump(mode="json")
    statements = " ".join(card["statement"] for card in payload.get("memory_cards", []))
    payload["fixture_id"] = fixture.id
    payload["expected_kind_hit"] = bool(
        fixture.expected_kinds
        and fixture.expected_kinds
        & {card["kind"] for card in payload.get("memory_cards", [])}
    )
    payload["term_recall"] = term_recall(statements, fixture.expected_terms)
    return payload


def _run_query(
    query: GoldenRecallQuery,
    *,
    settings: Settings,
    cognee_searcher: Any,
) -> dict[str, Any]:
    response = recall(
        RecallRequest(query=query.query, mode=query.mode),
        settings,
        cognee_searcher=cognee_searcher,
    )
    payload = response.model_dump(mode="json")
    payload["query_id"] = query.id
    payload["term_recall"] = term_recall(response.answer, query.expected_terms)
    payload.update(groundedness(payload))
    return payload
