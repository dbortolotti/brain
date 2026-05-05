from __future__ import annotations

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    func,
)

metadata = MetaData()


sources = Table(
    "sources",
    metadata,
    Column("id", Text, primary_key=True),
    Column("kind", Text, nullable=False),
    Column("title", Text),
    Column("uri", Text),
    Column("file_path", Text),
    Column("raw_text", Text),
    Column("summary", Text),
    Column("content_hash", Text, nullable=False, unique=True),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("status", Text, nullable=False, default="pending"),
    Column("captured_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("processed_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("sources_content_hash_idx", sources.c.content_hash, unique=True)


memory_cards = Table(
    "memory_cards",
    metadata,
    Column("id", Text, primary_key=True),
    Column("kind", Text, nullable=False),
    Column("statement", Text, nullable=False),
    Column("summary", Text),
    Column("confidence", Text, nullable=False, default="medium"),
    Column("status", Text, nullable=False, default="current"),
    Column("observed_at", DateTime(timezone=True)),
    Column("source_id", Text, ForeignKey("sources.id")),
    Column("source_quote", Text),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("content_hash", Text, nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("memory_cards_kind_idx", memory_cards.c.kind)
Index("memory_cards_status_idx", memory_cards.c.status)
Index("memory_cards_source_id_idx", memory_cards.c.source_id)
Index("memory_cards_content_hash_idx", memory_cards.c.content_hash, unique=True)


entities = Table(
    "entities",
    metadata,
    Column("id", Text, primary_key=True),
    Column("type", Text, nullable=False),
    Column("canonical_name", Text, nullable=False),
    Column("normalized_name", Text, nullable=False),
    Column("confidence", Text, nullable=False, default="medium"),
    Column("status", Text, nullable=False, default="current"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("entities_type_idx", entities.c.type)
Index("entities_normalized_name_idx", entities.c.normalized_name)


entity_aliases = Table(
    "entity_aliases",
    metadata,
    Column("id", Text, primary_key=True),
    Column("entity_id", Text, ForeignKey("entities.id"), nullable=False),
    Column("alias", Text, nullable=False),
    Column("normalized_alias", Text, nullable=False),
    Column("source_memory_id", Text, ForeignKey("memory_cards.id")),
    Column("confidence", Text, nullable=False, default="medium"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("entity_id", "normalized_alias", name="entity_aliases_entity_alias_uq"),
)
Index("entity_aliases_entity_id_idx", entity_aliases.c.entity_id)
Index("entity_aliases_normalized_alias_idx", entity_aliases.c.normalized_alias)


memory_entities = Table(
    "memory_entities",
    metadata,
    Column("memory_id", Text, ForeignKey("memory_cards.id"), primary_key=True),
    Column("entity_id", Text, ForeignKey("entities.id"), primary_key=True),
    Column("role", Text, primary_key=True),
    Column("confidence", Text, nullable=False, default="medium"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("memory_entities_entity_id_idx", memory_entities.c.entity_id)
Index("memory_entities_memory_id_idx", memory_entities.c.memory_id)


relationships = Table(
    "relationships",
    metadata,
    Column("id", Text, primary_key=True),
    Column("subject_entity_id", Text, ForeignKey("entities.id"), nullable=False),
    Column("predicate", Text, nullable=False),
    Column("object_entity_id", Text, ForeignKey("entities.id"), nullable=False),
    Column("evidence_memory_id", Text, ForeignKey("memory_cards.id")),
    Column("confidence", Text, nullable=False, default="medium"),
    Column("status", Text, nullable=False, default="current"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "subject_entity_id",
        "predicate",
        "object_entity_id",
        "evidence_memory_id",
        name="relationships_evidence_uq",
    ),
)
Index("relationships_subject_idx", relationships.c.subject_entity_id)
Index("relationships_object_idx", relationships.c.object_entity_id)
Index("relationships_predicate_idx", relationships.c.predicate)


memory_links = Table(
    "memory_links",
    metadata,
    Column("id", Text, primary_key=True),
    Column("from_memory_id", Text, ForeignKey("memory_cards.id"), nullable=False),
    Column("relation", Text, nullable=False),
    Column("to_memory_id", Text, ForeignKey("memory_cards.id"), nullable=False),
    Column("confidence", Text, nullable=False, default="medium"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "from_memory_id",
        "relation",
        "to_memory_id",
        name="memory_links_relation_uq",
    ),
)
Index("memory_links_from_idx", memory_links.c.from_memory_id)
Index("memory_links_to_idx", memory_links.c.to_memory_id)
Index("memory_links_relation_idx", memory_links.c.relation)


open_loops = Table(
    "open_loops",
    metadata,
    Column("id", Text, primary_key=True),
    Column("memory_id", Text, ForeignKey("memory_cards.id"), nullable=False),
    Column("status", Text, nullable=False, default="open"),
    Column("priority", Text, nullable=False, default="normal"),
    Column("next_review_at", DateTime(timezone=True)),
    Column("last_reminded_at", DateTime(timezone=True)),
    Column("reminder_policy", Text),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("memory_id", name="open_loops_memory_uq"),
)
Index("open_loops_status_idx", open_loops.c.status)
Index("open_loops_next_review_idx", open_loops.c.next_review_at)


cognee_sync = Table(
    "cognee_sync",
    metadata,
    Column("id", Text, primary_key=True),
    Column("object_type", Text, nullable=False),
    Column("object_id", Text, nullable=False),
    Column("dataset", Text, nullable=False),
    Column("projection_hash", Text, nullable=False),
    Column("cognee_reference", Text),
    Column("status", Text, nullable=False, default="pending"),
    Column("last_synced_at", DateTime(timezone=True)),
    Column("error_message", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("object_type", "object_id", "dataset", name="cognee_sync_object_dataset_idx"),
)


ingestion_runs = Table(
    "ingestion_runs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("input_type", Text, nullable=False),
    Column("input_hash", Text, nullable=False),
    Column("raw_input_preview", Text),
    Column("status", Text, nullable=False, default="started"),
    Column("source_id", Text, ForeignKey("sources.id")),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("error_message", Text),
    Column("started_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("finished_at", DateTime(timezone=True)),
)
Index("ingestion_runs_status_idx", ingestion_runs.c.status)
Index("ingestion_runs_input_hash_idx", ingestion_runs.c.input_hash)


recall_logs = Table(
    "recall_logs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("query", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("retrieved_memory_ids", JSON, nullable=False, default=list),
    Column("retrieved_source_ids", JSON, nullable=False, default=list),
    Column("answer_preview", Text),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
