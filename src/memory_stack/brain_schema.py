from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Float,
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    func,
)

metadata = MetaData()


brain_users = Table(
    "brain_users",
    metadata,
    Column("id", Text, primary_key=True),
    Column("display_name", Text),
    Column("email", Text),
    Column("status", Text, nullable=False, default="active"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("brain_users_status_idx", brain_users.c.status)


sources = Table(
    "sources",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("sources_user_created_idx", sources.c.user_id, sources.c.created_at)


memory_cards = Table(
    "memory_cards",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("memory_cards_user_created_idx", memory_cards.c.user_id, memory_cards.c.created_at)


entities = Table(
    "entities",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("entities_user_name_idx", entities.c.user_id, entities.c.type, entities.c.normalized_name)


entity_aliases = Table(
    "entity_aliases",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("entity_aliases_user_alias_idx", entity_aliases.c.user_id, entity_aliases.c.normalized_alias)


memory_entities = Table(
    "memory_entities",
    metadata,
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("relationships_user_status_idx", relationships.c.user_id, relationships.c.status)


memory_links = Table(
    "memory_links",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("memory_links_user_relation_idx", memory_links.c.user_id, memory_links.c.relation)


open_loops = Table(
    "open_loops",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("open_loops_user_status_idx", open_loops.c.user_id, open_loops.c.status)


cognee_sync = Table(
    "cognee_sync",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
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
Index("ingestion_runs_user_started_idx", ingestion_runs.c.user_id, ingestion_runs.c.started_at)


recall_logs = Table(
    "recall_logs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("query", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("retrieved_memory_ids", JSON, nullable=False, default=list),
    Column("retrieved_source_ids", JSON, nullable=False, default=list),
    Column("answer_preview", Text),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


app_write_audit = Table(
    "app_write_audit",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("tool_name", Text, nullable=False),
    Column("client_id", Text),
    Column("subject", Text),
    Column("request_id", Text),
    Column("target_id", Text),
    Column("status", Text, nullable=False),
    Column("confirmed_by_user", Integer, nullable=False, default=0),
    Column("summary", Text),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("app_write_audit_tool_idx", app_write_audit.c.tool_name)
Index("app_write_audit_status_idx", app_write_audit.c.status)
Index("app_write_audit_created_idx", app_write_audit.c.created_at)
Index("app_write_audit_user_created_idx", app_write_audit.c.user_id, app_write_audit.c.created_at)


taste_items = Table(
    "taste_items",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("brain_entity_id", Text, ForeignKey("entities.id"), nullable=False),
    Column("type", Text, nullable=False),
    Column("canonical_name", Text, nullable=False),
    Column("normalized_name", Text, nullable=False),
    Column("source_text", Text),
    Column("notes", Text),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("enrichment_metadata_json", JSON, nullable=False, default=dict),
    Column("enrichment_status", Text, nullable=False, default="not_attempted"),
    Column("status", Text, nullable=False, default="current"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "type IN ('wine','restaurant','music','cigar','experience','movie','series')",
        name="taste_items_type_ck",
    ),
    CheckConstraint(
        "status IN ('current','deleted')",
        name="taste_items_status_ck",
    ),
)
Index("taste_items_entity_idx", taste_items.c.brain_entity_id)
Index("taste_items_type_idx", taste_items.c.type)
Index("taste_items_normalized_name_idx", taste_items.c.normalized_name)
Index("taste_items_status_idx", taste_items.c.status)
Index("taste_items_user_name_idx", taste_items.c.user_id, taste_items.c.type, taste_items.c.normalized_name)


taste_attributes = Table(
    "taste_attributes",
    metadata,
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("taste_item_id", Text, ForeignKey("taste_items.id"), primary_key=True),
    Column("key", Text, primary_key=True),
    Column("value", Float, nullable=False),
    Column("lower_95", Float, nullable=False),
    Column("upper_95", Float, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("value >= 0 AND value <= 1", name="taste_attributes_value_01_ck"),
    CheckConstraint("lower_95 >= 0 AND lower_95 <= 1", name="taste_attributes_lower_01_ck"),
    CheckConstraint("upper_95 >= 0 AND upper_95 <= 1", name="taste_attributes_upper_01_ck"),
    CheckConstraint("lower_95 <= value", name="taste_attributes_lower_le_value_ck"),
    CheckConstraint("value <= upper_95", name="taste_attributes_value_le_upper_ck"),
)
Index("taste_attributes_key_idx", taste_attributes.c.key)


taste_signals = Table(
    "taste_signals",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("taste_item_id", Text, ForeignKey("taste_items.id"), nullable=False),
    Column("signal_type", Text, nullable=False),
    Column("value_json", JSON, nullable=False),
    Column("provenance_memory_id", Text, ForeignKey("memory_cards.id")),
    Column("provenance_entity_id", Text, ForeignKey("entities.id")),
    Column("source", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "signal_type IN ("
        "'rating','tried','watched','listened','wanted_to_try','wanted_to_watch',"
        "'wanted_to_listen','recommended_by','disliked','avoid','not_my_style',"
        "'bad_fit','rejected_option'"
        ")",
        name="taste_signals_type_ck",
    ),
)
Index("taste_signals_item_idx", taste_signals.c.taste_item_id)
Index("taste_signals_type_idx", taste_signals.c.signal_type)


taste_decisions = Table(
    "taste_decisions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("query", Text, nullable=False),
    Column("context_json", JSON, nullable=False, default=dict),
    Column("options_json", JSON, nullable=False, default=list),
    Column("ranked_json", JSON, nullable=False, default=list),
    Column("chosen_taste_item_id", Text, ForeignKey("taste_items.id")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("taste_decisions_chosen_idx", taste_decisions.c.chosen_taste_item_id)


taste_proposals = Table(
    "taste_proposals",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("original_text", Text, nullable=False),
    Column("proposal_json", JSON, nullable=False),
    Column("warnings_json", JSON, nullable=False, default=list),
    Column("source_metadata_json", JSON, nullable=False, default=dict),
    Column("status", Text, nullable=False),
    Column("correction_count", Integer, nullable=False, default=0),
    Column("last_correction_text", Text),
    Column("last_corrected_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "status IN ('pending','confirmed','cancelled','expired','superseded')",
        name="taste_proposals_status_ck",
    ),
)
Index("taste_proposals_status_idx", taste_proposals.c.status)
Index("taste_proposals_expires_idx", taste_proposals.c.expires_at)
