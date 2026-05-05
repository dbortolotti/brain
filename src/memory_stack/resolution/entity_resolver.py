from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from memory_stack.brain_store import normalize_name


ResolutionAction = Literal["matched", "created", "alias_added", "ambiguous"]
ResolutionConfidence = Literal["low", "medium", "high"]

CONTEXT_RE = re.compile(
    r"^(?P<name>.+?)\s+(?:from|at|/)\s+(?P<organization>.+?)$",
    re.IGNORECASE,
)


class EntityResolution(BaseModel):
    entity_id: str
    action: ResolutionAction
    confidence: ResolutionConfidence
    reason: str
    entity: dict[str, Any] = Field(default_factory=dict)
    created: bool = False
    ambiguous_candidates: list[str] = Field(default_factory=list)


class EntityResolver:
    def __init__(self, store: Any) -> None:
        self.store = store

    def resolve_entity(
        self,
        *,
        entity_type: str,
        canonical_name: str,
        aliases: list[str] | None = None,
        confidence: str = "medium",
        metadata_json: dict[str, Any] | None = None,
    ) -> EntityResolution:
        normalized = normalize_name(canonical_name)
        if not normalized:
            raise ValueError("canonical_name must contain at least one word-like character.")

        clean_aliases = unique_nonempty(
            [canonical_name, *(aliases or []), *implicit_aliases(canonical_name)]
        )
        exact = self.store.find_entity_by_normalized_name(
            entity_type=entity_type,
            normalized_name=normalized,
        )
        if exact is not None:
            self._add_aliases(exact["id"], clean_aliases, confidence)
            return EntityResolution(
                entity_id=exact["id"],
                action="matched",
                confidence="high",
                reason="Exact normalized entity name match.",
                entity=exact,
                created=False,
            )

        contextual = contextual_name(canonical_name)
        if entity_type == "person" and contextual is not None:
            match = self._resolve_contextual_person(
                canonical_name=canonical_name,
                aliases=clean_aliases,
                context=contextual,
                confidence=confidence,
            )
            if match is not None:
                return match
            entity, created = self.store.create_entity(
                entity_type=entity_type,
                canonical_name=canonical_name,
                normalized_name=normalized,
                confidence=confidence,
                metadata_json=metadata_json,
            )
            self._add_aliases(entity["id"], clean_aliases, confidence)
            return EntityResolution(
                entity_id=entity["id"],
                action="created" if created else "matched",
                confidence=as_resolution_confidence(confidence),
                reason="No compatible contextual person match found.",
                entity=entity,
                created=created,
            )

        alias_candidates = self._alias_candidates(entity_type, clean_aliases)
        if len(alias_candidates) == 1:
            entity = alias_candidates[0]
            self._add_aliases(entity["id"], [canonical_name, *clean_aliases], confidence)
            return EntityResolution(
                entity_id=entity["id"],
                action="alias_added",
                confidence="medium",
                reason="Single alias match.",
                entity=entity,
                created=False,
            )
        if len(alias_candidates) > 1:
            return self._create_ambiguous_entity(
                entity_type=entity_type,
                canonical_name=canonical_name,
                normalized_name=normalized,
                aliases=clean_aliases,
                confidence=confidence,
                metadata_json=metadata_json,
                candidates=alias_candidates,
            )

        entity, created = self.store.create_entity(
            entity_type=entity_type,
            canonical_name=canonical_name,
            normalized_name=normalized,
            confidence=confidence,
            metadata_json=metadata_json,
        )
        self._add_aliases(entity["id"], clean_aliases, confidence)
        return EntityResolution(
            entity_id=entity["id"],
            action="created" if created else "matched",
            confidence=as_resolution_confidence(confidence),
            reason="No exact, alias, or contextual match found.",
            entity=entity,
            created=created,
        )

    def _resolve_contextual_person(
        self,
        *,
        canonical_name: str,
        aliases: list[str],
        context: dict[str, str],
        confidence: str,
    ) -> EntityResolution | None:
        candidates = self._alias_candidates("person", [context["name"], *aliases])
        compatible = [
            candidate
            for candidate in candidates
            if contexts_compatible(contextual_name(candidate["canonical_name"]), context)
        ]
        if len(compatible) == 1:
            entity = compatible[0]
            self._add_aliases(entity["id"], [canonical_name, *aliases], confidence)
            return EntityResolution(
                entity_id=entity["id"],
                action="alias_added",
                confidence="high",
                reason="Matched contextual person alias and compatible organization context.",
                entity=entity,
                created=False,
            )
        if len(compatible) > 1:
            return self._create_ambiguous_entity(
                entity_type="person",
                canonical_name=canonical_name,
                normalized_name=normalize_name(canonical_name),
                aliases=aliases,
                confidence=confidence,
                metadata_json=None,
                candidates=compatible,
            )
        return None

    def _create_ambiguous_entity(
        self,
        *,
        entity_type: str,
        canonical_name: str,
        normalized_name: str,
        aliases: list[str],
        confidence: str,
        metadata_json: dict[str, Any] | None,
        candidates: list[dict[str, Any]],
    ) -> EntityResolution:
        candidate_ids = sorted({candidate["id"] for candidate in candidates})
        metadata = dict(metadata_json or {})
        metadata["resolution_ambiguity"] = {
            "candidate_entity_ids": candidate_ids,
            "reason": "Multiple alias candidates matched; Brain did not guess.",
        }
        entity, created = self.store.create_entity(
            entity_type=entity_type,
            canonical_name=canonical_name,
            normalized_name=normalized_name,
            confidence="low",
            metadata_json=metadata,
        )
        self._add_aliases(entity["id"], aliases, confidence)
        return EntityResolution(
            entity_id=entity["id"],
            action="ambiguous",
            confidence="low",
            reason="Multiple alias candidates matched; created a separate ambiguous entity.",
            entity=entity,
            created=created,
            ambiguous_candidates=candidate_ids,
        )

    def _alias_candidates(
        self,
        entity_type: str,
        aliases: list[str],
    ) -> list[dict[str, Any]]:
        by_id: dict[str, dict[str, Any]] = {}
        for alias in aliases:
            normalized_alias = normalize_name(alias)
            if not normalized_alias:
                continue
            for entity in self.store.find_entities_by_alias(
                entity_type=entity_type,
                normalized_alias=normalized_alias,
            ):
                by_id[entity["id"]] = entity
        return list(by_id.values())

    def _add_aliases(
        self,
        entity_id: str,
        aliases: list[str],
        confidence: str,
    ) -> None:
        for alias in unique_nonempty(aliases):
            self.store.add_entity_alias(
                entity_id=entity_id,
                alias=alias,
                confidence=confidence,
            )


def contextual_name(value: str) -> dict[str, str] | None:
    match = CONTEXT_RE.match(value.strip())
    if match is None:
        return None
    name = match.group("name").strip()
    organization = match.group("organization").strip()
    if not name or not organization:
        return None
    return {
        "name": name,
        "organization": organization,
        "normalized_name": normalize_name(name),
        "normalized_organization": normalize_name(organization),
    }


def contexts_compatible(
    existing: dict[str, str] | None,
    candidate: dict[str, str],
) -> bool:
    if existing is None:
        return False
    if existing["normalized_name"] != candidate["normalized_name"]:
        return False
    existing_org = existing["normalized_organization"]
    candidate_org = candidate["normalized_organization"]
    return (
        existing_org == candidate_org
        or existing_org in candidate_org
        or candidate_org in existing_org
    )


def implicit_aliases(canonical_name: str) -> list[str]:
    context = contextual_name(canonical_name)
    if context is None:
        return []
    return [context["name"]]


def unique_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        stripped = value.strip()
        normalized = normalize_name(stripped)
        if not stripped or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(stripped)
    return result


def as_resolution_confidence(value: str) -> ResolutionConfidence:
    if value in {"low", "medium", "high"}:
        return value  # type: ignore[return-value]
    return "medium"
