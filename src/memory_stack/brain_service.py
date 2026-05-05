from __future__ import annotations

import re
from typing import Any

from memory_stack.brain_models import (
    EntityMention,
    EntityReceipt,
    IngestionReceipt,
    MemoryCandidate,
    MemoryReceipt,
    RecallRequest,
    RecallResponse,
    RelationshipCandidate,
    RememberRequest,
    SourceCandidate,
    SourceReceipt,
)
from memory_stack.brain_store import BrainStore, content_hash, stable_id
from memory_stack.config import Settings


FAMILY_TWINS_RE = re.compile(
    r"^(?P<first>[A-Z][A-Za-z'-]+)\s+and\s+(?P<second>[A-Z][A-Za-z'-]+)\s+are\s+my\s+twin\s+daughters?\.?$",
    re.IGNORECASE,
)
PERSON_INTERACTION_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z'-]+)\s+(?:from|at)\s+(?P<org>[A-Z][A-Za-z0-9& .'-]+?)\s+"
    r"mentioned\s+that\s+(?:he|she|they)\s+likes?\s+(?P<liked>[^.]+)\.?$",
    re.IGNORECASE,
)
LEARN_MORE_RE = re.compile(
    r"^I\s+(?:would\s+)?(?:like|want)\s+to\s+learn\s+more\s+about\s+(?P<topic>[^.]+)\.?$",
    re.IGNORECASE,
)
WONDER_RE = re.compile(
    r"^I\s+wonder\s+(?P<question>.+?)(?:\.?\s+Need\s+to\s+research\s+this\.?)?$",
    re.IGNORECASE | re.DOTALL,
)


def slug(value: str) -> str:
    return "_".join(re.findall(r"[a-z0-9]+", value.casefold()))


def compact_statement(value: str) -> str:
    return " ".join(value.strip().split())


class CompiledInput:
    def __init__(
        self,
        *,
        classification: str,
        source: SourceCandidate | None,
        memory_cards: list[MemoryCandidate],
    ) -> None:
        self.classification = classification
        self.source = source
        self.memory_cards = memory_cards


def compile_input(request: RememberRequest, settings: Settings) -> CompiledInput:
    text = compact_statement(request.input)
    input_type = request.input_type if request.input_type != "auto" else classify_input(text)
    source = source_for_input(text, input_type, request.source_policy)
    if request.source_policy == "source_only":
        return CompiledInput(classification=input_type, source=source, memory_cards=[])

    if input_type == "family_fact":
        cards = [compile_family_fact(text, request, settings)]
    elif input_type == "person_interaction":
        cards = [compile_person_interaction(text, request)]
    elif input_type == "open_question":
        cards = [compile_open_question(text, request, settings)]
    elif input_type == "research_question":
        cards = [compile_research_question(text, request, settings)]
    elif input_type in {"article_url", "article"}:
        cards = [compile_article_note(text, request)]
    elif input_type == "table":
        cards = [compile_table_note(text, request)]
    elif input_type in {"chat_summary", "chat_conclusion"}:
        cards = [compile_chat_conclusion(text, request)]
    elif input_type in {"transcript", "markdown", "source_text"}:
        cards = [compile_source_summary(text, request)]
    else:
        cards = [compile_basic_memory(text, request)]

    if source is not None:
        cards = [
            card.model_copy(update={"source_quote": card.source_quote or text[:500]})
            for card in cards
        ]
    return CompiledInput(classification=input_type, source=source, memory_cards=cards)


def classify_input(text: str) -> str:
    if FAMILY_TWINS_RE.match(text):
        return "family_fact"
    if PERSON_INTERACTION_RE.match(text):
        return "person_interaction"
    if LEARN_MORE_RE.match(text):
        return "open_question"
    if WONDER_RE.match(text) and "research" in text.casefold():
        return "research_question"
    if text.startswith(("http://", "https://")):
        return "article_url"
    if "\n|" in text or text.count(",") >= 4 and "\n" in text:
        return "table"
    if len(text) > 1200 or text.startswith("#"):
        return "source_text"
    if "concluded" in text.casefold() or "should use" in text.casefold():
        return "chat_conclusion"
    return "basic_fact"


def source_for_input(text: str, input_type: str, source_policy: str) -> SourceCandidate | None:
    if source_policy == "memory_only":
        return None
    if input_type == "article_url":
        return SourceCandidate(
            kind="article",
            title=text,
            uri=text,
            raw_text=text,
            summary=f"Saved article URL: {text}",
            metadata={"capture_note": "URL captured; article fetching is not implemented yet."},
        )
    if input_type in {"article", "transcript", "markdown", "source_text", "table"}:
        return SourceCandidate(
            kind="table" if input_type == "table" else input_type,
            raw_text=text,
            summary=text[:500],
        )
    if source_policy == "source_and_memory":
        return SourceCandidate(kind="manual_note", raw_text=text, summary=text[:500])
    return None


def compile_family_fact(
    text: str,
    request: RememberRequest,
    settings: Settings,
) -> MemoryCandidate:
    match = FAMILY_TWINS_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    first = match.group("first")
    second = match.group("second")
    owner = settings.brain_owner_name
    statement = f"{first} and {second} are {owner}'s twin daughters."
    return MemoryCandidate(
        kind="family_fact",
        statement=statement,
        summary=f"{first} and {second} are twin daughters of {owner}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": ["family"]},
        entities=[
            EntityMention(name=owner, type="person", role="parent", confidence="high"),
            EntityMention(name=first, type="person", role="child", confidence="high"),
            EntityMention(name=second, type="person", role="child", confidence="high"),
        ],
        relationships=[
            RelationshipCandidate(
                subject=first,
                predicate="daughter_of",
                object=owner,
                confidence="high",
            ),
            RelationshipCandidate(
                subject=second,
                predicate="daughter_of",
                object=owner,
                confidence="high",
            ),
            RelationshipCandidate(subject=first, predicate="twin_of", object=second, confidence="high"),
            RelationshipCandidate(subject=second, predicate="twin_of", object=first, confidence="high"),
        ],
    )


def compile_person_interaction(text: str, request: RememberRequest) -> MemoryCandidate:
    match = PERSON_INTERACTION_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    person = match.group("person").strip()
    org = match.group("org").strip()
    liked = match.group("liked").strip()
    person_alias = f"{person} from {org}"
    topics = infer_topics(liked)
    return MemoryCandidate(
        kind="person_interaction",
        statement=text,
        summary=f"{person_alias} likes {liked}.",
        confidence="medium",
        observed_at=request.observed_at,
        metadata={"topics": topics},
        entities=[
            EntityMention(name=person_alias, type="person", role="subject", alias=person),
            EntityMention(name=org, type="organization", role="affiliation_context"),
            EntityMention(name=liked, type=infer_entity_type(liked), role="topic"),
        ],
        relationships=[
            RelationshipCandidate(subject=person_alias, predicate="associated_with", object=org),
            RelationshipCandidate(subject=person_alias, predicate="likes", object=liked),
        ],
    )


def compile_open_question(
    text: str,
    request: RememberRequest,
    settings: Settings,
) -> MemoryCandidate:
    match = LEARN_MORE_RE.match(text)
    topic = match.group("topic").strip() if match else text
    topics = [slug(topic)]
    return MemoryCandidate(
        kind="open_question",
        statement=f"{settings.brain_owner_name} wants to learn more about {topic}.",
        summary=f"Learn more about {topic}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": topics},
        entities=[EntityMention(name=topic, type="concept", role="topic")],
        open_loop={
            "status": "open",
            "priority": "normal",
            "reminder_policy": "opportunistic_or_weekly",
        },
    )


def compile_research_question(
    text: str,
    request: RememberRequest,
    settings: Settings,
) -> MemoryCandidate:
    match = WONDER_RE.match(text)
    question = compact_statement(match.group("question")) if match else text
    statement = f"{settings.brain_owner_name} wants to research: {question.rstrip('?')}?"
    topics = infer_topics(question)
    return MemoryCandidate(
        kind="research_question",
        statement=statement,
        summary=question,
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": topics},
        open_loop={
            "status": "open",
            "priority": "normal",
            "reminder_policy": "opportunistic_or_weekly",
        },
    )


def compile_article_note(text: str, request: RememberRequest) -> MemoryCandidate:
    topics = infer_topics(f"{text} {request.context.get('user_note', '')}")
    return MemoryCandidate(
        kind="article_note",
        statement=f"Saved article for later recall: {text}",
        summary=f"Saved article: {text}",
        confidence="medium",
        observed_at=request.observed_at,
        metadata={"topics": topics, "why_saved": request.context.get("user_note")},
    )


def compile_table_note(text: str, request: RememberRequest) -> MemoryCandidate:
    first_line = text.splitlines()[0] if text.splitlines() else "table"
    return MemoryCandidate(
        kind="table_note",
        statement=f"Stored a small table: {first_line[:160]}",
        summary=text[:500],
        confidence="medium",
        observed_at=request.observed_at,
        metadata={"topics": infer_topics(text)},
    )


def compile_chat_conclusion(text: str, request: RememberRequest) -> MemoryCandidate:
    return MemoryCandidate(
        kind="chat_conclusion",
        statement=text,
        summary=text[:300],
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": infer_topics(text)},
    )


def compile_source_summary(text: str, request: RememberRequest) -> MemoryCandidate:
    return MemoryCandidate(
        kind="source_summary",
        statement=f"Stored source material: {text[:220]}",
        summary=text[:500],
        confidence="medium",
        observed_at=request.observed_at,
        metadata={"topics": infer_topics(text)},
    )


def compile_basic_memory(text: str, request: RememberRequest) -> MemoryCandidate:
    kind = "idea" if text.endswith("?") else "basic_fact"
    return MemoryCandidate(
        kind=kind,
        statement=text,
        summary=text[:300],
        confidence="high" if request.input_type in {"fact", "note", "auto"} else "medium",
        observed_at=request.observed_at,
        metadata={"topics": infer_topics(text)},
    )


def infer_entity_type(value: str) -> str:
    words = value.split()
    if len(words) >= 2 and all(word[:1].isupper() for word in words):
        return "person"
    return "concept"


def infer_topics(text: str) -> list[str]:
    lower = text.casefold()
    topics: list[str] = []
    topic_map = {
        "knowledge graph": "knowledge_graphs",
        "ai memory": "ai_memory",
        "cognee": "cognee",
        "brain": "brain",
        "bill evans": "jazz",
        "coltrane": "jazz",
        "jazz": "jazz",
        "language": "language",
        "intelligence": "intelligence",
    }
    for needle, topic in topic_map.items():
        if needle in lower and topic not in topics:
            topics.append(topic)
    return topics


def remember(request: RememberRequest, settings: Settings) -> IngestionReceipt:
    compiled = compile_input(request, settings)
    input_hash = content_hash(request.input, request.input_type, request.context)
    run_id = stable_id("dry_ing", input_hash)
    if request.dry_run:
        return IngestionReceipt(
            ingestion_run_id=run_id,
            classification=compiled.classification,
            source=SourceReceipt(created=compiled.source is not None, source_id=None),
            memory_cards=[
                MemoryReceipt(
                    id=stable_id("dry_mem", card.kind, card.statement),
                    kind=str(card.kind),
                    statement=card.statement,
                    status=card.status,
                    created=False,
                )
                for card in compiled.memory_cards
            ],
            dry_run=True,
        )

    store = BrainStore(settings)
    run = store.create_ingestion_run(
        input_type=compiled.classification,
        input_hash=input_hash,
        raw_input_preview=request.input,
        metadata_json={"context": request.context, "source_policy": request.source_policy},
    )
    source_id = None
    source_created = False
    try:
        if compiled.source is not None:
            source, source_created = store.upsert_source(
                {
                    "kind": compiled.source.kind,
                    "title": compiled.source.title,
                    "uri": compiled.source.uri,
                    "file_path": compiled.source.file_path,
                    "raw_text": compiled.source.raw_text,
                    "summary": compiled.source.summary,
                    "metadata_json": compiled.source.metadata,
                    "status": compiled.source.status,
                }
            )
            source_id = source["id"]

        receipt = IngestionReceipt(
            ingestion_run_id=run["id"],
            classification=compiled.classification,
            source=SourceReceipt(created=source_created, source_id=source_id),
        )
        entity_receipts: dict[str, dict[str, Any]] = {}
        for card in compiled.memory_cards:
            memory, memory_created = store.upsert_memory_card(
                {
                    "kind": str(card.kind),
                    "statement": card.statement,
                    "summary": card.summary,
                    "confidence": card.confidence,
                    "status": card.status,
                    "observed_at": card.observed_at,
                    "source_id": source_id,
                    "source_quote": card.source_quote,
                    "metadata_json": card.metadata,
                }
            )
            receipt.memory_cards.append(
                MemoryReceipt(
                    id=memory["id"],
                    kind=memory["kind"],
                    statement=memory["statement"],
                    status=memory["status"],
                    created=memory_created,
                )
            )
            entity_map: dict[str, dict[str, Any]] = {}
            for mention in card.entities:
                aliases = [mention.alias] if mention.alias else []
                entity, entity_created = store.upsert_entity(
                    entity_type=mention.type,
                    canonical_name=mention.name,
                    aliases=aliases,
                    confidence=mention.confidence,
                    metadata_json=mention.metadata,
                )
                entity_map[mention.name] = entity
                if mention.alias:
                    entity_map[mention.alias] = entity
                entity_receipts[entity["id"]] = {
                    "id": entity["id"],
                    "canonical_name": entity["canonical_name"],
                    "type": entity["type"],
                    "created": entity_created,
                }
                store.link_memory_entity(
                    memory_id=memory["id"],
                    entity_id=entity["id"],
                    role=mention.role,
                    confidence=mention.confidence,
                )

            for relationship in card.relationships:
                subject = entity_map.get(relationship.subject)
                object_ = entity_map.get(relationship.object)
                if subject is None:
                    subject, _ = store.upsert_entity(
                        entity_type="concept",
                        canonical_name=relationship.subject,
                    )
                if object_ is None:
                    object_, _ = store.upsert_entity(
                        entity_type="concept",
                        canonical_name=relationship.object,
                    )
                rel, rel_created = store.create_relationship(
                    subject_entity_id=subject["id"],
                    predicate=relationship.predicate,
                    object_entity_id=object_["id"],
                    evidence_memory_id=memory["id"],
                    confidence=relationship.confidence,
                    status=relationship.status,
                    metadata_json=relationship.metadata,
                )
                receipt.relationships.append({**rel, "created": rel_created})

            if card.open_loop is not None:
                loop, loop_created = store.create_open_loop(
                    memory_id=memory["id"],
                    status=card.open_loop.get("status", "open"),
                    priority=card.open_loop.get("priority", "normal"),
                    reminder_policy=card.open_loop.get("reminder_policy"),
                    metadata_json={k: v for k, v in card.open_loop.items() if k not in {"status", "priority", "reminder_policy"}},
                )
                receipt.open_loops.append({**loop, "created": loop_created})

            projection_hash = content_hash(memory["id"], memory["statement"], memory["status"])
            store.mark_cognee_pending(
                object_type="memory",
                object_id=memory["id"],
                dataset="memory",
                projection_hash=projection_hash,
            )

        receipt.entities = [
            EntityReceipt(
                id=value["id"],
                canonical_name=value["canonical_name"],
                type=value["type"],
                created=value["created"],
            )
            for value in entity_receipts.values()
        ]
        store.finish_ingestion_run(run["id"], status="processed", source_id=source_id)
        return IngestionReceipt.model_validate(receipt)
    except Exception as exc:
        store.finish_ingestion_run(run["id"], status="failed", error_message=str(exc))
        raise


def recall(request: RecallRequest, settings: Settings) -> RecallResponse:
    store = BrainStore(settings)
    query = request.query.strip()
    mode = request.mode if request.mode != "auto" else infer_recall_mode(query)
    if mode == "profile":
        name = extract_profile_name(query)
        profile = build_profile_response(name, settings, include_superseded=request.include_superseded)
        if profile is not None:
            store.log_recall(
                query=query,
                mode=mode,
                retrieved_memory_ids=[fact["memory_id"] for fact in profile.facts if "memory_id" in fact],
                retrieved_source_ids=[],
                answer_preview=profile.answer,
            )
            return profile
    if mode == "open_loops":
        loops = store.list_open_loops(limit=request.limit)
        answer = render_open_loops(loops)
        response = RecallResponse(answer=answer, open_loops=loops)
        store.log_recall(
            query=query,
            mode=mode,
            retrieved_memory_ids=[loop["memory_id"] for loop in loops],
            retrieved_source_ids=[],
            answer_preview=answer,
        )
        return response

    memories = store.search_memory(
        query,
        include_superseded=request.include_superseded,
        limit=request.limit,
    )
    facts = [
        {
            "memory_id": memory["id"],
            "kind": memory["kind"],
            "statement": memory["statement"],
            "status": memory["status"],
            "confidence": memory["confidence"],
        }
        for memory in memories
    ]
    evidence = [
        {
            "memory_id": memory["id"],
            "source_id": memory.get("source_id"),
            "quote": memory.get("source_quote") or memory["statement"],
        }
        for memory in memories
    ]
    answer = render_memory_answer(memories)
    store.log_recall(
        query=query,
        mode=mode,
        retrieved_memory_ids=[memory["id"] for memory in memories],
        retrieved_source_ids=[memory["source_id"] for memory in memories if memory.get("source_id")],
        answer_preview=answer,
    )
    return RecallResponse(answer=answer, facts=facts, evidence=evidence)


def infer_recall_mode(query: str) -> str:
    lower = query.casefold()
    if "open question" in lower or "open idea" in lower or "open loops" in lower:
        return "open_loops"
    if lower.startswith(("tell me everything about ", "tell me about ", "what do i know about ")):
        return "profile"
    return "memories"


def extract_profile_name(query: str) -> str:
    lower = query.casefold()
    prefixes = [
        "tell me everything about ",
        "tell me about ",
        "what do i know about ",
    ]
    for prefix in prefixes:
        if lower.startswith(prefix):
            return query[len(prefix) :].strip(" ?.")
    return query.strip(" ?.")


def build_profile_response(
    name: str,
    settings: Settings,
    *,
    entity_type: str | None = None,
    include_superseded: bool = False,
) -> RecallResponse | None:
    store = BrainStore(settings)
    profile = store.entity_profile(
        name,
        entity_type=entity_type,
        include_superseded=include_superseded,
    )
    if profile is None:
        return None

    entity = profile["entity"]
    memories = profile["memories"]
    relationships = profile["relationships"]
    facts = [
        {
            "memory_id": memory["id"],
            "kind": memory["kind"],
            "statement": memory["statement"],
            "status": memory["status"],
            "confidence": memory["confidence"],
        }
        for memory in memories
    ]
    evidence = [
        {
            "memory_id": memory["id"],
            "source_id": memory.get("source_id"),
            "quote": memory.get("source_quote") or memory["statement"],
        }
        for memory in memories
    ]
    lines = [entity["canonical_name"], "Identity"]
    lines.append(f"- {entity['type']}; confidence {entity['confidence']}.")
    if profile["aliases"]:
        alias_names = sorted({alias["alias"] for alias in profile["aliases"]})
        lines.append(f"- Aliases: {', '.join(alias_names)}.")
    lines.append("Known facts")
    known = [memory for memory in memories if memory["kind"] not in {"person_interaction", "open_question"}]
    lines.extend([f"- {memory['statement']} [{memory['id']}]" for memory in known] or ["- None known."])
    lines.append("Interactions")
    interactions = [memory for memory in memories if memory["kind"] == "person_interaction"]
    lines.extend(
        [f"- {memory['statement']} [{memory['id']}]" for memory in interactions] or ["- None known."]
    )
    lines.append("Relationships")
    lines.extend(
        [
            f"- {relationship['predicate']} {relationship['other_name']} "
            f"[evidence: {relationship['evidence_memory_id']}]"
            for relationship in relationships
        ]
        or ["- None known."]
    )
    lines.append("Open loops")
    lines.extend(
        [f"- {loop['statement']} [{loop['memory_id']}]" for loop in profile["open_loops"]]
        or ["- None known."]
    )
    lines.append("Conflicts / uncertainties")
    lines.append("- No conflicts recorded.")
    return RecallResponse(answer="\n".join(lines), facts=facts, evidence=evidence)


def render_open_loops(loops: list[dict[str, Any]]) -> str:
    if not loops:
        return "No open loops found."
    lines = ["Open loops"]
    for loop in loops:
        lines.append(f"- {loop['statement']} [{loop['memory_id']}]")
    return "\n".join(lines)


def render_memory_answer(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return "No matching memories found."
    lines = ["Known memories"]
    for memory in memories:
        lines.append(
            f"- {memory['statement']} "
            f"[{memory['id']}; {memory['kind']}; {memory['confidence']}]"
        )
    return "\n".join(lines)


def get_memory(memory_id: str, settings: Settings) -> dict[str, Any] | None:
    return BrainStore(settings).get_memory(memory_id)


def get_source(
    source_id: str,
    settings: Settings,
    *,
    include_text: bool = False,
    max_chars: int = 10_000,
) -> dict[str, Any] | None:
    return BrainStore(settings).get_source(
        source_id,
        include_text=include_text,
        max_chars=max_chars,
    )


def list_open_loops(
    settings: Settings,
    *,
    topic: str | None = None,
    status: str = "open",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return BrainStore(settings).list_open_loops(topic=topic, status=status, limit=limit)


def profile_entity(
    settings: Settings,
    *,
    name: str,
    entity_type: str | None = None,
    include_superseded: bool = False,
) -> RecallResponse:
    response = build_profile_response(
        name,
        settings,
        entity_type=entity_type,
        include_superseded=include_superseded,
    )
    if response is None:
        return RecallResponse(answer=f"No entity found for {name}.")
    return response


def forget(
    settings: Settings,
    *,
    object_type: str,
    object_id: str,
    hard: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    del reason
    deleted = BrainStore(settings).forget(object_type=object_type, object_id=object_id, hard=hard)
    return {"object_type": object_type, "object_id": object_id, "status": "deleted" if deleted else "not_found"}


def resolve_conflict(
    settings: Settings,
    *,
    conflict_memory_id: str,
    target_memory_id: str,
    action: str,
    note: str | None = None,
) -> dict[str, Any]:
    store = BrainStore(settings)
    if action == "supersede":
        store.update_memory_status(target_memory_id, "superseded")
        store.update_memory_status(conflict_memory_id, "current")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="supersedes",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "keep_both":
        store.update_memory_status(conflict_memory_id, "current")
        store.update_memory_status(target_memory_id, "current")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="contradicts",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "mark_contradiction":
        store.update_memory_status(conflict_memory_id, "current")
        store.update_memory_status(target_memory_id, "current")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="contradicts",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "mark_duplicate":
        store.update_memory_status(conflict_memory_id, "archived")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="duplicates",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "archive_old":
        store.update_memory_status(target_memory_id, "archived")
        return {"action": action, "target_memory_id": target_memory_id, "status": "archived"}
    if action == "reject_new":
        store.update_memory_status(conflict_memory_id, "rejected")
        return {"action": action, "conflict_memory_id": conflict_memory_id, "status": "rejected"}
    raise ValueError(
        "action must be supersede, keep_both, mark_duplicate, archive_old, "
        "reject_new, or mark_contradiction."
    )
