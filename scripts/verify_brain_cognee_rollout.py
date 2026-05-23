#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack import brain_schema as schema
from memory_stack import brain_service
from memory_stack.bias_context import remember_bias_context
from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import forget, ingest_source, recall, remember, review_recent, undo_last
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings, load_settings
from memory_stack.cognee.legacy_export import (
    export_legacy_brain_to_cognee,
    verify_legacy_export_integrity,
)
from memory_stack.profile_context import remember_profile_context
from memory_stack.taste.cognee_store import CogneePalateStore, InMemoryPalateCogneeAdapter
from memory_stack.taste.models import TasteQueryRequest, TasteRememberRequest
from memory_stack.taste.service import TasteService


SEMANTIC_TABLES = (
    schema.ingestion_runs,
    schema.sources,
    schema.memory_cards,
    schema.entities,
    schema.relationships,
    schema.open_loops,
    schema.cognee_sync,
    schema.recall_logs,
)


class FakeCogneeAdapter:
    def __init__(self) -> None:
        self.remember_calls: list[dict[str, Any]] = []
        self.forget_calls: list[dict[str, Any]] = []

    def remember_text(
        self,
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> dict[str, Any]:
        del settings
        self.remember_calls.append(
            {
                "text": text,
                "dataset_name": dataset_name,
                "node_set": node_set or [],
            }
        )
        return {"items": [{"id": f"00000000-0000-0000-0000-{len(self.remember_calls):012d}"}]}

    def forget_cognee(
        self,
        *,
        data_id: str | None = None,
        dataset: str | None = None,
        everything: bool = False,
        memory_only: bool = False,
        settings: Settings | None = None,
    ) -> dict[str, Any]:
        del settings
        call = {
            "data_id": data_id,
            "dataset": dataset,
            "everything": everything,
            "memory_only": memory_only,
        }
        self.forget_calls.append(call)
        return {"status": "forgotten", **call}


class FakeCogneeSearch:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        query: str,
        *,
        dataset: str,
        top_k: int,
        settings: Settings,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            {
                "query": query,
                "dataset": dataset,
                "top_k": top_k,
                "settings": settings,
            }
        )
        return [
            {
                "datapoint_type": "BrainMemoryDataPoint",
                "external_id": "rollout_mem_recall",
                "kind": "fact",
                "statement": "Rollout verification memory is available from Cognee.",
                "status": "current",
                "confidence": "high",
            }
        ]


class FakeExportVerifier:
    def recall_text(
        self,
        *,
        query: str,
        dataset: str,
        settings: Settings | None = None,
    ) -> list[str]:
        del dataset, settings
        return [f"found {query}"]


def run_rollout_verification(
    settings: Settings,
    *,
    live_cognee: bool = False,
    run_export: bool = True,
    sample_size: int = 3,
) -> dict[str, Any]:
    fake_cognee = FakeCogneeAdapter()
    fake_palate_adapter = InMemoryPalateCogneeAdapter(settings.brain_cognee_palate_dataset)
    report: dict[str, Any] = {
        "mode": "live_cognee" if live_cognee else "fake_cognee",
        "database_url": settings.brain_database_url,
        "steps": {},
        "errors": [],
    }
    try:
        run_schema_migrations(settings)
        report["steps"]["schema_migrations"] = {"status": "ok"}
        if run_export:
            export_adapter = None if live_cognee else fake_cognee
            palate_adapter = None if live_cognee else fake_palate_adapter
            first_export = export_legacy_brain_to_cognee(
                settings=settings,
                adapter=export_adapter,
                palate_adapter=palate_adapter,
                include_source_chunks=True,
            )
            second_export = export_legacy_brain_to_cognee(
                settings=settings,
                adapter=export_adapter,
                palate_adapter=palate_adapter,
                include_source_chunks=True,
            )
            integrity = verify_legacy_export_integrity(
                settings=settings,
                verifier=None if live_cognee else FakeExportVerifier(),
                sample_size=sample_size,
            )
            report["steps"]["legacy_export"] = {
                "first": first_export,
                "second": second_export,
                "idempotent": all(
                    receipt.get("skipped_existing")
                    for receipt in second_export.get("receipts", [])
                )
                if second_export.get("receipts")
                else True,
                "integrity": integrity,
            }

        with _patched_cognee(fake_cognee, enabled=not live_cognee):
            smoke = run_smoke_checks(
                settings,
                cognee_searcher=None if live_cognee else FakeCogneeSearch(settings),
                palate_adapter=None if live_cognee else fake_palate_adapter,
            )
        report["steps"]["smoke"] = smoke
        report["steps"]["fake_cognee_calls"] = {
            "remember": len(fake_cognee.remember_calls),
            "forget": len(fake_cognee.forget_calls),
            "palate_points": len(fake_palate_adapter.points),
        }
    except Exception as exc:
        report["errors"].append(str(exc))

    report["status"] = "failed" if report["errors"] or _step_failed(report["steps"]) else "ok"
    return report


def run_smoke_checks(
    settings: Settings,
    *,
    cognee_searcher: Any = None,
    palate_adapter: InMemoryPalateCogneeAdapter | None = None,
) -> dict[str, Any]:
    before = semantic_table_counts(settings)
    profile = remember_profile_context(
        settings,
        statement="Rollout verifier profile context.",
        scope="rollout",
        source="phase_11_verifier",
    )
    bias = remember_bias_context(
        settings,
        statement="Rollout verifier bias context.",
        scope="rollout",
        source="phase_11_verifier",
    )
    first_memory = remember(
        RememberRequest(
            input="Rollout verifier memory likes Cognee.",
            context={"surface": "phase_11_verifier"},
        ),
        settings,
    )
    source = ingest_source(
        IngestSourceRequest(
            source="# Rollout verifier\nCognee source ingest smoke test.",
            source_kind="markdown",
            title="Rollout verifier source",
            metadata={"phase": "11"},
        ),
        settings,
    )
    recalled = recall(
        RecallRequest(query="rollout verification memory", limit=5),
        settings,
        cognee_searcher=cognee_searcher,
    )
    undone = undo_last(settings)
    second_memory = remember(
        RememberRequest(
            input="Rollout verifier memory for explicit forget.",
            context={"surface": "phase_11_verifier"},
        ),
        settings,
    )
    forgotten = forget(
        settings,
        object_type="memory",
        object_id=second_memory.memory_datapoints[0].id,
        reason="phase 11 rollout verifier",
    )
    review = review_recent(settings)
    taste = run_taste_smoke(settings, palate_adapter=palate_adapter)
    after = semantic_table_counts(settings)
    smoke_ok = (
        before == after
        and undone["status"] == "undone"
        and forgotten["status"] == "deleted"
        and len(recalled.facts) > 0
        and taste["stored"] is True
    )
    return {
        "status": "ok" if smoke_ok else "failed",
        "legacy_semantic_counts_before": before,
        "legacy_semantic_counts_after": after,
        "legacy_semantic_rows_unchanged": before == after,
        "profile_context_id": profile["id"],
        "bias_context_id": bias["id"],
        "remember_receipt": first_memory.ingestion_run_id,
        "source_receipt": source.ingestion_run_id,
        "recall_fact_count": len(recalled.facts),
        "undo_status": undone["status"],
        "forget_status": forgotten["status"],
        "review_external_receipts": len(review.get("external_receipts", [])),
        "taste": taste,
    }


def run_taste_smoke(
    settings: Settings,
    *,
    palate_adapter: InMemoryPalateCogneeAdapter | None,
) -> dict[str, Any]:
    active_settings = settings.model_copy(
        update={
            "brain_taste_enabled": True,
            "brain_taste_canonical_store": "cognee",
            "brain_taste_omdb_api_key": None,
        }
    )
    canonical_store = (
        CogneePalateStore(active_settings, adapter=palate_adapter)
        if palate_adapter is not None
        else None
    )
    service = TasteService(active_settings, canonical_store=canonical_store)
    remembered = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Rollout Verifier Rioja",
            description="Rollout verifier liked an oaky Rioja.",
            rating=8,
            attributes={"oak": 0.7},
            fetch_external_ratings=False,
            store_anyway=True,
            metadata={"phase": "11"},
        )
    )
    queried = service.query(
        TasteQueryRequest(
            query="Which rollout verifier wine should I pick?",
            intent={"intent": "recommend", "entity_type": "wine"},
        )
    )
    return {
        "stored": remembered["stored"],
        "canonical_store": remembered["canonical_store"],
        "record_count": len(remembered["taste_records"]),
        "decision_id": queried["decision_id"],
        "ranked_count": len(queried["ranked_results"]),
    }


@contextmanager
def _patched_cognee(fake_cognee: FakeCogneeAdapter, *, enabled: bool) -> Iterator[None]:
    if not enabled:
        yield
        return
    original_remember = brain_service._cognee_remember_text
    original_forget = brain_service._cognee_forget
    brain_service._cognee_remember_text = fake_cognee.remember_text
    brain_service._cognee_forget = fake_cognee.forget_cognee
    try:
        yield
    finally:
        brain_service._cognee_remember_text = original_remember
        brain_service._cognee_forget = original_forget


def semantic_table_counts(settings: Settings) -> dict[str, int]:
    store = BrainStore(settings)
    with store.engine.begin() as conn:
        return {
            table.name: int(conn.execute(select(func.count()).select_from(table)).scalar_one())
            for table in SEMANTIC_TABLES
        }


def run_schema_migrations(settings: Settings) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.brain_database_url)
    command.upgrade(config, "head")


def _step_failed(steps: dict[str, Any]) -> bool:
    for step in steps.values():
        if isinstance(step, dict) and step.get("status") == "failed":
            return True
        if isinstance(step, dict) and step.get("integrity", {}).get("status") == "failed":
            return True
    return False


def copy_sqlite_database(settings: Settings, destination: Path) -> Settings:
    source = sqlite_path(settings.brain_database_url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copy2(source, destination)
    return settings.model_copy(update={"brain_database_url": f"sqlite:///{destination}"})


def sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise SystemExit(f"Only SQLite Brain DB copy verification is supported, got: {database_url}")
    return Path(database_url.removeprefix(prefix)).expanduser()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Brain/Cognee Phase 11 rollout smoke checks.")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--env", choices=["dev", "qa", "staging", "prod"], default="dev")
    parser.add_argument("--db-copy", default=None, help="Run against a copied SQLite DB at this path.")
    parser.add_argument("--live-cognee", action="store_true", help="Use real Cognee instead of fake adapters.")
    parser.add_argument("--skip-export", action="store_true", help="Skip legacy export and integrity checks.")
    parser.add_argument("--sample-size", type=int, default=3)
    args = parser.parse_args()

    settings = load_settings(args.env_file, config_env=args.env)
    if args.db_copy:
        settings = copy_sqlite_database(settings, Path(args.db_copy).expanduser())
    report = run_rollout_verification(
        settings,
        live_cognee=args.live_cognee,
        run_export=not args.skip_export,
        sample_size=args.sample_size,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
