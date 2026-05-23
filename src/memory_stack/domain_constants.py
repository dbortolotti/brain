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

RECALL_MODES = ("auto", "evidence", "profile", "memories", "debug")
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
FORGET_OBJECT_TYPES = ("cognee_remember", "entity")
ADMIN_COGNEE_OBJECT_TYPES = ("memory", "source", "data", "all")
ADMIN_COGNEE_DATASETS = ("memory", "data", "all")
COGNEE_IMPROVE_DATASETS = ("memory", "data", "palate")

CONFIDENCE_VALUES = ("low", "medium", "high")
