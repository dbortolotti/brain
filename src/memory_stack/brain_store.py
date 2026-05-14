from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, and_, create_engine, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from memory_stack import brain_schema as schema
from memory_stack.cfg import Settings, repo_path


WORD_RE = re.compile(r"[a-z0-9]+")


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def normalize_name(value: str) -> str:
    return " ".join(WORD_RE.findall(value.casefold()))


def content_hash(*values: Any) -> str:
    payload = json.dumps(values, ensure_ascii=True, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *values: Any) -> str:
    digest = content_hash(*values).split(":", 1)[1][:16]
    return f"{prefix}_{digest}"


def visible_memory_status_filter(
    *,
    include_superseded: bool = False,
    include_conflicts: bool = True,
) -> Any:
    statuses = ["current"]
    if include_conflicts:
        statuses.append("conflicted")
    if include_superseded:
        statuses.append("superseded")
    return schema.memory_cards.c.status.in_(statuses)


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
        from memory_stack.resolution.entity_resolver import EntityResolver

        resolution = EntityResolver(self).resolve_entity(
            entity_type=entity_type,
            canonical_name=canonical_name,
            aliases=aliases,
            confidence=confidence,
            metadata_json=metadata_json,
        )
        return resolution.entity, resolution.created

    def find_entity_by_normalized_name(
        self,
        *,
        entity_type: str,
        normalized_name: str,
    ) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.entities).where(
                    and_(
                        schema.entities.c.type == entity_type,
                        schema.entities.c.normalized_name == normalized_name,
                    )
                )
            ).first()
        return row_dict(row) if row is not None else None

    def find_entities_by_alias(
        self,
        *,
        entity_type: str,
        normalized_alias: str,
    ) -> list[dict[str, Any]]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.entities)
                .join(
                    schema.entity_aliases,
                    schema.entity_aliases.c.entity_id == schema.entities.c.id,
                )
                .where(
                    and_(
                        schema.entities.c.type == entity_type,
                        schema.entity_aliases.c.normalized_alias == normalized_alias,
                    )
                )
            ).fetchall()
        return [row_dict(row) for row in rows]

    def create_entity(
        self,
        *,
        entity_type: str,
        canonical_name: str,
        normalized_name: str,
        confidence: str = "medium",
        metadata_json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        entity_id = stable_id("ent", entity_type, normalized_name)
        with self.engine.begin() as conn:
            try:
                conn.execute(
                    insert(schema.entities).values(
                        id=entity_id,
                        type=entity_type,
                        canonical_name=canonical_name,
                        normalized_name=normalized_name,
                        confidence=confidence,
                        status="current",
                        metadata_json=metadata_json or {},
                    )
                )
                created = True
            except IntegrityError:
                created = False
            row = conn.execute(
                select(schema.entities).where(schema.entities.c.id == entity_id)
            ).one()
        return row_dict(row), created

    def add_entity_alias(
        self,
        *,
        entity_id: str,
        alias: str,
        source_memory_id: str | None = None,
        confidence: str = "medium",
    ) -> None:
        with self.engine.begin() as conn:
            self._insert_alias(
                conn,
                entity_id=entity_id,
                alias=alias,
                source_memory_id=source_memory_id,
                confidence=confidence,
            )

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
                        error_message=None,
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

    def mark_cognee_stale(
        self,
        *,
        object_type: str,
        object_id: str,
        dataset: str | None = None,
        projection_hash: str | None = None,
    ) -> int:
        filters = [
            schema.cognee_sync.c.object_type == object_type,
            schema.cognee_sync.c.object_id == object_id,
        ]
        if dataset is not None:
            filters.append(schema.cognee_sync.c.dataset == dataset)
        values: dict[str, Any] = {"status": "stale", "updated_at": now_utc()}
        if projection_hash is not None:
            values["projection_hash"] = projection_hash
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.cognee_sync)
                .where(and_(*filters))
                .values(**values)
            )
        return result.rowcount

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

    def get_cognee_sync_by_id(self, sync_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.cognee_sync).where(schema.cognee_sync.c.id == sync_id)
            ).first()
        return row_dict(row) if row is not None else None

    def list_cognee_sync(
        self,
        *,
        statuses: list[str] | tuple[str, ...] | None = None,
        object_type: str | None = None,
        object_id: str | None = None,
        dataset: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = []
        if statuses:
            filters.append(schema.cognee_sync.c.status.in_(list(statuses)))
        if object_type:
            filters.append(schema.cognee_sync.c.object_type == object_type)
        if object_id:
            filters.append(schema.cognee_sync.c.object_id == object_id)
        if dataset:
            filters.append(schema.cognee_sync.c.dataset == dataset)
        where_clause = and_(*filters) if filters else True
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.cognee_sync)
                .where(where_clause)
                .order_by(schema.cognee_sync.c.updated_at.asc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def update_cognee_sync_status(
        self,
        sync_id: str,
        *,
        status: str,
        projection_hash: str | None = None,
        cognee_reference: str | None = None,
        error_message: str | None = None,
        last_synced_at: datetime | None = None,
    ) -> bool:
        values: dict[str, Any] = {
            "status": status,
            "error_message": error_message,
            "updated_at": now_utc(),
        }
        if projection_hash is not None:
            values["projection_hash"] = projection_hash
        if cognee_reference is not None:
            values["cognee_reference"] = cognee_reference
        if last_synced_at is not None:
            values["last_synced_at"] = last_synced_at
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.cognee_sync)
                .where(schema.cognee_sync.c.id == sync_id)
                .values(**values)
            )
        return result.rowcount > 0

    def list_memory_cards(
        self,
        *,
        since: datetime | None = None,
        source_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = []
        if since is not None:
            filters.append(schema.memory_cards.c.created_at >= since)
        if source_id is not None:
            filters.append(schema.memory_cards.c.source_id == source_id)
        if not include_deleted:
            filters.append(schema.memory_cards.c.status != "deleted")
        where_clause = and_(*filters) if filters else True
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.memory_cards)
                .where(where_clause)
                .order_by(schema.memory_cards.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def list_memories_by_entity(
        self,
        entity_id: str,
        *,
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        status_filter = visible_memory_status_filter(
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
        )
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.memory_cards)
                .join(
                    schema.memory_entities,
                    schema.memory_entities.c.memory_id == schema.memory_cards.c.id,
                )
                .where(and_(schema.memory_entities.c.entity_id == entity_id, status_filter))
                .order_by(schema.memory_cards.c.created_at.desc())
                .limit(limit)
            ).fetchall()
            results = []
            for row in rows:
                payload = row_dict(row)
                payload["entities"] = self._memory_entities(conn, payload["id"])
                payload["relationships"] = self._memory_relationships(conn, payload["id"])
                payload["links"] = self._memory_links(conn, payload["id"])
                results.append(payload)
        return results

    def list_sources(
        self,
        *,
        since: datetime | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = []
        if since is not None:
            filters.append(schema.sources.c.created_at >= since)
        if not include_deleted:
            filters.append(schema.sources.c.status != "deleted")
        where_clause = and_(*filters) if filters else True
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.sources)
                .where(where_clause)
                .order_by(schema.sources.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def list_ingestion_runs(
        self,
        *,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = []
        if since is not None:
            filters.append(schema.ingestion_runs.c.started_at >= since)
        where_clause = and_(*filters) if filters else True
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.ingestion_runs)
                .where(where_clause)
                .order_by(schema.ingestion_runs.c.started_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def list_memory_links(
        self,
        *,
        relations: list[str] | tuple[str, ...] | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = []
        if relations:
            filters.append(schema.memory_links.c.relation.in_(list(relations)))
        if since is not None:
            filters.append(schema.memory_links.c.created_at >= since)
        where_clause = and_(*filters) if filters else True
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.memory_links)
                .where(where_clause)
                .order_by(schema.memory_links.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def search_memory(
        self,
        query: str,
        *,
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        terms = WORD_RE.findall(query.casefold())
        if not terms:
            return []

        status_filter = visible_memory_status_filter(
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
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
                .where(and_(status_filter, or_(*text_filters)))
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
                        status_filter,
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
        include_conflicts: bool = True,
    ) -> dict[str, Any] | None:
        entity = self.resolve_entity(name, entity_type)
        if entity is None:
            return None
        status_filter = visible_memory_status_filter(
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
        )
        subject_entities = schema.entities.alias("subject_entities")
        object_entities = schema.entities.alias("object_entities")
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
                select(
                    schema.relationships,
                    subject_entities.c.canonical_name.label("subject_name"),
                    object_entities.c.canonical_name.label("object_name"),
                )
                .join(
                    subject_entities,
                    subject_entities.c.id == schema.relationships.c.subject_entity_id,
                )
                .join(
                    object_entities,
                    object_entities.c.id == schema.relationships.c.object_entity_id,
                )
                .outerjoin(
                    schema.memory_cards,
                    schema.memory_cards.c.id == schema.relationships.c.evidence_memory_id,
                )
                .where(
                    and_(
                        or_(
                            schema.relationships.c.subject_entity_id == entity["id"],
                            schema.relationships.c.object_entity_id == entity["id"],
                        ),
                        schema.relationships.c.status == "current",
                        or_(
                            schema.relationships.c.evidence_memory_id.is_(None),
                            status_filter,
                        ),
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
                        status_filter,
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
                "subject_name": row._mapping["subject_name"],
                "object_name": row._mapping["object_name"],
                "direction_relative_to_profile_entity": (
                    "outgoing"
                    if row._mapping[schema.relationships.c.subject_entity_id] == entity["id"]
                    else "incoming"
                ),
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
                .where(and_(*filters, visible_memory_status_filter()))
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

    def list_due_open_loops(
        self,
        *,
        now: datetime | None = None,
        include_recently_reminded: bool = False,
        recent_seconds: int = 60 * 60 * 24,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        active_now = as_utc(now or now_utc())
        loops = self.list_open_loops(status="open", limit=limit * 5)
        due: list[dict[str, Any]] = []
        for loop in loops:
            next_review_at = loop.get("next_review_at")
            if next_review_at is not None and as_utc(next_review_at) > active_now:
                continue
            last_reminded_at = loop.get("last_reminded_at")
            if (
                not include_recently_reminded
                and last_reminded_at is not None
                and (active_now - as_utc(last_reminded_at)).total_seconds() < recent_seconds
            ):
                continue
            due.append(loop)
            if len(due) >= limit:
                break
        return due

    def mark_open_loop_reminded(
        self,
        loop_id: str,
        *,
        reminded_at: datetime | None = None,
        next_review_at: datetime | None = None,
    ) -> bool:
        values: dict[str, Any] = {
            "last_reminded_at": reminded_at or now_utc(),
            "updated_at": now_utc(),
        }
        if next_review_at is not None:
            values["next_review_at"] = next_review_at
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.open_loops)
                .where(schema.open_loops.c.id == loop_id)
                .values(**values)
            )
        return result.rowcount > 0

    def update_open_loop_status(self, loop_id: str, status: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.open_loops)
                .where(schema.open_loops.c.id == loop_id)
                .values(status=status, updated_at=now_utc())
            )
        return result.rowcount > 0

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
            if result.rowcount > 0 and object_type in {"memory", "source"}:
                conn.execute(
                    update(schema.cognee_sync)
                    .where(
                        and_(
                            schema.cognee_sync.c.object_type == object_type,
                            schema.cognee_sync.c.object_id == object_id,
                        )
                    )
                    .values(status="stale", updated_at=now_utc())
                )
        return result.rowcount > 0

    def update_memory_status(self, memory_id: str, status: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.memory_cards)
                .where(schema.memory_cards.c.id == memory_id)
                .values(status=status, updated_at=now_utc())
            )
            if result.rowcount > 0:
                conn.execute(
                    update(schema.cognee_sync)
                    .where(
                        and_(
                            schema.cognee_sync.c.object_type == "memory",
                            schema.cognee_sync.c.object_id == memory_id,
                        )
                    )
                    .values(status="stale", updated_at=now_utc())
                )
        return result.rowcount > 0

    def update_source_status(self, source_id: str, status: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.sources)
                .where(schema.sources.c.id == source_id)
                .values(status=status, updated_at=now_utc())
            )
            if result.rowcount > 0:
                conn.execute(
                    update(schema.cognee_sync)
                    .where(
                        and_(
                            schema.cognee_sync.c.object_type == "source",
                            schema.cognee_sync.c.object_id == source_id,
                        )
                    )
                    .values(status="stale", updated_at=now_utc())
                )
        return result.rowcount > 0

    def update_entity_status(
        self,
        entity_id: str,
        status: str,
        *,
        metadata_updates: dict[str, Any] | None = None,
    ) -> bool:
        values: dict[str, Any] = {"status": status, "updated_at": now_utc()}
        if metadata_updates:
            entity = self.get_entity(entity_id)
            metadata = dict(entity.get("metadata_json") or {}) if entity else {}
            metadata.update(metadata_updates)
            values["metadata_json"] = metadata
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.entities)
                .where(schema.entities.c.id == entity_id)
                .values(**values)
            )
        return result.rowcount > 0

    def merge_entities(
        self,
        *,
        primary_entity_id: str,
        duplicate_entity_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        primary = self.get_entity(primary_entity_id)
        duplicate = self.get_entity(duplicate_entity_id)
        if primary is None or duplicate is None:
            raise ValueError("Both primary_entity_id and duplicate_entity_id must exist.")
        if primary_entity_id == duplicate_entity_id:
            raise ValueError("primary_entity_id and duplicate_entity_id must be different.")

        moved_aliases = 0
        repointed_memories = 0
        repointed_relationships = 0
        archived = False
        with self.engine.begin() as conn:
            canonical_alias_exists = conn.execute(
                select(schema.entity_aliases).where(
                    and_(
                        schema.entity_aliases.c.entity_id == primary_entity_id,
                        schema.entity_aliases.c.normalized_alias
                        == normalize_name(duplicate["canonical_name"]),
                    )
                )
            ).first()
            if canonical_alias_exists is None:
                self._insert_alias(
                    conn,
                    entity_id=primary_entity_id,
                    alias=duplicate["canonical_name"],
                    source_memory_id=None,
                    confidence=duplicate.get("confidence") or "medium",
                )
                moved_aliases += 1
            duplicate_alias_rows = conn.execute(
                select(schema.entity_aliases).where(
                    schema.entity_aliases.c.entity_id == duplicate_entity_id
                )
            ).fetchall()
            for alias_row in duplicate_alias_rows:
                alias = row_dict(alias_row)
                before = conn.execute(
                    select(schema.entity_aliases).where(
                        and_(
                            schema.entity_aliases.c.entity_id == primary_entity_id,
                            schema.entity_aliases.c.normalized_alias == alias["normalized_alias"],
                        )
                    )
                ).first()
                if before is None:
                    self._insert_alias(
                        conn,
                        entity_id=primary_entity_id,
                        alias=alias["alias"],
                        source_memory_id=alias.get("source_memory_id"),
                        confidence=alias.get("confidence") or "medium",
                    )
                    moved_aliases += 1
            conn.execute(
                delete(schema.entity_aliases).where(
                    schema.entity_aliases.c.entity_id == duplicate_entity_id
                )
            )

            duplicate_memory_rows = conn.execute(
                select(schema.memory_entities).where(
                    schema.memory_entities.c.entity_id == duplicate_entity_id
                )
            ).fetchall()
            for memory_row in duplicate_memory_rows:
                memory_link = row_dict(memory_row)
                existing = conn.execute(
                    select(schema.memory_entities).where(
                        and_(
                            schema.memory_entities.c.memory_id == memory_link["memory_id"],
                            schema.memory_entities.c.entity_id == primary_entity_id,
                            schema.memory_entities.c.role == memory_link["role"],
                        )
                    )
                ).first()
                if existing is None:
                    conn.execute(
                        insert(schema.memory_entities).values(
                            memory_id=memory_link["memory_id"],
                            entity_id=primary_entity_id,
                            role=memory_link["role"],
                            confidence=memory_link["confidence"],
                        )
                    )
                    repointed_memories += 1
                conn.execute(
                    delete(schema.memory_entities).where(
                        and_(
                            schema.memory_entities.c.memory_id == memory_link["memory_id"],
                            schema.memory_entities.c.entity_id == duplicate_entity_id,
                            schema.memory_entities.c.role == memory_link["role"],
                        )
                    )
                )

            subject_result = conn.execute(
                update(schema.relationships)
                .where(schema.relationships.c.subject_entity_id == duplicate_entity_id)
                .values(subject_entity_id=primary_entity_id, updated_at=now_utc())
            )
            object_result = conn.execute(
                update(schema.relationships)
                .where(schema.relationships.c.object_entity_id == duplicate_entity_id)
                .values(object_entity_id=primary_entity_id, updated_at=now_utc())
            )
            repointed_relationships = subject_result.rowcount + object_result.rowcount

            duplicate_metadata = dict(duplicate.get("metadata_json") or {})
            duplicate_metadata.update(
                {
                    "merged_into": primary_entity_id,
                    "merge_reason": reason,
                    "merged_at": now_utc().isoformat(),
                }
            )
            archive_result = conn.execute(
                update(schema.entities)
                .where(schema.entities.c.id == duplicate_entity_id)
                .values(
                    status="archived",
                    metadata_json=duplicate_metadata,
                    updated_at=now_utc(),
                )
            )
            archived = archive_result.rowcount > 0

        return {
            "primary_entity_id": primary_entity_id,
            "duplicate_entity_id": duplicate_entity_id,
            "moved_aliases": moved_aliases,
            "repointed_memories": repointed_memories,
            "repointed_relationships": repointed_relationships,
            "duplicate_status": "archived" if archived else duplicate["status"],
        }

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
