from __future__ import annotations

from dataclasses import dataclass, field

from memory_stack.model_selection import (
    configured_embedding,
    configured_llm,
    is_embedding_ref,
    parse_model_ref,
)


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    kind: str
    api_model: str | None = None
    quantizations: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    judge_only: bool = False
    price_per_1m: dict[str, float] = field(default_factory=dict)
    reasoning_effort: str | None = None
    skip_reason: str | None = None
    requested_ref: str | None = None

    @property
    def ref(self) -> str:
        return self.requested_ref or f"{self.provider}:{self.model}"

    @property
    def endpoint_key(self) -> str:
        target = self.api_model or self.model
        quantization_key = ",".join(self.quantizations)
        if quantization_key:
            return f"{self.provider}:{target}:{self.kind}:{quantization_key}"
        return f"{self.provider}:{target}:{self.kind}"


def select_model_candidates(
    settings: object,
    *,
    model_refs: list[str] | None,
    roles: set[str],
    fixture_roles: set[str],
) -> list[ModelCandidate]:
    """Build eval candidates from explicit refs or the active runtime settings.

    Brain now has exactly one configured LLM model and one configured embedding
    model. Model selection must not consult a registry or role matrix.
    """

    selected_roles = set(roles or fixture_roles)
    if model_refs:
        return dedupe_candidates(
            [
                candidate_from_ref(
                    ref,
                    roles=roles_for_kind(
                        "embedding" if is_embedding_ref(ref) else "llm",
                        selected_roles,
                    ),
                )
                for ref in model_refs
            ]
        )

    candidates: list[ModelCandidate] = []
    llm_roles = roles_for_kind("llm", selected_roles)
    if llm_roles:
        llm = configured_llm(settings)
        candidates.append(candidate_from_ref(llm.ref, roles=llm_roles))

    embedding_roles = roles_for_kind("embedding", selected_roles)
    if embedding_roles:
        embedding = configured_embedding(settings)
        candidates.append(candidate_from_ref(embedding.ref, roles=embedding_roles))

    return candidates


def candidate_from_ref(ref: str, *, roles: set[str]) -> ModelCandidate:
    parsed = parse_model_ref(ref)
    kind = "embedding" if "embeddings" in roles or is_embedding_ref(ref) else "llm"
    return ModelCandidate(
        provider=parsed.provider,
        model=parsed.model,
        kind=kind,
        api_model=parsed.model,
        roles=tuple(sorted(roles)),
        requested_ref=ref,
    )


def roles_for_kind(kind: str, roles: set[str]) -> set[str]:
    if kind == "embedding":
        return {"embeddings"} if "embeddings" in roles else set()
    return {role for role in roles if role != "embeddings"}


def dedupe_candidates(candidates: list[ModelCandidate]) -> list[ModelCandidate]:
    deduped: dict[tuple[str, str, str], ModelCandidate] = {}
    for candidate in candidates:
        key = (
            candidate.kind,
            candidate.provider,
            candidate.model,
            candidate.api_model,
            candidate.quantizations,
            candidate.reasoning_effort,
            candidate.requested_ref,
        )
        if key not in deduped:
            deduped[key] = candidate
            continue
        existing = deduped[key]
        deduped[key] = ModelCandidate(
            provider=existing.provider,
            model=existing.model,
            kind=existing.kind,
            api_model=existing.api_model,
            quantizations=existing.quantizations or candidate.quantizations,
            roles=tuple(dict.fromkeys((*existing.roles, *candidate.roles))),
            judge_only=existing.judge_only or candidate.judge_only,
            price_per_1m=existing.price_per_1m or candidate.price_per_1m,
            reasoning_effort=existing.reasoning_effort or candidate.reasoning_effort,
            skip_reason=existing.skip_reason or candidate.skip_reason,
            requested_ref=existing.requested_ref or candidate.requested_ref,
        )
    return list(deduped.values())
