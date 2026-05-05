from __future__ import annotations

import re

from memory_stack.brain_models import (
    EntityMention,
    MemoryCandidate,
    RelationshipCandidate,
    RememberRequest,
    SourceCandidate,
)
from memory_stack.config import Settings
from memory_stack.ingestion.article_loader import load_article
from memory_stack.ingestion.classifier import source_kind_for_input_type
from memory_stack.ingestion.table_parser import parse_table, table_summary
from memory_stack.ingestion.transcript_parser import parse_transcript, transcript_summary


FAMILY_TWINS_RE = re.compile(
    r"^(?P<first>[A-Z][A-Za-z'-]+)\s+and\s+(?P<second>[A-Z][A-Za-z'-]+)\s+are\s+my\s+twin\s+daughters?\.?$",
    re.IGNORECASE,
)
PERSON_INTERACTION_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z'-]+)\s+(?:from|at)\s+(?P<org>[A-Z][A-Za-z0-9& .'-]+?)\s+"
    r"mentioned\s+that\s+(?:he|she|they)\s+likes?\s+(?P<liked>[^.]+)\.?$",
    re.IGNORECASE,
)
PERSON_LIKES_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z'-]+)\s+likes\s+(?P<liked>[^.]+)\.?$",
    re.IGNORECASE,
)
PERSON_LIKES_CORRECTION_RE = re.compile(
    r"^Actually,\s+(?P<person>[A-Z][A-Za-z'-]+)\s+likes\s+(?P<liked>.+?),\s+not\s+(?P<old>[^.]+)\.?$",
    re.IGNORECASE,
)
PERSON_WORKS_AT_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z'-]+)\s+works\s+at\s+(?P<org>[A-Z][A-Za-z0-9& .'-]+?)\.?$",
    re.IGNORECASE,
)
PERSON_LEFT_JOINED_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z'-]+)\s+left\s+(?P<old_org>[A-Z][A-Za-z0-9& .'-]+?)\s+"
    r"and\s+joined\s+(?P<new_org>[A-Z][A-Za-z0-9& .'-]+?)\.?$",
    re.IGNORECASE,
)
PERSON_CHILDREN_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z'-]+)\s+has\s+(?P<count>no|zero|one|two|three|four|five|\d+)\s+children\.?$",
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
        confidence: str = "medium",
        sufficient: bool = False,
    ) -> None:
        self.classification = classification
        self.source = source
        self.memory_cards = memory_cards
        self.confidence = confidence
        self.sufficient = sufficient


def compile_input(request: RememberRequest, settings: Settings) -> CompiledInput:
    raw_text = request.input.strip()
    input_type = request.input_type if request.input_type != "auto" else classify_input(raw_text)
    text = raw_text if preserves_source_structure(input_type) else compact_statement(raw_text)
    source = source_for_input(text, input_type, request.source_policy, request.context)
    if request.source_policy == "source_only":
        return CompiledInput(
            classification=input_type,
            source=source,
            memory_cards=[],
            confidence="high",
            sufficient=True,
        )

    if input_type == "family_fact":
        cards = [compile_family_fact(text, request, settings)]
    elif input_type == "person_interaction":
        cards = [compile_person_interaction(text, request)]
    elif input_type == "preference":
        cards = [compile_person_likes(text, request)]
    elif input_type == "preference_correction":
        cards = [compile_person_likes_correction(text, request)]
    elif input_type == "person_workplace":
        cards = [compile_person_workplace(text, request)]
    elif input_type == "person_transition":
        cards = [compile_person_transition(text, request)]
    elif input_type == "person_family_fact":
        cards = [compile_person_children(text, request)]
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
    return CompiledInput(
        classification=input_type,
        source=source,
        memory_cards=cards,
        confidence=rule_confidence(input_type, cards),
        sufficient=rule_sufficient(input_type),
    )


def classify_input(text: str) -> str:
    if FAMILY_TWINS_RE.match(text):
        return "family_fact"
    if PERSON_INTERACTION_RE.match(text):
        return "person_interaction"
    if PERSON_LIKES_CORRECTION_RE.match(text):
        return "preference_correction"
    if PERSON_LIKES_RE.match(text):
        return "preference"
    if PERSON_LEFT_JOINED_RE.match(text):
        return "person_transition"
    if PERSON_WORKS_AT_RE.match(text):
        return "person_workplace"
    if PERSON_CHILDREN_RE.match(text):
        return "person_family_fact"
    if LEARN_MORE_RE.match(text):
        return "open_question"
    if WONDER_RE.match(text) and "research" in text.casefold():
        return "research_question"
    if text.startswith(("http://", "https://")):
        return "article_url"
    if "\n|" in text or text.count(",") >= 4 and "\n" in text:
        return "table"
    if len(parse_transcript(text).turns) >= 2:
        return "transcript"
    if len(text) > 1200 or text.startswith("#"):
        return "source_text"
    if "concluded" in text.casefold() or "should use" in text.casefold():
        return "chat_conclusion"
    return "basic_fact"


def preserves_source_structure(input_type: str) -> bool:
    return input_type in {
        "article",
        "article_url",
        "transcript",
        "markdown",
        "source_text",
        "table",
    }


def source_for_input(
    text: str,
    input_type: str,
    source_policy: str,
    context: dict[str, object] | None = None,
) -> SourceCandidate | None:
    if source_policy == "memory_only":
        return None

    context = context or {}
    title = string_or_none(context.get("title"))
    why_saved = string_or_none(context.get("why_saved"))
    requested_kind = string_or_none(context.get("source_kind"))
    metadata = dict(context.get("metadata") or {})
    if why_saved:
        metadata["why_saved"] = why_saved

    if input_type == "article_url":
        article = load_article(text, title=title, why_saved=why_saved)
        return SourceCandidate(
            kind="article",
            title=article.title or title or text,
            uri=text,
            raw_text=article.text,
            summary=article.summary or why_saved or f"Saved article URL: {text}",
            metadata={
                **metadata,
                **article.metadata,
            },
            status=article.status,
        )
    if input_type == "transcript":
        parse_result = parse_transcript(text)
        metadata.update(
            {
                "participants": parse_result.participants,
                "turn_count": len(parse_result.turns),
                "parser": parse_result.metadata.get("parser"),
            }
        )
        return SourceCandidate(
            kind="transcript",
            title=title,
            raw_text=text,
            summary=why_saved or transcript_summary(parse_result, text),
            metadata=metadata,
        )
    if input_type == "table":
        table = parse_table(text)
        metadata.update(
            {
                "columns": table.columns,
                "row_count": table.row_count,
                "sample_rows": table.sample_rows,
                "table_kind": table.kind,
            }
        )
        return SourceCandidate(
            kind="table",
            title=title,
            raw_text=text,
            summary=why_saved or table_summary(table),
            metadata=metadata,
        )
    if input_type in {"article", "transcript", "markdown", "source_text", "table"}:
        return SourceCandidate(
            kind=source_kind_for_input_type(input_type, requested_kind),
            title=title,
            raw_text=text,
            summary=why_saved or text[:500],
            metadata=metadata,
        )
    if source_policy == "source_and_memory":
        return SourceCandidate(
            kind="manual_note",
            title=title,
            raw_text=text,
            summary=why_saved or text[:500],
            metadata=metadata,
        )
    return None


def string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def rule_confidence(input_type: str, cards: list[MemoryCandidate]) -> str:
    if input_type in {
        "family_fact",
        "open_question",
        "research_question",
        "preference",
        "preference_correction",
        "person_workplace",
        "person_transition",
        "person_family_fact",
    }:
        return "high"
    if input_type == "person_interaction":
        return "high"
    if cards and all(card.confidence == "high" for card in cards):
        return "high"
    return "medium"


def rule_sufficient(input_type: str) -> bool:
    return input_type in {
        "family_fact",
        "person_interaction",
        "open_question",
        "research_question",
        "basic_fact",
        "chat_conclusion",
        "preference",
        "preference_correction",
        "person_workplace",
        "person_transition",
        "person_family_fact",
    }


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


def compile_person_likes(text: str, request: RememberRequest) -> MemoryCandidate:
    match = PERSON_LIKES_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    person = match.group("person").strip()
    liked = match.group("liked").strip()
    return MemoryCandidate(
        kind="preference",
        statement=text,
        summary=f"{person} likes {liked}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": infer_topics(liked)},
        entities=[
            EntityMention(name=person, type="person", role="subject", confidence="high"),
            EntityMention(name=liked, type=infer_entity_type(liked), role="topic"),
        ],
        relationships=[
            RelationshipCandidate(subject=person, predicate="likes", object=liked, confidence="high"),
        ],
    )


def compile_person_likes_correction(text: str, request: RememberRequest) -> MemoryCandidate:
    match = PERSON_LIKES_CORRECTION_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    person = match.group("person").strip()
    liked = match.group("liked").strip()
    old = match.group("old").strip()
    return MemoryCandidate(
        kind="preference",
        statement=text,
        summary=f"Correction: {person} likes {liked}, not {old}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": infer_topics(f"{liked} {old}"), "correction": True, "not": old},
        entities=[
            EntityMention(name=person, type="person", role="subject", confidence="high"),
            EntityMention(name=liked, type=infer_entity_type(liked), role="topic"),
            EntityMention(name=old, type=infer_entity_type(old), role="negated_topic"),
        ],
        relationships=[
            RelationshipCandidate(subject=person, predicate="likes", object=liked, confidence="high"),
        ],
    )


def compile_person_workplace(text: str, request: RememberRequest) -> MemoryCandidate:
    match = PERSON_WORKS_AT_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    person = match.group("person").strip()
    org = match.group("org").strip()
    person_alias = f"{person} from {org}"
    return MemoryCandidate(
        kind="person_fact",
        statement=text,
        summary=f"{person_alias} works at {org}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": [slug(org)]},
        entities=[
            EntityMention(name=person_alias, type="person", role="subject", alias=person, confidence="high"),
            EntityMention(name=org, type="organization", role="organization", confidence="high"),
        ],
        relationships=[
            RelationshipCandidate(subject=person_alias, predicate="works_at", object=org, confidence="high"),
        ],
    )


def compile_person_transition(text: str, request: RememberRequest) -> MemoryCandidate:
    match = PERSON_LEFT_JOINED_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    person = match.group("person").strip()
    old_org = match.group("old_org").strip()
    new_org = match.group("new_org").strip()
    person_alias = f"{person} from {old_org}"
    return MemoryCandidate(
        kind="person_fact",
        statement=text,
        summary=f"{person} left {old_org} and joined {new_org}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": [slug(old_org), slug(new_org)], "supersession": True},
        entities=[
            EntityMention(name=person_alias, type="person", role="subject", alias=person, confidence="high"),
            EntityMention(name=old_org, type="organization", role="previous_organization", confidence="high"),
            EntityMention(name=new_org, type="organization", role="organization", confidence="high"),
        ],
        relationships=[
            RelationshipCandidate(subject=person_alias, predicate="left", object=old_org, confidence="high"),
            RelationshipCandidate(subject=person_alias, predicate="works_at", object=new_org, confidence="high"),
        ],
    )


def compile_person_children(text: str, request: RememberRequest) -> MemoryCandidate:
    match = PERSON_CHILDREN_RE.match(text)
    if not match:
        return compile_basic_memory(text, request)
    person = match.group("person").strip()
    count = match.group("count").strip().casefold()
    normalized_count = number_word_to_int(count)
    object_name = "no children" if normalized_count == 0 else f"{normalized_count} children"
    return MemoryCandidate(
        kind="person_fact",
        statement=text,
        summary=f"{person} has {object_name}.",
        confidence="high",
        observed_at=request.observed_at,
        metadata={"topics": ["family"], "children_count": normalized_count},
        entities=[
            EntityMention(name=person, type="person", role="subject", confidence="high"),
            EntityMention(name=object_name, type="concept", role="attribute", confidence="high"),
        ],
        relationships=[
            RelationshipCandidate(
                subject=person,
                predicate="has_children_count",
                object=object_name,
                confidence="high",
            ),
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
    why_saved = request.context.get("why_saved") or request.context.get("user_note")
    topics = infer_topics(f"{text} {why_saved or ''}")
    return MemoryCandidate(
        kind="article_note",
        statement=f"Saved article for later recall: {text}",
        summary=f"Saved article: {text}",
        confidence="medium",
        observed_at=request.observed_at,
        metadata={"topics": topics, "why_saved": why_saved},
    )


def compile_table_note(text: str, request: RememberRequest) -> MemoryCandidate:
    first_line = text.splitlines()[0] if text.splitlines() else "table"
    table = parse_table(text)
    return MemoryCandidate(
        kind="table_note",
        statement=f"Stored a small table: {first_line[:160]}",
        summary=table_summary(table),
        confidence="medium",
        observed_at=request.observed_at,
        metadata={
            "topics": infer_topics(text),
            "columns": table.columns,
            "row_count": table.row_count,
            "sample_rows": table.sample_rows,
            "table_kind": table.kind,
        },
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


def number_word_to_int(value: str) -> int:
    numbers = {
        "no": 0,
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }
    lowered = value.casefold()
    if lowered in numbers:
        return numbers[lowered]
    return int(value)


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
