from __future__ import annotations

from memory_stack.brain_models import RememberRequest
from memory_stack.brain_service import remember
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.resolution.entity_resolver import EntityResolver


def test_contextual_goldman_variants_resolve_same_person(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    first = remember(
        RememberRequest(input="Sam from Goldman mentioned that he likes Bill Evans."),
        settings,
    )
    second = remember(
        RememberRequest(input="Sam at Goldman Sachs mentioned that he likes Sonny Rollins."),
        settings,
    )

    first_sam = person_entity(first.entities, "Sam from Goldman")
    second_sam = person_entity(second.entities, "Sam from Goldman")
    assert first_sam.id == second_sam.id
    assert second_sam.created is False

    aliases = {
        alias["alias"]
        for alias in BrainStore(settings).get_entity(first_sam.id)["aliases"]
    }
    assert {"Sam", "Sam from Goldman Sachs"} <= aliases

    slash = EntityResolver(BrainStore(settings)).resolve_entity(
        entity_type="person",
        canonical_name="Sam / Goldman",
    )
    assert slash.entity_id == first_sam.id


def test_contextual_people_at_different_organizations_do_not_merge(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    first = remember(
        RememberRequest(input="Sam from Goldman mentioned that he likes Bill Evans."),
        settings,
    )
    second = remember(
        RememberRequest(input="Sam from Point72 mentioned that he likes Sonny Rollins."),
        settings,
    )

    first_sam = person_entity(first.entities, "Sam from Goldman")
    second_sam = person_entity(second.entities, "Sam from Point72")
    assert first_sam.id != second_sam.id
    assert second_sam.created is True


def test_alias_lookup_resolves_existing_entity(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    resolver = EntityResolver(BrainStore(settings))

    created = resolver.resolve_entity(
        entity_type="person",
        canonical_name="William Evans",
        aliases=["Bill Evans"],
        confidence="high",
    )
    matched = resolver.resolve_entity(
        entity_type="person",
        canonical_name="Bill Evans",
        confidence="medium",
    )

    assert created.action == "created"
    assert matched.entity_id == created.entity_id
    assert matched.action == "alias_added"


def test_low_confidence_ambiguity_is_stored_not_guessed(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    resolver = EntityResolver(BrainStore(settings))

    goldman = resolver.resolve_entity(
        entity_type="person",
        canonical_name="Sam from Goldman",
    )
    point72 = resolver.resolve_entity(
        entity_type="person",
        canonical_name="Sam from Point72",
    )
    ambiguous = resolver.resolve_entity(
        entity_type="person",
        canonical_name="Sam",
    )

    assert ambiguous.action == "ambiguous"
    assert ambiguous.confidence == "low"
    assert ambiguous.entity_id not in {goldman.entity_id, point72.entity_id}
    ambiguity = ambiguous.entity["metadata_json"]["resolution_ambiguity"]
    assert ambiguity["candidate_entity_ids"] == sorted([goldman.entity_id, point72.entity_id])


def person_entity(entities, canonical_name: str):
    for entity in entities:
        if entity.type == "person" and entity.canonical_name == canonical_name:
            return entity
    raise AssertionError(f"person entity not found: {canonical_name}")


def brain_test_settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
