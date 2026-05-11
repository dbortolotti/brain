from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


Decision = Literal[
    "ask",
    "complain",
    "dry_run",
    "commit",
    "recall",
    "profile",
    "debug",
    "unsupported",
]
InputType = Literal[
    "auto",
    "fact",
    "note",
    "person_interaction",
    "open_question",
    "research_question",
    "chat_conclusion",
    "table",
]
SourcePolicy = Literal["memory_only", "source_and_memory"]
Confidence = Literal["low", "medium", "high"]


SECRET_PATTERNS = [
    re.compile(r"\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\b[A-Za-z0-9_/-]{24,}\.[A-Za-z0-9_/-]{12,}\.[A-Za-z0-9_/-]{12,}\b"),
]
AMBIGUOUS_PRONOUN_RE = re.compile(r"\b(he|she|they|it|that|this)\b", re.IGNORECASE)
CORRECTION_RE = re.compile(r"\b(actually|replace|supersedes|correction|instead)\b", re.IGNORECASE)
SENSITIVE_RE = re.compile(
    r"\b(health|medical|diagnosis|pregnant|salary|ssn|passport|bank|children|child)\b",
    re.IGNORECASE,
)


class ProposedMemory(BaseModel):
    input: str
    input_type: InputType = "auto"
    source_policy: SourcePolicy = "memory_only"
    confidence: Confidence = "medium"
    entities: list[str] = Field(default_factory=list)


class SlackAgentProposal(BaseModel):
    decision: Decision
    reason: str
    user_message: str
    proposed_memory: ProposedMemory | None = None
    questions: list[str] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    requires_confirmation: bool = True


class GuardrailResult(BaseModel):
    accepted: bool
    proposal: SlackAgentProposal
    blocked_reason: str | None = None

def parse_llm_proposal(raw: Any) -> SlackAgentProposal:
    if isinstance(raw, SlackAgentProposal):
        return raw
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Slack memory guard returned malformed JSON.") from exc
    try:
        return SlackAgentProposal.model_validate(raw)
    except ValidationError as exc:
        raise ValueError("Slack memory guard returned invalid proposal schema.") from exc


def validate_slack_proposal(
    proposal: SlackAgentProposal,
    *,
    raw_text: str,
    allow_commit: bool,
) -> GuardrailResult:
    blocked_reason = deterministic_blocker(proposal, raw_text=raw_text, allow_commit=allow_commit)
    if blocked_reason is not None:
        blocked = proposal.model_copy(
            update={
                "decision": "complain" if "secret" in blocked_reason else "ask",
                "reason": blocked_reason,
                "user_message": blocked_message(blocked_reason),
                "requires_confirmation": True,
            }
        )
        return GuardrailResult(accepted=False, proposal=blocked, blocked_reason=blocked_reason)
    return GuardrailResult(accepted=True, proposal=proposal)


def deterministic_blocker(
    proposal: SlackAgentProposal,
    *,
    raw_text: str,
    allow_commit: bool,
) -> str | None:
    proposed_input = proposal.proposed_memory.input if proposal.proposed_memory else ""
    combined = f"{raw_text}\n{proposed_input}"
    if contains_secret(combined):
        return "secret_or_token_detected"
    if proposal.decision == "commit" and not allow_commit:
        return "commit_not_allowed_without_confirmation"
    if proposal.decision in {"commit", "dry_run"} and proposal.proposed_memory is None:
        return "write_decision_missing_memory"
    if proposal.proposed_memory is not None:
        memory = proposal.proposed_memory
        if not memory.input.strip():
            return "empty_memory"
        if memory.confidence == "low":
            return "low_confidence_memory"
        if ambiguous_pronoun_without_entity(memory.input, memory.entities):
            return "ambiguous_subject"
        if proposal.conflicts and not proposal.requires_confirmation:
            return "conflict_requires_confirmation"
        if is_sensitive(memory.input) and not proposal.requires_confirmation:
            return "sensitive_memory_requires_confirmation"
        if CORRECTION_RE.search(memory.input) and not proposal.requires_confirmation:
            return "correction_requires_confirmation"
    return None


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def ambiguous_pronoun_without_entity(text: str, entities: list[str]) -> bool:
    if not AMBIGUOUS_PRONOUN_RE.search(text):
        return False
    if re.match(r"^\s*(he|she|they|it|that|this)\b", text, re.IGNORECASE):
        return True
    return not [entity for entity in entities if entity.strip()]


def is_sensitive(text: str) -> bool:
    return SENSITIVE_RE.search(text) is not None


def blocked_message(reason: str) -> str:
    messages = {
        "secret_or_token_detected": "I will not store this because it contains a token/password-shaped value.",
        "commit_not_allowed_without_confirmation": "I can prepare this memory, but I need confirmation before writing it.",
        "write_decision_missing_memory": "I cannot store this because the proposed memory is missing.",
        "empty_memory": "I cannot store an empty memory.",
        "low_confidence_memory": "This is too uncertain to store as memory. What should I preserve?",
        "ambiguous_subject": "I cannot store this as written because the subject is unclear. Who does the pronoun refer to?",
        "conflict_requires_confirmation": "This appears to conflict with existing memory. Confirm whether to supersede it or keep both.",
        "sensitive_memory_requires_confirmation": "This looks sensitive, so I need explicit confirmation before storing it.",
        "correction_requires_confirmation": "This looks like a correction, so I need confirmation before changing memory state.",
    }
    return messages.get(reason, f"I cannot store this as written: {reason}.")
