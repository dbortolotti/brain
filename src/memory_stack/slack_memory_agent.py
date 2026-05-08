from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel
from sqlalchemy import func, select

from memory_stack import brain_schema as schema
from memory_stack.brain_models import RecallRequest, RememberRequest
from memory_stack.brain_service import (
    get_memory,
    list_open_loops,
    profile_entity,
    recall,
    remember,
)
from memory_stack.brain_store import BrainStore, row_dict
from memory_stack.config import Settings
from memory_stack.slack_guardrails import (
    ProposedMemory,
    SlackAgentProposal,
    contains_secret,
    load_slack_rules,
    parse_llm_proposal,
    validate_slack_proposal,
)


class SlackGuardLLM(Protocol):
    def complete_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str | None = None,
        temperature: float = 0,
    ) -> Any:
        ...


@dataclass(frozen=True)
class SlackAgentRequest:
    text: str
    user_id: str
    channel_id: str
    team_id: str | None = None
    thread_ts: str | None = None
    message_ts: str | None = None
    permalink: str | None = None
    source: str = "slash_command"
    confirmed: bool = False
    proposed_memory: dict[str, Any] | None = None


@dataclass(frozen=True)
class SlackAgentResponse:
    decision: str
    text: str
    response_type: str = "ephemeral"
    payload: dict[str, Any] = field(default_factory=dict)
    blocks: list[dict[str, Any]] = field(default_factory=list)

    def as_slack_payload(self) -> dict[str, Any]:
        payload = {
            "response_type": self.response_type,
            "text": self.text,
            "payload": self.payload,
        }
        if self.blocks:
            payload["blocks"] = self.blocks
        return payload


class SlackDebugInspector:
    TABLES = {
        "memory_cards": schema.memory_cards,
        "sources": schema.sources,
        "entities": schema.entities,
        "relationships": schema.relationships,
        "memory_links": schema.memory_links,
        "open_loops": schema.open_loops,
        "cognee_sync": schema.cognee_sync,
        "ingestion_runs": schema.ingestion_runs,
        "recall_logs": schema.recall_logs,
    }
    TEXT_COLUMNS = {
        "memory_cards": [schema.memory_cards.c.statement, schema.memory_cards.c.summary],
        "sources": [schema.sources.c.title, schema.sources.c.summary, schema.sources.c.uri],
        "entities": [schema.entities.c.canonical_name, schema.entities.c.normalized_name],
        "ingestion_runs": [schema.ingestion_runs.c.raw_input_preview],
        "cognee_sync": [schema.cognee_sync.c.object_id, schema.cognee_sync.c.error_message],
    }

    def __init__(self, settings: Settings) -> None:
        self.store = BrainStore(settings)

    def snapshot(self, *, limit: int = 5) -> dict[str, Any]:
        with self.store.engine.begin() as conn:
            counts = {
                name: conn.execute(select(func.count()).select_from(table)).scalar_one()
                for name, table in self.TABLES.items()
            }
            recent_memory_rows = conn.execute(
                select(schema.memory_cards)
                .order_by(schema.memory_cards.c.created_at.desc())
                .limit(limit)
            ).fetchall()
            recent_source_rows = conn.execute(
                select(schema.sources).order_by(schema.sources.c.created_at.desc()).limit(limit)
            ).fetchall()
        return {
            "counts": counts,
            "recent_memory_ids": [row._mapping[schema.memory_cards.c.id] for row in recent_memory_rows],
            "recent_source_ids": [row._mapping[schema.sources.c.id] for row in recent_source_rows],
        }

    def raw_record(self, table_name: str, object_id: str) -> dict[str, Any] | None:
        table = self._table(table_name)
        with self.store.engine.begin() as conn:
            row = conn.execute(select(table).where(table.c.id == object_id)).first()
        return redact_record(table_name, row_dict(row)) if row is not None else None

    def search_rows(self, table_name: str, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        table = self._table(table_name)
        columns = self.TEXT_COLUMNS.get(table_name)
        if not columns:
            raise ValueError(f"Table is not searchable: {table_name}")
        safe_limit = max(1, min(limit, 20))
        filters = [column.ilike(f"%{query}%") for column in columns]
        with self.store.engine.begin() as conn:
            rows = conn.execute(select(table).where(filters[0] if len(filters) == 1 else filters[0] | filters[1]).limit(safe_limit)).fetchall()
        return [redact_record(table_name, row_dict(row)) for row in rows]

    def ingestion_run(self, run_id: str) -> dict[str, Any] | None:
        run = self.store.get_ingestion_run(run_id)
        if run is None:
            return None
        memories = [
            memory
            for memory in self.store.list_memory_cards(include_deleted=True, limit=100_000)
            if (memory.get("metadata_json") or {}).get("ingestion_run_id") == run_id
            or (run.get("source_id") and memory.get("source_id") == run.get("source_id"))
        ]
        sync_rows = []
        for memory in memories:
            sync_rows.extend(self.store.get_cognee_sync(memory["id"]))
        if run.get("source_id"):
            sync_rows.extend(self.store.get_cognee_sync(run["source_id"]))
        return {
            "ingestion_run": run,
            "memory_ids": [memory["id"] for memory in memories],
            "source_id": run.get("source_id"),
            "cognee_sync": sync_rows,
        }

    def cognee_sync(self, object_id: str) -> list[dict[str, Any]]:
        return self.store.get_cognee_sync(object_id)

    def _table(self, table_name: str) -> Any:
        table = self.TABLES.get(table_name)
        if table is None:
            raise ValueError(f"Table is not allowed: {table_name}")
        return table


class SlackMemoryAgent:
    def __init__(
        self,
        settings: Settings,
        *,
        llm_client: SlackGuardLLM | None = None,
    ) -> None:
        self.settings = settings
        self.llm_client = llm_client
        self.store = BrainStore(settings)
        self.rules = load_slack_rules(settings)

    def handle(self, request: SlackAgentRequest) -> SlackAgentResponse:
        normalized = normalize_agent_text(request.text)
        if not normalized:
            return self._unsupported("Tell me what to remember or recall.")

        command, argument = split_intent(normalized)
        if command == "remember":
            return self._handle_remember(argument, request)
        if command == "confirm":
            return self._handle_confirm(argument, request)
        if command == "recall":
            return self._handle_recall(argument, request)
        if command == "profile":
            return self._handle_profile(argument, request)
        if command in {"open_loops", "open"}:
            return self._handle_open_loops(argument)
        if command == "get_memory":
            return self._handle_get_memory(argument)
        if command == "debug":
            return self._handle_debug(argument, request)
        return self._unsupported("I only handle Brain memory commands.")

    def _handle_remember(
        self,
        text: str,
        request: SlackAgentRequest,
    ) -> SlackAgentResponse:
        if not text:
            return self._ask("What should I remember?")
        context = self._context_for(text)
        try:
            proposal = self._proposal_for_remember(text, request=request, context=context)
        except ValueError as exc:
            return SlackAgentResponse(
                decision="complain",
                text=f"I cannot use the guardrail proposal: {exc}",
                payload={"reason": "invalid_guardrail_proposal"},
            )
        context_conflicts = possible_contradictions(text, context.get("similar_memories", []))
        if context_conflicts and not request.confirmed:
            return SlackAgentResponse(
                decision="complain",
                text=(
                    "That may conflict with existing memory. Confirm whether to supersede it "
                    "or keep both before I write anything."
                ),
                payload={"conflicts": context_conflicts, "proposal": proposal.model_dump(mode="json")},
            )

        allow_commit = request.confirmed or self._auto_commit_allowed(proposal)
        guard = validate_slack_proposal(
            proposal,
            raw_text=text,
            allow_commit=allow_commit,
        )
        if not guard.accepted:
            return SlackAgentResponse(
                decision=guard.proposal.decision,
                text=guard.proposal.user_message,
                payload={
                    "reason": guard.blocked_reason,
                    "proposal": guard.proposal.model_dump(mode="json"),
                },
            )

        accepted = guard.proposal
        if accepted.proposed_memory is None:
            return self._ask("What durable memory should I store?")

        dry_run_receipt = remember(
            self._remember_request(accepted.proposed_memory, request, dry_run=True),
            self.settings,
        )
        if not allow_commit:
            response_text = accepted.user_message or "I can store this memory after you confirm."
            return SlackAgentResponse(
                decision="dry_run",
                text=response_text,
                payload={
                    "requires_confirmation": True,
                    "proposal": accepted.model_dump(mode="json"),
                    "dry_run": dry_run_receipt.model_dump(mode="json"),
                    "verification_hint": "Click Confirm or run /brain confirm <same text>.",
                },
                blocks=confirmation_blocks(
                    response_text,
                    accepted.proposed_memory.model_dump(mode="json"),
                ),
            )

        receipt = remember(
            self._remember_request(accepted.proposed_memory, request, dry_run=False),
            self.settings,
        )
        return SlackAgentResponse(
            decision="commit",
            text=receipt_text(receipt.model_dump(mode="json")),
            payload={
                "receipt": receipt.model_dump(mode="json"),
                "dry_run": dry_run_receipt.model_dump(mode="json"),
            },
        )

    def _handle_confirm(
        self,
        text: str,
        request: SlackAgentRequest,
    ) -> SlackAgentResponse:
        if request.proposed_memory:
            proposed_memory = ProposedMemory.model_validate(request.proposed_memory)
        elif text:
            proposed_memory = deterministic_memory(text)
        else:
            return self._ask("What proposed memory should I confirm?")
        proposal = SlackAgentProposal(
            decision="commit",
            reason="User confirmed proposed Slack memory.",
            user_message="Confirmed. I stored the memory.",
            proposed_memory=proposed_memory,
            requires_confirmation=True,
        )
        confirmed_request = SlackAgentRequest(
            **{**request.__dict__, "confirmed": True, "text": f"remember {proposed_memory.input}"}
        )
        response = self._handle_remember(proposed_memory.input, confirmed_request)
        return SlackAgentResponse(
            decision=response.decision,
            text=response.text,
            response_type=response.response_type,
            payload={**response.payload, "proposal": proposal.model_dump(mode="json")},
            blocks=response.blocks,
        )

    def _handle_recall(self, query: str, request: SlackAgentRequest) -> SlackAgentResponse:
        if not query:
            return self._ask("What should I recall?")
        response = recall(RecallRequest(query=query), self.settings)
        return SlackAgentResponse(
            decision="recall",
            text=response.answer,
            response_type="in_channel" if request.source == "event" else "ephemeral",
            payload=response.model_dump(mode="json"),
        )

    def _handle_profile(self, name: str, request: SlackAgentRequest) -> SlackAgentResponse:
        if not name:
            return self._ask("Which entity should I profile?")
        response = profile_entity(self.settings, name=name)
        return SlackAgentResponse(
            decision="profile",
            text=response.answer,
            response_type="in_channel" if request.source == "event" else "ephemeral",
            payload=response.model_dump(mode="json"),
        )

    def _handle_open_loops(self, topic: str) -> SlackAgentResponse:
        loops = list_open_loops(self.settings, topic=topic or None)
        if not loops:
            return SlackAgentResponse(
                decision="open_loops",
                text="No open loops found.",
                payload={"open_loops": []},
            )
        text = "\n".join(["Open loops", *[f"- {loop['statement']} [{loop['memory_id']}]" for loop in loops]])
        return SlackAgentResponse(
            decision="open_loops",
            text=text,
            payload={"open_loops": loops},
        )

    def _handle_get_memory(self, memory_id: str) -> SlackAgentResponse:
        if not memory_id:
            return self._ask("Which memory_id should I fetch?")
        memory = get_memory(memory_id, self.settings)
        if memory is None:
            return SlackAgentResponse(
                decision="get_memory",
                text=f"Memory not found: {memory_id}",
                payload={"memory": None},
            )
        return SlackAgentResponse(
            decision="get_memory",
            text=f"{memory['statement']} [{memory['id']}; {memory['status']}]",
            payload={"memory": memory},
        )

    def _handle_debug(self, argument: str, request: SlackAgentRequest) -> SlackAgentResponse:
        if not is_admin_user(self.settings, request.user_id):
            return SlackAgentResponse(
                decision="debug",
                text="Debug tools are admin-only.",
                payload={"status": "forbidden"},
            )
        inspector = SlackDebugInspector(self.settings)
        action, rest = split_first(argument)
        if action in {"", "snapshot"}:
            payload = inspector.snapshot()
        elif action == "raw_record":
            table, object_id = split_first(rest)
            payload = {"record": inspector.raw_record(table, object_id)}
        elif action == "search_rows":
            table, query = split_first(rest)
            payload = {"rows": inspector.search_rows(table, query)}
        elif action == "ingestion_run":
            payload = {"ingestion_run": inspector.ingestion_run(rest)}
        elif action == "cognee_sync":
            payload = {"cognee_sync": inspector.cognee_sync(rest)}
        else:
            return self._unsupported("Unknown debug command.")
        return SlackAgentResponse(
            decision="debug",
            text=json.dumps(payload, default=str)[:3000],
            payload=payload,
        )

    def _proposal_for_remember(
        self,
        text: str,
        *,
        request: SlackAgentRequest,
        context: dict[str, Any],
    ) -> SlackAgentProposal:
        if self.llm_client is None:
            return deterministic_proposal(text, context=context)
        raw = self.llm_client.complete_json(
            self._guard_prompt(text, request=request, context=context),
            SlackAgentProposal.model_json_schema(),
            model=self.settings.brain_llm_model or self.settings.llm_model,
            temperature=0,
        )
        return parse_llm_proposal(raw)

    def _guard_prompt(
        self,
        text: str,
        *,
        request: SlackAgentRequest,
        context: dict[str, Any],
    ) -> str:
        return "\n".join(
            [
                self.rules,
                "",
                "Slack request:",
                json.dumps(request.__dict__, default=str, sort_keys=True),
                "",
                "Brain context:",
                json.dumps(context, default=str, sort_keys=True),
                "",
                "User message:",
                text,
            ]
        )

    def _context_for(self, text: str) -> dict[str, Any]:
        return {
            "similar_memories": self.store.search_memory(
                text,
                include_superseded=True,
                limit=5,
            ),
            "recent_conflicts": self.store.list_memory_links(
                relations=("duplicates", "supersedes", "contradicts"),
                limit=5,
            ),
        }

    def _remember_request(
        self,
        memory: ProposedMemory,
        request: SlackAgentRequest,
        *,
        dry_run: bool,
    ) -> RememberRequest:
        return RememberRequest(
            input=memory.input,
            input_type=memory.input_type,
            source_policy=memory.source_policy,
            dry_run=dry_run,
            context={
                "slack": {
                    "team_id": request.team_id,
                    "channel_id": request.channel_id,
                    "user_id": request.user_id,
                    "thread_ts": request.thread_ts,
                    "message_ts": request.message_ts,
                    "permalink": request.permalink,
                    "source": request.source,
                }
            },
        )

    def _auto_commit_allowed(self, proposal: SlackAgentProposal) -> bool:
        return (
            self.settings.brain_slack_auto_commit_high_confidence
            and proposal.proposed_memory is not None
            and proposal.proposed_memory.confidence == "high"
            and not proposal.conflicts
            and not proposal.requires_confirmation
        )

    def _ask(self, text: str) -> SlackAgentResponse:
        return SlackAgentResponse(decision="ask", text=text)

    def _unsupported(self, text: str) -> SlackAgentResponse:
        return SlackAgentResponse(
            decision="unsupported",
            text=text,
            payload={"status": "unsupported"},
        )


def normalize_agent_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("/brain"):
        stripped = stripped.removeprefix("/brain").strip()
    return stripped


def split_intent(text: str) -> tuple[str, str]:
    command, argument = split_first(text)
    normalized = command.replace("-", "_")
    aliases = {
        "open": "open_loops",
        "open_loop": "open_loops",
        "memory": "get_memory",
    }
    if normalized in {
        "remember",
        "confirm",
        "recall",
        "profile",
        "open_loops",
        "get_memory",
        "debug",
    }:
        return aliases.get(normalized, normalized), argument
    lower = text.casefold()
    if lower.startswith(("remember ", "store ", "save ")):
        return "remember", split_first(text)[1]
    if lower.startswith(("what ", "who ", "tell me ", "find ")):
        return "recall", text
    return "unsupported", text


def split_first(text: str) -> tuple[str, str]:
    first, _, rest = text.strip().partition(" ")
    return first.strip(), rest.strip()


def deterministic_proposal(text: str, *, context: dict[str, Any]) -> SlackAgentProposal:
    if contains_secret(text):
        return SlackAgentProposal(
            decision="complain",
            reason="secret_or_token_detected",
            user_message="I will not store this because it contains a token/password-shaped value.",
            proposed_memory=None,
        )
    memory = deterministic_memory(text)
    conflicts = possible_contradictions(text, context.get("similar_memories", []))
    return SlackAgentProposal(
        decision="dry_run",
        reason="Deterministic Slack proposal.",
        user_message="I can store this memory after you confirm.",
        proposed_memory=memory,
        conflicts=conflicts,
        requires_confirmation=bool(conflicts) or memory.input_type in {"open_question", "research_question"},
    )


def deterministic_memory(text: str) -> ProposedMemory:
    lower = text.casefold()
    input_type = "auto"
    if lower.startswith(("i want to learn", "i would like to learn", "remind me to learn")):
        input_type = "open_question"
        if lower.startswith("remind me to learn"):
            text = "I want to learn " + text.split("learn", 1)[1].strip()
    elif "?" in text or lower.startswith("i wonder"):
        input_type = "research_question"
    elif "mentioned that" in lower:
        input_type = "person_interaction"
    elif "concluded" in lower or "should use" in lower:
        input_type = "chat_conclusion"
    confidence = "medium" if re.search(r"\b(maybe|probably|might|guess)\b", lower) else "high"
    entities = guess_entities(text)
    return ProposedMemory(
        input=text.strip(),
        input_type=input_type,
        source_policy="memory_only",
        confidence=confidence,
        entities=entities,
    )


def possible_contradictions(text: str, similar_memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lower = text.casefold()
    if not re.search(r"\b(no|not|actually|left|joined|replace|supersedes|correction)\b", lower):
        return []
    return [
        {
            "memory_id": memory["id"],
            "statement": memory["statement"],
            "status": memory["status"],
        }
        for memory in similar_memories
        if memory.get("status") in {"current", "conflicted", "superseded"}
    ][:5]


def guess_entities(text: str) -> list[str]:
    pronouns = {"He", "She", "They", "It", "That", "This"}
    return [
        entity
        for entity in re.findall(r"\b[A-Z][A-Za-z0-9&'-]*(?:\s+[A-Z][A-Za-z0-9&'-]*)*\b", text)
        if entity not in pronouns
    ]


def is_admin_user(settings: Settings, user_id: str) -> bool:
    admins = settings.brain_slack_admin_user_id_list
    return bool(admins and user_id in admins)


def redact_record(table_name: str, record: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(record)
    if table_name == "sources" and "raw_text" in redacted:
        redacted["raw_text"] = "[redacted]"
    for key, value in list(redacted.items()):
        if isinstance(value, str) and len(value) > 500:
            redacted[key] = value[:500] + "...[truncated]"
    return redacted


def receipt_text(receipt: dict[str, Any]) -> str:
    cards = receipt.get("memory_cards", [])
    if not cards:
        return "No memory cards were stored."
    lines = [f"Stored {len(cards)} memory card(s)."]
    source = receipt.get("source") if isinstance(receipt.get("source"), dict) else {}
    if source.get("source_id"):
        lines.append(f"Source ID: {source['source_id']}")
    for card in cards:
        lines.append(
            "- "
            f"{card['kind']}: {card['statement']} "
            f"[memory_id: {card['id']}; confidence: {card.get('confidence', 'medium')}; "
            f"status: {card['status']}]"
        )
    entities = receipt.get("entities") if isinstance(receipt.get("entities"), list) else []
    if entities:
        lines.append("Entities: " + ", ".join(str(entity.get("canonical_name")) for entity in entities))
    relationships = receipt.get("relationships") if isinstance(receipt.get("relationships"), list) else []
    if relationships:
        lines.append(f"Relationships: {len(relationships)}")
    if receipt.get("conflicts"):
        lines.append(f"Conflicts detected: {len(receipt['conflicts'])}.")
    lines.append("Actions: Inspect | Undo | Mark wrong")
    return "\n".join(lines)


def confirmation_blocks(text: str, proposed_memory: dict[str, Any]) -> list[dict[str, Any]]:
    value = json.dumps({"proposed_memory": proposed_memory}, separators=(",", ":"))
    if len(value) > 1900:
        return []
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Confirm"},
                    "style": "primary",
                    "action_id": "brain_confirm_memory",
                    "value": value,
                }
            ],
        },
    ]


class InteractionPayload(BaseModel):
    proposed_memory: dict[str, Any]
    user_id: str
    channel_id: str
    team_id: str | None = None
    thread_ts: str | None = None
    message_ts: str | None = None
    permalink: str | None = None
