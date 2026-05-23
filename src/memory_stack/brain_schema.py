from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
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
    Column("confidence", Text, nullable=False, default="medium"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("entity_id", "normalized_alias", name="entity_aliases_entity_alias_uq"),
)
Index("entity_aliases_entity_id_idx", entity_aliases.c.entity_id)
Index("entity_aliases_normalized_alias_idx", entity_aliases.c.normalized_alias)
Index("entity_aliases_user_alias_idx", entity_aliases.c.user_id, entity_aliases.c.normalized_alias)


brain_session_maps = Table(
    "brain_session_maps",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("profile_name", Text, nullable=False),
    Column("surface", Text, nullable=False),
    Column("client_session_id", Text, nullable=False),
    Column("cognee_session_id", Text, nullable=False),
    Column("cognee_dataset", Text, nullable=False),
    Column("node_sets_json", JSON, nullable=False, default=list),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("last_used_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "user_id",
        "profile_name",
        "surface",
        "client_session_id",
        name="brain_session_maps_user_profile_surface_client_uq",
    ),
)
Index("brain_session_maps_cognee_session_idx", brain_session_maps.c.cognee_session_id)
Index("brain_session_maps_user_last_used_idx", brain_session_maps.c.user_id, brain_session_maps.c.last_used_at)


brain_external_receipts = Table(
    "brain_external_receipts",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("surface", Text, nullable=False),
    Column("tool_name", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("summary", Text),
    Column("cognee_dataset", Text),
    Column("cognee_reference", Text),
    Column("cognee_result_json", JSON, nullable=False, default=dict),
    Column("warnings_json", JSON, nullable=False, default=list),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("brain_external_receipts_user_created_idx", brain_external_receipts.c.user_id, brain_external_receipts.c.created_at)
Index("brain_external_receipts_status_idx", brain_external_receipts.c.status)
Index("brain_external_receipts_action_idx", brain_external_receipts.c.action)
Index("brain_external_receipts_cognee_reference_idx", brain_external_receipts.c.cognee_reference)


brain_pending_confirmations = Table(
    "brain_pending_confirmations",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("surface", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("original_input", Text, nullable=False),
    Column("proposed_payload_json", JSON, nullable=False, default=dict),
    Column("reason", Text),
    Column("options_json", JSON, nullable=False, default=list),
    Column("status", Text, nullable=False, default="pending"),
    Column("expires_at", DateTime(timezone=True)),
    Column("confirmed_at", DateTime(timezone=True)),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "status IN ('pending','confirmed','cancelled','expired','rejected')",
        name="brain_pending_confirmations_status_ck",
    ),
)
Index("brain_pending_confirmations_user_status_idx", brain_pending_confirmations.c.user_id, brain_pending_confirmations.c.status)
Index("brain_pending_confirmations_expires_idx", brain_pending_confirmations.c.expires_at)


brain_context_records = Table(
    "brain_context_records",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, default="default", server_default="default"),
    Column("kind", Text, nullable=False),
    Column("statement", Text, nullable=False),
    Column("scope", Text, nullable=False, default="profile", server_default="profile"),
    Column("source", Text),
    Column("status", Text, nullable=False, default="current"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("cognee_reference", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("kind IN ('profile','bias')", name="brain_context_records_kind_ck"),
    CheckConstraint(
        "status IN ('current','deleted','archived','superseded')",
        name="brain_context_records_status_ck",
    ),
)
Index("brain_context_records_user_kind_status_idx", brain_context_records.c.user_id, brain_context_records.c.kind, brain_context_records.c.status)
Index("brain_context_records_scope_idx", brain_context_records.c.scope)
Index("brain_context_records_cognee_reference_idx", brain_context_records.c.cognee_reference)


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
