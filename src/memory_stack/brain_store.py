from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, and_, create_engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from memory_stack import brain_schema as schema
from memory_stack.cfg import Settings, repo_path


WORD_RE = re.compile(r"[a-z0-9]+")
DEFAULT_USER_ID = "default"


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


def normalize_user_id(value: str | None) -> str:
    normalized = normalize_name(value or DEFAULT_USER_ID).replace(" ", "_")
    return normalized or DEFAULT_USER_ID


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


def jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=True, sort_keys=True, default=str))


class BrainStore:
    def __init__(self, settings: Settings, *, user_id: str | None = None) -> None:
        self.settings = settings
        self.user_id = normalize_user_id(user_id or settings.brain_user_id)
        self.engine = create_brain_engine(settings)
        schema.metadata.create_all(self.engine)
        self.ensure_user()

    def ensure_user(self) -> None:
        with self.engine.begin() as conn:
            try:
                conn.execute(
                    insert(schema.brain_users).values(
                        id=self.user_id,
                        display_name=self.user_id,
                        status="active",
                        metadata_json={},
                    )
                )
            except IntegrityError:
                return

    def _user_filter(self, table: Any) -> Any:
        return table.c.user_id == self.user_id

    def _scoped_hash(self, *values: Any) -> str:
        return content_hash("user", self.user_id, *values)

    def _scoped_id(self, prefix: str, *values: Any) -> str:
        return stable_id(prefix, "user", self.user_id, *values)

    def _object_id(self, prefix: str, supplied_id: Any | None, *fallback_values: Any) -> str:
        if supplied_id:
            raw_id = str(supplied_id)
            if self.user_id == DEFAULT_USER_ID:
                return raw_id
            return self._scoped_id(prefix, "external", raw_id)
        return stable_id(prefix, *fallback_values)

    def make_external_id(self, prefix: str, *values: Any) -> str:
        return self._scoped_id(prefix, *values)

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
                        self._user_filter(schema.entities),
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
                        self._user_filter(schema.entities),
                        self._user_filter(schema.entity_aliases),
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
        entity_id = self._scoped_id("ent", entity_type, normalized_name)
        with self.engine.begin() as conn:
            try:
                conn.execute(
                    insert(schema.entities).values(
                        id=entity_id,
                        user_id=self.user_id,
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
                select(schema.entities).where(
                    and_(schema.entities.c.id == entity_id, self._user_filter(schema.entities))
                )
            ).one()
        return row_dict(row), created

    def add_entity_alias(
        self,
        *,
        entity_id: str,
        alias: str,
        confidence: str = "medium",
    ) -> None:
        with self.engine.begin() as conn:
            self._insert_alias(
                conn,
                entity_id=entity_id,
                alias=alias,
                confidence=confidence,
            )

    def _insert_alias(
        self,
        conn: Any,
        *,
        entity_id: str,
        alias: str,
        confidence: str = "medium",
    ) -> None:
        normalized = normalize_name(alias)
        if not normalized:
            return
        alias_id = self._scoped_id("alias", entity_id, normalized)
        try:
            conn.execute(
                insert(schema.entity_aliases).values(
                    id=alias_id,
                    user_id=self.user_id,
                    entity_id=entity_id,
                    alias=alias,
                    normalized_alias=normalized,
                    confidence=confidence,
                )
            )
        except IntegrityError:
            return

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.entities).where(
                    and_(schema.entities.c.id == entity_id, self._user_filter(schema.entities))
                )
            ).first()
            if row is None:
                return None
            aliases = conn.execute(
                select(schema.entity_aliases).where(
                    and_(
                        schema.entity_aliases.c.entity_id == entity_id,
                        self._user_filter(schema.entity_aliases),
                    )
                )
            ).fetchall()
        return {**row_dict(row), "aliases": [row_dict(alias) for alias in aliases]}

    def get_or_create_session_map(
        self,
        *,
        profile_name: str,
        surface: str,
        client_session_id: str,
        cognee_dataset: str,
        cognee_session_id: str | None = None,
        node_sets_json: list[str] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session_id = self._scoped_id(
            "sess",
            profile_name,
            surface,
            client_session_id,
        )
        mapped_cognee_session_id = cognee_session_id or self._scoped_id(
            "cog_sess",
            profile_name,
            surface,
            client_session_id,
        )
        filters = [
            self._user_filter(schema.brain_session_maps),
            schema.brain_session_maps.c.profile_name == profile_name,
            schema.brain_session_maps.c.surface == surface,
            schema.brain_session_maps.c.client_session_id == client_session_id,
        ]
        values = {
            "id": session_id,
            "user_id": self.user_id,
            "profile_name": profile_name,
            "surface": surface,
            "client_session_id": client_session_id,
            "cognee_session_id": mapped_cognee_session_id,
            "cognee_dataset": cognee_dataset,
            "node_sets_json": jsonable(node_sets_json or []),
            "metadata_json": jsonable(metadata_json or {}),
        }
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.brain_session_maps).where(and_(*filters))
            ).first()
            if row is None:
                try:
                    conn.execute(insert(schema.brain_session_maps).values(**values))
                except IntegrityError:
                    pass
            update_values = {
                "cognee_dataset": cognee_dataset,
                "node_sets_json": jsonable(node_sets_json or []),
                "metadata_json": jsonable(metadata_json or {}),
                "updated_at": now_utc(),
                "last_used_at": now_utc(),
            }
            if cognee_session_id is not None:
                update_values["cognee_session_id"] = cognee_session_id
            conn.execute(
                update(schema.brain_session_maps)
                .where(and_(*filters))
                .values(**update_values)
            )
            row = conn.execute(
                select(schema.brain_session_maps).where(and_(*filters))
            ).one()
        return row_dict(row)

    def get_session_map(self, session_map_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.brain_session_maps).where(
                    and_(
                        schema.brain_session_maps.c.id == session_map_id,
                        self._user_filter(schema.brain_session_maps),
                    )
                )
            ).first()
        return row_dict(row) if row is not None else None

    def create_external_receipt(
        self,
        *,
        receipt_id: str | None = None,
        surface: str,
        tool_name: str,
        action: str,
        status: str,
        summary: str | None = None,
        cognee_dataset: str | None = None,
        cognee_reference: str | None = None,
        cognee_result_json: dict[str, Any] | list[Any] | None = None,
        warnings_json: list[Any] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        receipt_id = receipt_id or self._scoped_id(
            "rcpt",
            surface,
            tool_name,
            action,
            status,
            content_hash(summary, cognee_dataset, cognee_reference, metadata_json or {}),
            now_utc().isoformat(),
        )
        values = {
            "id": receipt_id,
            "user_id": self.user_id,
            "surface": surface,
            "tool_name": tool_name,
            "action": action,
            "status": status,
            "summary": summary,
            "cognee_dataset": cognee_dataset,
            "cognee_reference": cognee_reference,
            "cognee_result_json": jsonable(cognee_result_json or {}),
            "warnings_json": jsonable(warnings_json or []),
            "metadata_json": jsonable(metadata_json or {}),
        }
        with self.engine.begin() as conn:
            conn.execute(insert(schema.brain_external_receipts).values(**values))
            row = conn.execute(
                select(schema.brain_external_receipts).where(
                    and_(
                        schema.brain_external_receipts.c.id == receipt_id,
                        self._user_filter(schema.brain_external_receipts),
                    )
                )
            ).one()
        return row_dict(row)

    def get_or_create_external_receipt(
        self,
        *,
        receipt_id: str,
        surface: str,
        tool_name: str,
        action: str,
        status: str,
        summary: str | None = None,
        cognee_dataset: str | None = None,
        cognee_reference: str | None = None,
        cognee_result_json: dict[str, Any] | list[Any] | None = None,
        warnings_json: list[Any] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        existing = self.get_external_receipt(receipt_id)
        if existing is not None:
            return existing, False
        try:
            receipt = self.create_external_receipt(
                receipt_id=receipt_id,
                surface=surface,
                tool_name=tool_name,
                action=action,
                status=status,
                summary=summary,
                cognee_dataset=cognee_dataset,
                cognee_reference=cognee_reference,
                cognee_result_json=cognee_result_json,
                warnings_json=warnings_json,
                metadata_json=metadata_json,
            )
        except IntegrityError:
            receipt = self.get_external_receipt(receipt_id)
            if receipt is None:
                raise
            return receipt, False
        return receipt, True

    def get_external_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.brain_external_receipts).where(
                    and_(
                        schema.brain_external_receipts.c.id == receipt_id,
                        self._user_filter(schema.brain_external_receipts),
                    )
                )
            ).first()
        return row_dict(row) if row is not None else None

    def update_external_receipt(
        self,
        receipt_id: str,
        *,
        status: str | None = None,
        summary: str | None = None,
        cognee_dataset: str | None = None,
        cognee_reference: str | None = None,
        cognee_result_json: dict[str, Any] | list[Any] | None = None,
        warnings_json: list[Any] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        values: dict[str, Any] = {}
        if status is not None:
            values["status"] = status
        if summary is not None:
            values["summary"] = summary
        if cognee_dataset is not None:
            values["cognee_dataset"] = cognee_dataset
        if cognee_reference is not None:
            values["cognee_reference"] = cognee_reference
        if cognee_result_json is not None:
            values["cognee_result_json"] = jsonable(cognee_result_json)
        if warnings_json is not None:
            values["warnings_json"] = jsonable(warnings_json)
        if metadata_json is not None:
            values["metadata_json"] = jsonable(metadata_json)
        if not values:
            return self.get_external_receipt(receipt_id)
        with self.engine.begin() as conn:
            conn.execute(
                update(schema.brain_external_receipts)
                .where(
                    and_(
                        schema.brain_external_receipts.c.id == receipt_id,
                        self._user_filter(schema.brain_external_receipts),
                    )
                )
                .values(**values)
            )
            row = conn.execute(
                select(schema.brain_external_receipts).where(
                    and_(
                        schema.brain_external_receipts.c.id == receipt_id,
                        self._user_filter(schema.brain_external_receipts),
                    )
                )
            ).first()
        return row_dict(row) if row is not None else None

    def claim_external_receipt(
        self,
        receipt_id: str,
        *,
        expected_statuses: tuple[str, ...] = ("queued",),
        claimed_status: str = "running",
    ) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.brain_external_receipts)
                .where(
                    and_(
                        schema.brain_external_receipts.c.id == receipt_id,
                        self._user_filter(schema.brain_external_receipts),
                        schema.brain_external_receipts.c.status.in_(expected_statuses),
                    )
                )
                .values(status=claimed_status)
            )
            if result.rowcount != 1:
                return None
            row = conn.execute(
                select(schema.brain_external_receipts).where(
                    and_(
                        schema.brain_external_receipts.c.id == receipt_id,
                        self._user_filter(schema.brain_external_receipts),
                    )
                )
            ).one()
        return row_dict(row)

    def list_external_receipts(
        self,
        *,
        status: str | None = None,
        action: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = [self._user_filter(schema.brain_external_receipts)]
        if status is not None:
            filters.append(schema.brain_external_receipts.c.status == status)
        if action is not None:
            filters.append(schema.brain_external_receipts.c.action == action)
        if since is not None:
            filters.append(schema.brain_external_receipts.c.created_at >= since)
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.brain_external_receipts)
                .where(and_(*filters))
                .order_by(schema.brain_external_receipts.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def create_pending_confirmation(
        self,
        *,
        surface: str,
        action: str,
        original_input: str,
        proposed_payload_json: dict[str, Any] | list[Any],
        reason: str | None = None,
        options_json: list[Any] | None = None,
        expires_at: datetime | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        confirmation_id = self._scoped_id(
            "conf",
            surface,
            action,
            content_hash(original_input, proposed_payload_json, metadata_json or {}),
            now_utc().isoformat(),
        )
        values = {
            "id": confirmation_id,
            "user_id": self.user_id,
            "surface": surface,
            "action": action,
            "original_input": original_input,
            "proposed_payload_json": jsonable(proposed_payload_json),
            "reason": reason,
            "options_json": jsonable(options_json or []),
            "status": "pending",
            "expires_at": expires_at,
            "metadata_json": jsonable(metadata_json or {}),
        }
        with self.engine.begin() as conn:
            conn.execute(insert(schema.brain_pending_confirmations).values(**values))
            row = conn.execute(
                select(schema.brain_pending_confirmations).where(
                    and_(
                        schema.brain_pending_confirmations.c.id == confirmation_id,
                        self._user_filter(schema.brain_pending_confirmations),
                    )
                )
            ).one()
        return row_dict(row)

    def get_pending_confirmation(self, confirmation_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.brain_pending_confirmations).where(
                    and_(
                        schema.brain_pending_confirmations.c.id == confirmation_id,
                        self._user_filter(schema.brain_pending_confirmations),
                    )
                )
            ).first()
        return row_dict(row) if row is not None else None

    def update_pending_confirmation_status(
        self,
        confirmation_id: str,
        status: str,
        *,
        confirmed_at: datetime | None = None,
    ) -> bool:
        values: dict[str, Any] = {
            "status": status,
            "updated_at": now_utc(),
        }
        if confirmed_at is not None:
            values["confirmed_at"] = confirmed_at
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.brain_pending_confirmations)
                .where(
                    and_(
                        schema.brain_pending_confirmations.c.id == confirmation_id,
                        self._user_filter(schema.brain_pending_confirmations),
                    )
                )
                .values(**values)
            )
        return result.rowcount > 0

    def list_pending_confirmations(
        self,
        *,
        status: str | None = "pending",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = [self._user_filter(schema.brain_pending_confirmations)]
        if status is not None:
            filters.append(schema.brain_pending_confirmations.c.status == status)
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.brain_pending_confirmations)
                .where(and_(*filters))
                .order_by(schema.brain_pending_confirmations.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def create_context_record(
        self,
        *,
        record_id: str | None = None,
        kind: str,
        statement: str,
        scope: str = "profile",
        source: str | None = None,
        status: str = "current",
        metadata_json: dict[str, Any] | None = None,
        cognee_reference: str | None = None,
    ) -> dict[str, Any]:
        resolved_record_id = record_id or self._scoped_id(
            "ctx",
            kind,
            scope,
            content_hash(statement, source, metadata_json or {}),
        )
        values = {
            "id": resolved_record_id,
            "user_id": self.user_id,
            "kind": kind,
            "statement": statement,
            "scope": scope,
            "source": source,
            "status": status,
            "metadata_json": jsonable(metadata_json or {}),
            "cognee_reference": cognee_reference,
        }
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(schema.brain_context_records).where(
                    and_(
                        schema.brain_context_records.c.id == resolved_record_id,
                        self._user_filter(schema.brain_context_records),
                    )
                )
            ).first()
            if existing is None:
                conn.execute(insert(schema.brain_context_records).values(**values))
            else:
                conn.execute(
                    update(schema.brain_context_records)
                    .where(
                        and_(
                            schema.brain_context_records.c.id == resolved_record_id,
                            self._user_filter(schema.brain_context_records),
                        )
                    )
                    .values(
                        kind=kind,
                        statement=statement,
                        scope=scope,
                        source=source,
                        status=status,
                        metadata_json=jsonable(metadata_json or {}),
                        cognee_reference=cognee_reference,
                        updated_at=now_utc(),
                    )
                )
            row = conn.execute(
                select(schema.brain_context_records).where(
                    and_(
                        schema.brain_context_records.c.id == resolved_record_id,
                        self._user_filter(schema.brain_context_records),
                    )
                )
            ).one()
        return row_dict(row)

    def get_context_record(self, record_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.brain_context_records).where(
                    and_(
                        schema.brain_context_records.c.id == record_id,
                        self._user_filter(schema.brain_context_records),
                    )
                )
            ).first()
        return row_dict(row) if row is not None else None

    def list_context_records(
        self,
        *,
        kind: str | None = None,
        scope: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = [self._user_filter(schema.brain_context_records)]
        if kind is not None:
            filters.append(schema.brain_context_records.c.kind == kind)
        if scope is not None:
            filters.append(schema.brain_context_records.c.scope == scope)
        if not include_deleted:
            filters.append(schema.brain_context_records.c.status != "deleted")
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.brain_context_records)
                .where(and_(*filters))
                .order_by(schema.brain_context_records.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [row_dict(row) for row in rows]

    def update_context_record_status(self, record_id: str, status: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.brain_context_records)
                .where(
                    and_(
                        schema.brain_context_records.c.id == record_id,
                        self._user_filter(schema.brain_context_records),
                    )
                )
                .values(status=status, updated_at=now_utc())
            )
        return result.rowcount > 0

    def resolve_entity(self, name: str, entity_type: str | None = None) -> dict[str, Any] | None:
        normalized = normalize_name(name)
        if not normalized:
            return None
        owner_names = {
            normalize_name(self.settings.brain_owner_name),
            normalize_name(self.settings.brain_owner_full_name),
            "me",
            "myself",
            "the user",
            "profile owner",
        }
        if (entity_type in {None, "person"}) and normalized in owner_names:
            owner = self.find_entity_by_normalized_name(
                entity_type="person",
                normalized_name=normalize_name(self.settings.brain_owner_full_name),
            )
            if owner and (owner.get("metadata_json") or {}).get("is_profile_owner"):
                return owner
        type_filter = schema.entities.c.type == entity_type if entity_type else True
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.entities).where(
                    and_(
                        self._user_filter(schema.entities),
                        type_filter,
                        schema.entities.c.normalized_name == normalized,
                    )
                )
            ).first()
            if row:
                return row_dict(row)
            row = conn.execute(
                select(schema.entities)
                .join(schema.entity_aliases, schema.entity_aliases.c.entity_id == schema.entities.c.id)
                .where(
                    and_(
                        self._user_filter(schema.entities),
                        self._user_filter(schema.entity_aliases),
                        type_filter,
                        schema.entity_aliases.c.normalized_alias == normalized,
                    )
                )
            ).first()
            if row:
                return row_dict(row)
        return None

    def forget(self, *, object_type: str, object_id: str, hard: bool = False) -> bool:
        if hard:
            raise ValueError("Hard delete is intentionally not implemented at the service layer.")
        table_by_type = {
            "entity": schema.entities,
        }
        table = table_by_type.get(object_type)
        if table is None:
            raise ValueError("object_type must be entity.")
        with self.engine.begin() as conn:
            result = conn.execute(
                update(table)
                .where(and_(table.c.id == object_id, self._user_filter(table)))
                .values(status="deleted", updated_at=now_utc())
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
                .where(and_(schema.entities.c.id == entity_id, self._user_filter(schema.entities)))
                .values(**values)
            )
        return result.rowcount > 0

def ensure_parent_dir_for_sqlite(settings: Settings) -> None:
    url = brain_database_url(settings)
    if not url.startswith("sqlite:///") or url == "sqlite:///:memory:":
        return
    path = Path(url.removeprefix("sqlite:///"))
    path.parent.mkdir(parents=True, exist_ok=True)
