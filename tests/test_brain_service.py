from __future__ import annotations

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import ingest_source, list_open_loops, profile_entity, recall, remember
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings


def test_family_fact_creates_single_card_entities_and_relationships(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(RememberRequest(input="Nur and Sara are my twin daughters."), settings)

    assert receipt.classification == "family_fact"
    assert len(receipt.memory_cards) == 1
    assert receipt.memory_cards[0].kind == "family_fact"
    assert receipt.memory_cards[0].statement == "Nur and Sara are Daniele's twin daughters."
    assert {entity.canonical_name for entity in receipt.entities} == {"Daniele", "Nur", "Sara"}
    assert {
        (relationship["predicate"], relationship["confidence"])
        for relationship in receipt.relationships
    } == {
        ("daughter_of", "high"),
        ("twin_of", "high"),
    }

    answer = recall(RecallRequest(query="Who are my daughters?"), settings)
    assert "Nur and Sara are Daniele's twin daughters" in answer.answer


def test_profile_preserves_relationship_direction_for_parent_profile(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    remember(RememberRequest(input="Nur and Sara are my twin daughters."), settings)

    profile = profile_entity(settings, name="Daniele")
    assert "Nur --daughter_of--> Daniele" in profile.answer
    assert "Sara --daughter_of--> Daniele" in profile.answer
    assert "daughter_of Nur" not in profile.answer
    assert "daughter_of Sara" not in profile.answer

    raw_profile = BrainStore(settings).entity_profile("Daniele")
    daughter_relationships = [
        relationship
        for relationship in raw_profile["relationships"]
        if relationship["predicate"] == "daughter_of"
    ]
    assert {
        (
            relationship["subject_name"],
            relationship["predicate"],
            relationship["object_name"],
            relationship["direction_relative_to_profile_entity"],
        )
        for relationship in daughter_relationships
    } == {
        ("Nur", "daughter_of", "Daniele", "incoming"),
        ("Sara", "daughter_of", "Daniele", "incoming"),
    }


def test_person_interaction_profile_is_entity_centric(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(
        RememberRequest(input="Sam from Goldman mentioned that he likes Bill Evans."),
        settings,
    )

    assert receipt.classification == "person_interaction"
    assert {entity.canonical_name for entity in receipt.entities} == {
        "Sam from Goldman",
        "Goldman",
        "Bill Evans",
    }
    assert {relationship["predicate"] for relationship in receipt.relationships} == {
        "associated_with",
        "likes",
    }

    profile = profile_entity(settings, name="Sam from Goldman")
    assert "Sam from Goldman" in profile.answer
    assert "Sam" in profile.answer
    assert "Sam from Goldman --associated_with--> Goldman" in profile.answer
    assert "Sam from Goldman --likes--> Bill Evans" in profile.answer


def test_open_question_creates_open_loop(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )

    assert receipt.classification == "open_question"
    assert receipt.open_loops[0]["status"] == "open"
    assert receipt.memory_cards[0].statement == "Daniele wants to learn more about knowledge graphs."

    loops = list_open_loops(settings, topic="knowledge graphs")
    assert len(loops) == 1
    assert loops[0]["topics"] == ["knowledge_graphs"]
    assert "knowledge graphs" in loops[0]["statement"]


def test_recall_hides_non_current_statuses_by_default(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    store = BrainStore(settings)
    memory_ids = {
        status: remember(
            RememberRequest(input=f"Visibility regression memory {status}."),
            settings,
        ).memory_cards[0].id
        for status in ["current", "deleted", "archived", "superseded"]
    }
    for status in ["deleted", "archived", "superseded"]:
        store.update_memory_status(memory_ids[status], status)

    response = recall(RecallRequest(query="visibility regression"), settings)

    assert {fact["memory_id"] for fact in response.facts} == {memory_ids["current"]}


def test_recall_include_superseded_keeps_deleted_and_rejected_hidden(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    store = BrainStore(settings)
    memory_ids = {
        status: remember(
            RememberRequest(input=f"Superseded visibility regression memory {status}."),
            settings,
        ).memory_cards[0].id
        for status in ["current", "superseded", "deleted", "rejected"]
    }
    for status in ["superseded", "deleted", "rejected"]:
        store.update_memory_status(memory_ids[status], status)

    response = recall(
        RecallRequest(query="superseded visibility regression", include_superseded=True),
        settings,
    )

    assert {fact["memory_id"] for fact in response.facts} == {
        memory_ids["current"],
        memory_ids["superseded"],
    }


def test_ingest_source_request_accepts_article_url(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path)

    class FakeResponse:
        text = """
        <html>
          <head><title>Fetched article title</title></head>
          <body><article><p>AI memory systems need durable source evidence.</p></article></body>
        </html>
        """

        def raise_for_status(self) -> None:
            return None

    def fake_get(url, **kwargs):
        assert url == "https://example.com/ai-memory"
        assert kwargs["follow_redirects"] is True
        return FakeResponse()

    monkeypatch.setattr("memory_stack.ingestion.article_loader.httpx.get", fake_get)

    receipt = ingest_source(
        IngestSourceRequest(
            source="https://example.com/ai-memory",
            source_kind="article",
            title="AI memory note",
            why_saved="Useful for memory design.",
        ),
        settings,
    )

    source = BrainStore(settings).get_source(receipt.source.source_id, include_text=True)
    assert receipt.classification == "article_url"
    assert receipt.source.created is True
    assert receipt.memory_cards[0].kind == "source_record"
    assert source["kind"] == "article"
    assert source["title"] == "AI memory note"
    assert source["uri"] == "https://example.com/ai-memory"
    assert source["text"] == ""
    assert source["metadata_json"]["raw_text_storage"] == "cognee"
    assert source["status"] == "processed"
    assert source["metadata_json"]["fetched"] is True
    assert source["metadata_json"]["why_saved"] == "Useful for memory design."
    sync_rows = BrainStore(settings).get_cognee_sync(receipt.memory_cards[0].id)
    assert {
        (row["object_type"], row["dataset"], row["status"])
        for row in sync_rows
    } == {("memory", "memory", "pending")}


def test_ingest_source_dry_run_does_not_write_rows(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = ingest_source(
        IngestSourceRequest(
            source="# Brain note\nKnowledge graphs matter for Brain.",
            source_kind="markdown",
            dry_run=True,
        ),
        settings,
    )

    assert receipt.dry_run is True
    assert receipt.source.created is True
    assert receipt.source.source_id is None
    assert BrainStore(settings).search_memory("knowledge graphs") == []


def test_table_source_creates_source_and_table_note(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    table = "\n".join(
        [
            "| Person | Preference |",
            "| --- | --- |",
            "| Sam | Bill Evans |",
            "| Daniele | Knowledge graphs |",
        ]
    )

    receipt = ingest_source(
        IngestSourceRequest(source=table, source_kind="table", title="Preferences"),
        settings,
    )

    source = BrainStore(settings).get_source(receipt.source.source_id)
    memory = BrainStore(settings).get_memory(receipt.memory_cards[0].id)
    assert receipt.classification == "table"
    assert source["kind"] == "table"
    assert source["metadata_json"]["columns"] == ["Person", "Preference"]
    assert source["metadata_json"]["row_count"] == 2
    assert memory["kind"] == "table_note"
    assert memory["metadata_json"]["sample_rows"][0] == {
        "Person": "Sam",
        "Preference": "Bill Evans",
    }


def test_transcript_source_preserves_participants(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    transcript = "\n".join(
        [
            "Daniele: We should keep Brain DB as source of truth.",
            "Sam: Cognee should stay rebuildable.",
            "Daniele: Add source-backed recall next.",
        ]
    )

    receipt = ingest_source(
        IngestSourceRequest(source=transcript, source_kind="transcript", title="Brain sync"),
        settings,
    )

    source = BrainStore(settings).get_source(receipt.source.source_id)
    assert receipt.classification == "transcript"
    assert source["kind"] == "transcript"
    assert source["metadata_json"]["participants"] == ["Daniele", "Sam"]
    assert source["metadata_json"]["turn_count"] == 3
    assert source["metadata_json"]["raw_text_storage"] == "cognee"
    assert receipt.memory_cards[0].kind == "source_record"


def test_markdown_source_record_stores_citation_metadata_without_raw_text(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    source_text = "# Anna Banti et Artemisia Gentileschi\n\nLong article body."

    receipt = ingest_source(
        IngestSourceRequest(
            source=source_text,
            source_kind="markdown",
            title="Anna Banti et Artemisia Gentileschi",
            metadata={
                "author": "Genesio",
                "journal": "Marges",
                "year": "2004",
            },
        ),
        settings,
    )

    store = BrainStore(settings)
    source = store.get_source(receipt.source.source_id, include_text=True)
    memory = store.get_memory(receipt.memory_cards[0].id)
    assert source["text"] == ""
    assert source["metadata_json"]["raw_text_storage"] == "cognee"
    assert source["metadata_json"]["raw_text_chars"] == len(source_text)
    assert memory["kind"] == "source_record"
    assert memory["statement"] == "Source stored: Anna Banti et Artemisia Gentileschi"
    assert memory["metadata_json"]["citation"] == (
        'Genesio. "Anna Banti et Artemisia Gentileschi". Marges. 2004'
    )


def brain_test_settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
