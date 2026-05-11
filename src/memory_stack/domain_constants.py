from __future__ import annotations


INPUT_TYPES = (
    "auto",
    "note",
    "fact",
    "thought",
    "person_interaction",
    "open_question",
    "research_question",
    "chat_conclusion",
    "table",
)

SOURCE_KINDS = (
    "auto",
    "article",
    "transcript",
    "markdown",
    "pdf",
    "email",
    "table",
    "chat_log",
    "other",
)

RECALL_MODES = ("auto", "evidence", "profile", "open_loops", "sources", "memories", "debug")
ENTITY_TYPES = ("auto", "person", "organization", "place", "concept", "project", "artifact")
OPEN_LOOP_STATUSES = ("open", "parked", "in_progress", "closed", "archived", "any")
CONFLICT_ACTIONS = (
    "supersede",
    "keep_both",
    "mark_duplicate",
    "archive_old",
    "reject_new",
    "mark_contradiction",
)
FORGET_OBJECT_TYPES = ("memory", "source", "entity", "relationship", "open_loop")
ADMIN_COGNEE_OBJECT_TYPES = ("memory", "source", "data", "all")
ADMIN_COGNEE_DATASETS = ("memory", "sources", "data", "all")

SLACK_PROPOSAL_INPUT_TYPES = (
    "auto",
    "fact",
    "note",
    "person_interaction",
    "open_question",
    "research_question",
    "chat_conclusion",
    "table",
)
SLACK_SOURCE_POLICIES = ("memory_only", "source_and_memory")
CONFIDENCE_VALUES = ("low", "medium", "high")
