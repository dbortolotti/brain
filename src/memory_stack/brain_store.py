from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, and_, create_engine, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from memory_stack import brain_schema as schema
from memory_stack.config import Settings, repo_path


WORD_RE = re.compile(r"[a-z0-9]+")


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_name(value: str) -> str:
    return " ".join(WORD_RE.findall(value.casefold()))


def content_hash(*values: Any) -> str:
    payload = json.dumps(values, ensure_ascii=True, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *values: Any) -> str:
    digest = content_hash(*values).split(":", 1)[1][:16]
    return f"{prefix}_{digest}"


def brain_database_url(settings: Settings) -> str:
    url = settings.brain_database_url
    if not url.startswith("sqlite:///") or url == "sqlite:///:memory:":
        return url

    raw_path = url.removeprefix("sqlite:///")
    if raw_path.startswith("/"):
        return url

    path = repo_path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def create_brain_engine(settings: Settings) -> Engine:
    connect_args = {"check_same_thread": False} if settings.brain_database_url.startswith("sqlite") else {}
    return create_engine(brain_database_url(settings), future=True, connect_args=connect_args)


def init_brain_db(settings: Settings) -> None:
    engine = create_brain_engine(settings)
    schema.metadata.create_all(engine)


def row_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


class BrainStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine = create_brain_engine(settings)
        schema.metadata.create_all(self.engine)

    def create_ingestion_run(
        self,
        *,
        input_type: str,
        input_hash: str,
        raw_input_preview: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        run_id = stable_id("ing", input_type, input_hash, now_utc().isoformat())
        values = {
            "id": run_id,
            "input_type": input_type,
            "input_hash": input_hash,
            "raw_input_preview": raw_input_preview[:500],
            "status": "started",
            "metadata_json": metadata_json or {},
        }
        with self.engine.begin() as conn:
            conn.execute(insert(schema.ingestion_runs).values(**values))
            row = conn.execute(
                select(schema.ingestion_runs).where(schema.ingestion_runs.c.id == run_id)
            ).one()
        return row_dict(row)

    def finish_ingestion_run(
        self,
        run_id: str,
        *,
        status: str,
        source_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                update(schema.ingestion_runs)
                .where(schema.ingestion_runs.c.id == run_id)
                .values(
                    status=status,
                    source_id=source_id,
                    error_message=error_message,
                    finished_at=now_utc(),
                )
            )

    def upsert_source(self, values: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        raw_text = values.get("raw_text") or ""
        source_hash = values.get("content_hash") or content_hash(
            values.get("kind"),
            values.get("uri"),
            values.get("title"),
            raw_text,
        )
        source_id = values.get("id") or stable_id("src", source_hash)
        payload = {
            "id": source_id,
            "kind": values["kind"],
            "title": values.get("title"),
            "uri": values.get("uri"),
            "file_path": values.get("file_path"),
            "raw_text": raw_text,
            "summary": values.get("summary"),
            "content_hash": source_hash,
            "metadata_json": values.get("metadata_json") or {},
            "status": values.get("status") or "processed",
            "captured_at": values.get("captured_at") or now_utc(),
            "processed_at": values.get("processed_at") or now_utc(),
        }

        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.sources).values(**payload))
                created = True
            except IntegrityError:
                created = False
            row = conn.execute(
                select(schema.sources).where(schema.sources.c.content_hash == source_hash)
            ).one()
        return row_dict(row), created

    def upsert_entity(
        self,
        *,
        entity_type: str,
        canonical_name: str,
        aliases: list[str] | None = None,
        confidence: str = "medium",
        metadata_json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        normalized = normalize_name(canonical_name)
        normalized_aliases = [normalize_name(alias) for alias in aliases or [] if alias.strip()]

        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.entities).where(
                    and_(
                        schema.entities.c.type == entity_type,
                        schema.entities.c.normalized_name == normalized,
                    )
                )
            ).first()
            if row is None and normalized_aliases:
                row = conn.execute(
                    select(schema.entities)
                    .join(
                        schema.entity_aliases,
                        schema.entity_aliases.c.entity_id == schema.entities.c.id,
                    )
                    .where(
                        and_(
                            schema.entities.c.type == entity_type,
                            schema.entity_aliases.c.normalized_alias.in_(normalized_aliases),
                        )
                    )
                ).first()

            created = row is None
            if row is None:
                entity_id = stable_id("ent", entity_type, normalized)
                conn.execute(
                    insert(schema.entities).values(
                        id=entity_id,
                        type=entity_type,
                        canonical_name=canonical_name,
                        normalized_name=normalized,
                        confidence=confidence,
                        status="current",
                        metadata_json=metadata_json or {},
                    )
                )
                row = conn.execute(
                    select(schema.entities).where(schema.entities.c.id == entity_id)
                ).one()

            entity = row_dict(row)
            for alias in aliases or []:
                self._insert_alias(
                    conn,
                    entity_id=entity["id"],
                    alias=alias,
                    source_memory_id=None,
                    confidence=confidence,
                )

        return entity, created

    def _insert_alias(
        self,
        conn: Any,
        *,
        entity_id: str,
        alias: str,
        source_memory_id: str | None,
        confidence: str = "medium",
    ) -> None:
        normalized = normalize_name(alias)
        if not normalized:
            return
        alias_id = stable_id("alias", entity_id, normalized)
        try:
            conn.execute(
                insert(schema.entity_aliases).values(
                    id=alias_id,
                    entity_id=entity_id,
                    alias=alias,
                    normalized_alias=normalized,
                    source_memory_id=source_memory_id,
                    confidence=confidence,
                )
            )
        except IntegrityError:
            return

    def upsert_memory_card(self, values: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        card_hash = values.get("content_hash") or content_hash(
            values.get("kind"),
            values.get("statement"),
            values.get("observed_at"),
            values.get("source_id"),
        )
        memory_id = values.get("id") or stable_id("mem", card_hash)
        payload = {
            "id": memory_id,
            "kind": values["kind"],
            "statement": values["statement"],
            "summary": values.get("summary"),
            "confidence": values.get("confidence") or "medium",
            "status": values.get("status") or "current",
            "observed_at": values.get("observed_at"),
            "source_id": values.get("source_id"),
            "source_quote": values.get("source_quote"),
            "metadata_json": values.get("metadata_json") or {},
            "content_hash": card_hash,
        }

        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.memory_cards).values(**payload))
                created = True
            except IntegrityError:
                created = False
            row = conn.execute(
                select(schema.memory_cards).where(schema.memory_cards.c.content_hash == card_hash)
            ).one()
        return row_dict(row), created

    def link_memory_entity(
        self,
        *,
        memory_id: str,
        entity_id: str,
        role: str,
        confidence: str = "medium",
    ) -> None:
        with self.engine.begin() as conn:
            try:
                conn.execute(
                    insert(schema.memory_entities).values(
                        memory_id=memory_id,
                        entity_id=entity_id,
                        role=role,
                        confidence=confidence,
                    )
                )
            except IntegrityError:
                return

    def create_relationship(
        self,
        *,
        subject_entity_id: str,
        predicate: str,
        object_entity_id: str,
        evidence_memory_id: str | None,
        confidence: str = "medium",
        status: str = "current",
        metadata_json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        relationship_id = stable_id(
            "rel",
            subject_entity_id,
            predicate,
            object_entity_id,
            evidence_memory_id,
        )
        payload = {
            "id": relationship_id,
            "subject_entity_id": subject_entity_id,
            "predicate": predicate,
            "object_entity_id": object_entity_id,
            "evidence_memory_id": evidence_memory_id,
            "confidence": confidence,
            "status": status,
            "metadata_json": metadata_json or {},
        }
        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.relationships).values(**payload))
                created = True
            except IntegrityError:
                created = False
            row = conn.execute(
                select(schema.relationships).where(schema.relationships.c.id == relationship_id)
            ).one()
        return row_dict(row), created

    def create_memory_link(
        self,
        *,
        from_memory_id: str,
        relation: str,
        to_memory_id: str,
        confidence: str = "medium",
        metadata_json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        link_id = stable_id("mlink", from_memory_id, relation, to_memory_id)
        payload = {
            "id": link_id,
            "from_memory_id": from_memory_id,
            "relation": relation,
            "to_memory_id": to_memory_id,
            "confidence": confidence,
            "metadata_json": metadata_json or {},
        }
        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.memory_links).values(**payload))
                created = True
            except IntegrityError:
                created = False
            row = conn.execute(
                select(schema.memory_links).where(schema.memory_links.c.id == link_id)
            ).one()
        return row_dict(row), created

    def create_open_loop(
        self,
        *,
        memory_id: str,
        status: str = "open",
        priority: str = "normal",
        next_review_at: datetime | None = None,
        reminder_policy: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        open_loop_id = stable_id("loop", memory_id)
        payload = {
            "id": open_loop_id,
            "memory_id": memory_id,
            "status": status,
            "priority": priority,
            "next_review_at": next_review_at,
            "reminder_policy": reminder_policy,
            "metadata_json": metadata_json or {},
        }
        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.open_loops).values(**payload))
                created = True
            except IntegrityError:
                created = False
            row = conn.execute(
                select(schema.open_loops).where(schema.open_loops.c.id == open_loop_id)
            ).one()
        return row_dict(row), created

    def mark_cognee_pending(
        self,
        *,
        object_type: str,
        object_id: str,
        dataset: str,
        projection_hash: str,
    ) -> None:
        sync_id = stable_id("sync", object_type, object_id, dataset)
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.cognee_sync).where(schema.cognee_sync.c.id == sync_id)
            ).first()
            if row:
                conn.execute(
                    update(schema.cognee_sync)
                    .where(schema.cognee_sync.c.id == sync_id)
                    .values(
                        projection_hash=projection_hash,
                        status="pending",
                        updated_at=now_utc(),
                    )
                )
                return
            conn.execute(
                insert(schema.cognee_sync).values(
                    id=sync_id,
                    object_type=object_type,
                    object_id=object_id,
                    dataset=dataset,
                    projection_hash=projection_hash,
                    status="pending",
                )
            )

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.memory_cards).where(schema.memory_cards.c.id == memory_id)
            ).first()
            if row is None:
                return None
            payload = row_dict(row)
            payload["entities"] = self._memory_entities(conn, memory_id)
            payload["relationships"] = self._memory_relationships(conn, memory_id)
            payload["links"] = self._memory_links(conn, memory_id)
            return payload

    def get_source(
        self,
        source_id: str,
        *,
        include_text: bool = False,
        max_chars: int = 10_000,
    ) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.sources).where(schema.sources.c.id == source_id)
            ).first()
        if row is None:
            return None

        source = row_dict(row)
        raw_text = source.pop("raw_text", None)
        if include_text:
            source["text"] = (raw_text or "")[:max_chars]
        return source

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.entities).where(schema.entities.c.id == entity_id)
            ).first()
            if row is None:
                return None
            aliases = conn.execute(
                select(schema.entity_aliases).where(
                    schema.entity_aliases.c.entity_id == entity_id
                )
            ).fetchall()
        return {**row_dict(row), "aliases": [row_dict(alias) for alias in aliases]}

    def get_open_loop(self, loop_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.open_loops, schema.memory_cards.c.statement)
                .join(schema.memory_cards, schema.memory_cards.c.id == schema.open_loops.c.memory_id)
                .where(schema.open_loops.c.id == loop_id)
            ).first()
        if row is None:
            return None
        return {**row_dict(row), "statement": row._mapping["statement"]}

    def get_ingestion_run(self, run_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.ingestion_runs).where(schema.ingestion_runs.c.id == run_id)
            ).first()
        return row_dict(row) if row is not None else None

    def get_cognee_sync(self, object_id: str) -> list[dict[str, Any]]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.cognee_sync).where(schema.cognee_sync.c.object_id == object_id)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def search_memory(
        self,
        query: str,
        *,
        include_superseded: bool = False,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        terms = WORD_RE.findall(query.casefold())
        if not terms:
            return []

        status_filter = (
            schema.memory_cards.c.status != "superseded" if not include_superseded else None
        )
        text_filters = [
            or_(
                schema.memory_cards.c.statement.ilike(f"%{term}%"),
                schema.memory_cards.c.summary.ilike(f"%{term}%"),
                schema.memory_cards.c.kind.ilike(f"%{term}%"),
            )
            for term in terms
        ]

        with self.engine.begin() as conn:
            direct = conn.execute(
                select(schema.memory_cards)
                .where(and_(*([status_filter] if status_filter is not None else []), or_(*text_filters)))
                .limit(limit)
            ).fetchall()
            entity_rows = conn.execute(
                select(schema.memory_cards)
                .join(
                    schema.memory_entities,
                    schema.memory_entities.c.memory_id == schema.memory_cards.c.id,
                )
                .join(schema.entities, schema.entities.c.id == schema.memory_entities.c.entity_id)
                .where(
                    and_(
                        *([status_filter] if status_filter is not None else []),
                        or_(
                            *[
                                schema.entities.c.normalized_name.ilike(f"%{term}%")
                                for term in terms
                            ]
                        ),
                    )
                )
                .limit(limit)
            ).fetchall()

            seen: set[str] = set()
            results: list[dict[str, Any]] = []
            for row in [*direct, *entity_rows]:
                payload = row_dict(row)
                if payload["id"] in seen:
                    continue
                seen.add(payload["id"])
                payload["entities"] = self._memory_entities(conn, payload["id"])
                results.append(payload)
                if len(results) >= limit:
                    break
        return results

    def resolve_entity(self, name: str, entity_type: str | None = None) -> dict[str, Any] | None:
        normalized = normalize_name(name)
        if not normalized:
            return None
        type_filter = schema.entities.c.type == entity_type if entity_type else True
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.entities).where(
                    and_(type_filter, schema.entities.c.normalized_name == normalized)
                )
            ).first()
            if row:
                return row_dict(row)
            row = conn.execute(
                select(schema.entities)
                .join(schema.entity_aliases, schema.entity_aliases.c.entity_id == schema.entities.c.id)
                .where(
                    and_(type_filter, schema.entity_aliases.c.normalized_alias == normalized)
                )
            ).first()
            if row:
                return row_dict(row)
        return None

    def entity_profile(
        self,
        name: str,
        *,
        entity_type: str | None = None,
        include_superseded: bool = False,
    ) -> dict[str, Any] | None:
        entity = self.resolve_entity(name, entity_type)
        if entity is None:
            return None
        status_filter = (
            schema.memory_cards.c.status != "superseded" if not include_superseded else True
        )
        with self.engine.begin() as conn:
            memory_rows = conn.execute(
                select(schema.memory_cards, schema.memory_entities.c.role)
                .join(
                    schema.memory_entities,
                    schema.memory_entities.c.memory_id == schema.memory_cards.c.id,
                )
                .where(
                    and_(
                        schema.memory_entities.c.entity_id == entity["id"],
                        status_filter,
                    )
                )
                .order_by(schema.memory_cards.c.created_at.desc())
            ).fetchall()
            relationship_rows = conn.execute(
                select(schema.relationships, schema.entities.c.canonical_name.label("other_name"))
                .join(
                    schema.entities,
                    or_(
                        and_(
                            schema.relationships.c.subject_entity_id == entity["id"],
                            schema.relationships.c.object_entity_id == schema.entities.c.id,
                        ),
                        and_(
                            schema.relationships.c.object_entity_id == entity["id"],
                            schema.relationships.c.subject_entity_id == schema.entities.c.id,
                        ),
                    ),
                )
                .where(
                    or_(
                        schema.relationships.c.subject_entity_id == entity["id"],
                        schema.relationships.c.object_entity_id == entity["id"],
                    )
                )
            ).fetchall()
            open_loop_rows = conn.execute(
                select(schema.open_loops, schema.memory_cards.c.statement)
                .join(schema.memory_cards, schema.memory_cards.c.id == schema.open_loops.c.memory_id)
                .join(
                    schema.memory_entities,
                    schema.memory_entities.c.memory_id == schema.memory_cards.c.id,
                )
                .where(
                    and_(
                        schema.memory_entities.c.entity_id == entity["id"],
                        schema.open_loops.c.status == "open",
                    )
                )
            ).fetchall()
            aliases = conn.execute(
                select(schema.entity_aliases).where(schema.entity_aliases.c.entity_id == entity["id"])
            ).fetchall()

        memories = [
            {**row_dict(row), "role": row._mapping["role"]}
            for row in memory_rows
        ]
        relationships = [
            {
                **row_dict(row),
                "other_name": row._mapping["other_name"],
            }
            for row in relationship_rows
        ]
        return {
            "entity": entity,
            "aliases": [row_dict(row) for row in aliases],
            "memories": memories,
            "relationships": relationships,
            "open_loops": [
                {**row_dict(row), "statement": row._mapping["statement"]}
                for row in open_loop_rows
            ],
        }

    def list_open_loops(
        self,
        *,
        topic: str | None = None,
        status: str = "open",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        filters = [] if status == "any" else [schema.open_loops.c.status == status]
        if topic:
            filters.append(schema.memory_cards.c.statement.ilike(f"%{topic}%"))
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.open_loops, schema.memory_cards)
                .join(schema.memory_cards, schema.memory_cards.c.id == schema.open_loops.c.memory_id)
                .where(and_(*filters))
                .order_by(schema.open_loops.c.next_review_at.is_(None), schema.open_loops.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [
            {
                "id": row._mapping[schema.open_loops.c.id],
                "memory_id": row._mapping[schema.open_loops.c.memory_id],
                "status": row._mapping[schema.open_loops.c.status],
                "priority": row._mapping[schema.open_loops.c.priority],
                "next_review_at": row._mapping[schema.open_loops.c.next_review_at],
                "last_reminded_at": row._mapping[schema.open_loops.c.last_reminded_at],
                "reminder_policy": row._mapping[schema.open_loops.c.reminder_policy],
                "statement": row._mapping[schema.memory_cards.c.statement],
                "topics": (row._mapping[schema.memory_cards.c.metadata_json] or {}).get("topics", []),
            }
            for row in rows
        ]

    def forget(self, *, object_type: str, object_id: str, hard: bool = False) -> bool:
        if hard:
            raise ValueError("Hard delete is intentionally not implemented at the service layer.")
        table_by_type = {
            "memory": schema.memory_cards,
            "source": schema.sources,
            "entity": schema.entities,
            "relationship": schema.relationships,
            "open_loop": schema.open_loops,
        }
        table = table_by_type.get(object_type)
        if table is None:
            raise ValueError(
                "object_type must be memory, source, entity, relationship, or open_loop."
            )
        with self.engine.begin() as conn:
            result = conn.execute(
                update(table)
                .where(table.c.id == object_id)
                .values(status="deleted", updated_at=now_utc())
            )
        return result.rowcount > 0

    def update_memory_status(self, memory_id: str, status: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.memory_cards)
                .where(schema.memory_cards.c.id == memory_id)
                .values(status=status, updated_at=now_utc())
            )
        return result.rowcount > 0

    def log_recall(
        self,
        *,
        query: str,
        mode: str,
        retrieved_memory_ids: list[str],
        retrieved_source_ids: list[str],
        answer_preview: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                insert(schema.recall_logs).values(
                    id=stable_id("recall", query, mode, now_utc().isoformat()),
                    query=query,
                    mode=mode,
                    retrieved_memory_ids=retrieved_memory_ids,
                    retrieved_source_ids=retrieved_source_ids,
                    answer_preview=answer_preview[:500],
                    metadata_json=metadata_json or {},
                )
            )

    def _memory_entities(self, conn: Any, memory_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            select(schema.memory_entities, schema.entities)
            .join(schema.entities, schema.entities.c.id == schema.memory_entities.c.entity_id)
            .where(schema.memory_entities.c.memory_id == memory_id)
        ).fetchall()
        return [
            {
                "entity_id": row._mapping[schema.entities.c.id],
                "canonical_name": row._mapping[schema.entities.c.canonical_name],
                "type": row._mapping[schema.entities.c.type],
                "role": row._mapping[schema.memory_entities.c.role],
                "confidence": row._mapping[schema.memory_entities.c.confidence],
            }
            for row in rows
        ]

    def _memory_relationships(self, conn: Any, memory_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            select(schema.relationships).where(
                schema.relationships.c.evidence_memory_id == memory_id
            )
        ).fetchall()
        return [row_dict(row) for row in rows]

    def _memory_links(self, conn: Any, memory_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            select(schema.memory_links).where(
                or_(
                    schema.memory_links.c.from_memory_id == memory_id,
                    schema.memory_links.c.to_memory_id == memory_id,
                )
            )
        ).fetchall()
        return [row_dict(row) for row in rows]


def ensure_parent_dir_for_sqlite(settings: Settings) -> None:
    url = brain_database_url(settings)
    if not url.startswith("sqlite:///") or url == "sqlite:///:memory:":
        return
    path = Path(url.removeprefix("sqlite:///"))
    path.parent.mkdir(parents=True, exist_ok=True)
