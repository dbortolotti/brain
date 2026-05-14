from __future__ import annotations

from typing import Any

from memory_stack.agents.prompt_contracts import MEMORY_COMPILER_RUNTIME_ROLES, prompt_contract_block
from memory_stack.brain_models import (
    EntityMention,
    MemoryCandidate,
    RelationshipCandidate,
    RememberRequest,
    SourceCandidate,
)
from memory_stack.cfg import Settings
from memory_stack.llm.client import LLMClient, build_llm_client
from memory_stack.llm.models import LLMCompilerOutput, compiler_output_schema
from memory_stack.ingestion.rule_compiler import CompiledInput, compile_input


def compile_memory(
    request: RememberRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> CompiledInput:
    rule_result = compile_input(request, settings)
    if rule_result.sufficient and rule_result.confidence == "high":
        return rule_result

    active_client = llm_client or build_llm_client(settings)
    if settings.brain_llm_enabled and active_client is not None:
        try:
            return compile_with_llm(request, settings, rule_result, active_client)
        except Exception:
            if llm_client is not None:
                raise

    return rule_result


def compile_with_llm(
    request: RememberRequest,
    settings: Settings,
    rule_result: CompiledInput,
    llm_client: LLMClient,
) -> CompiledInput:
    prompt = compiler_prompt(request, settings, rule_result)
    output = LLMCompilerOutput.model_validate(
        llm_client.complete_json(
            prompt,
            compiler_output_schema(),
            model=settings.llm_model,
            temperature=0,
        )
    )
    return compiler_output_to_compiled_input(output, request, rule_result)


def compiler_prompt(
    request: RememberRequest,
    settings: Settings,
    rule_result: CompiledInput,
) -> str:
    source_text = rule_result.source.raw_text if rule_result.source else request.input
    return "\n".join(
        [
            "Extract durable personal-memory cards from the input.",
            "Keep facts atomic. Preserve uncertainty. Do not invent names, dates, or relationships.",
            "Return only JSON matching the provided schema.",
            "Use the same role contracts that the model eval harness tests.",
            prompt_contract_block(MEMORY_COMPILER_RUNTIME_ROLES),
            f"Owner: {settings.brain_owner_name}",
            f"Input type: {request.input_type}",
            f"Rule classification: {rule_result.classification}",
            "Input:",
            source_text[:12_000],
        ]
    )


def compiler_output_to_compiled_input(
    output: LLMCompilerOutput,
    request: RememberRequest,
    rule_result: CompiledInput,
) -> CompiledInput:
    source = source_from_output(output, request, rule_result)
    cards = [memory_card_from_output(card.model_dump()) for card in output.memory_cards]
    if source is not None:
        cards = [
            card.model_copy(
                update={
                    "source_quote": card.source_quote
                    or (source.raw_text[:500] if source.raw_text else None)
                }
            )
            for card in cards
        ]
    return CompiledInput(
        classification=output.classification or rule_result.classification,
        source=source,
        memory_cards=cards,
        confidence="medium",
        sufficient=True,
    )


def source_from_output(
    output: LLMCompilerOutput,
    request: RememberRequest,
    rule_result: CompiledInput,
) -> SourceCandidate | None:
    if not output.source.should_create:
        return rule_result.source

    base = rule_result.source
    metadata = dict(base.metadata if base else {})
    metadata.update(output.source.metadata)
    return SourceCandidate(
        kind=output.source.kind or (base.kind if base else "other"),
        title=output.source.title or (base.title if base else None),
        uri=base.uri if base else request.input if request.input.startswith(("http://", "https://")) else None,
        file_path=base.file_path if base else None,
        raw_text=base.raw_text if base else request.input,
        summary=output.source.summary or (base.summary if base else request.input[:500]),
        metadata=metadata,
        status=base.status if base else "processed",
    )


def memory_card_from_output(card: dict[str, Any]) -> MemoryCandidate:
    metadata = dict(card.get("metadata") or {})
    topics = [topic for topic in card.get("topics", []) if topic]
    if topics:
        metadata["topics"] = topics
    open_loop = card.get("open_loop")
    if open_loop is None and card.get("kind") in {"open_question", "research_question"}:
        open_loop = {
            "status": "open",
            "priority": "normal",
            "reminder_policy": "opportunistic_or_weekly",
        }
    return MemoryCandidate(
        kind=card["kind"],
        statement=card["statement"],
        summary=card.get("summary"),
        confidence=card.get("confidence") or "medium",
        observed_at=card.get("observed_at"),
        source_quote=card.get("source_quote"),
        metadata=metadata,
        entities=[
            EntityMention(
                name=entity["name"],
                type=entity.get("type") or "concept",
                role=entity.get("role") or "mentioned",
                alias=entity.get("alias"),
                confidence=entity.get("confidence") or "medium",
                metadata=entity.get("metadata") or {},
            )
            for entity in card.get("entities", [])
        ],
        relationships=[
            RelationshipCandidate(
                subject=relationship["subject"],
                predicate=relationship["predicate"],
                object=relationship["object"],
                confidence=relationship.get("confidence") or "medium",
                metadata=relationship.get("metadata") or {},
            )
            for relationship in card.get("relationships", [])
        ],
        open_loop=open_loop,
    )
