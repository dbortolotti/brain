from __future__ import annotations

import json
import re
from typing import Any

from memory_stack.brain_store import content_hash, normalize_name, stable_id
from memory_stack.config import Settings
from memory_stack.resolution.entity_resolver import EntityResolver
from memory_stack.taste.enrichment import TasteEnrichmentService
from memory_stack.taste.models import (
    TasteDescribeRequest,
    TasteLogDecisionRequest,
    TasteQueryRequest,
    TasteRefreshRequest,
    TasteRememberRequest,
)
from memory_stack.taste.ranking import build_grounding, rank_candidates, retrieve_candidates
from memory_stack.taste.routing import classify_taste_route, taste_domain_router
from memory_stack.taste.schema import ENTITY_TYPES, INTENTS, attribute_keys_for_type
from memory_stack.taste.store import TasteStore


class TasteService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = TasteStore(settings)
        self.brain_store = self.store.brain_store
        self.enrichment = TasteEnrichmentService(settings)

    def describe_item(self, request: TasteDescribeRequest) -> dict[str, Any]:
        existing = self._match_existing(request.canonical_name or request.item_text, request.entity_type)
        if existing["record"] is not None:
            return {
                "stored": False,
                "source": "memory",
                "found_existing": True,
                "record": existing["record"],
                "match": existing["match"],
                "needs_confirmation": [],
                "enriched": None,
                "suggested_remember_payload": None,
                "warnings": [],
                "server_llm_used": {"enrichment": False},
            }
        if existing["needs_confirmation"]:
            return {
                "stored": False,
                "source": "memory_confirmation_required",
                "found_existing": False,
                "record": None,
                "match": None,
                "needs_confirmation": existing["needs_confirmation"],
                "enriched": None,
                "suggested_remember_payload": None,
                "warnings": [],
                "server_llm_used": {"enrichment": False},
            }

        enriched = self.enrichment.describe_item(
            item_text=request.item_text,
            entity_type=request.entity_type,
            canonical_name=request.canonical_name,
            attributes=request.attributes,
            attribute_intervals_95=request.attribute_intervals_95,
            metadata=request.metadata,
            notes=request.notes,
            fetch_external_ratings=request.fetch_external_ratings,
            allow_broader_web_search=request.allow_broader_web_search,
        )
        return {
            "stored": False,
            "source": "read_only_enrichment",
            "found_existing": False,
            "record": None,
            "match": None,
            "needs_confirmation": [],
            "enriched": enriched,
            "suggested_remember_payload": self._suggest_remember_payload(enriched),
            "warnings": enriched["warnings"],
            "server_llm_used": {"enrichment": False},
        }

    def remember(self, request: TasteRememberRequest) -> dict[str, Any]:
        if request.type not in ENTITY_TYPES:
            raise ValueError(f"type must be one of: {', '.join(ENTITY_TYPES)}")
        if request.rating is not None and not 1 <= float(request.rating) <= 10:
            raise ValueError("rating must be between 1 and 10.")

        enriched = self.enrichment.describe_item(
            item_text=request.description,
            entity_type=request.type,
            canonical_name=request.canonical_name,
            attributes=request.attributes,
            attribute_intervals_95=request.attribute_intervals_95,
            metadata=request.metadata,
            notes=request.notes,
            fetch_external_ratings=request.fetch_external_ratings,
            allow_broader_web_search=request.allow_broader_web_search,
        )
        if (
            enriched["enrichment_status"] in {"failed", "skipped"}
            and not request.dry_run
            and not request.store_anyway
        ):
            proposal = self.create_proposal_for_request(request, enriched)
            return {
                "stored": False,
                "dry_run": True,
                "requires_confirmation": True,
                "proposal_id": proposal["id"],
                "proposal": proposal["proposal_json"],
                "warnings": proposal["warnings_json"],
                "enrichment": {
                    "status": enriched["enrichment_status"],
                    "sources": enriched["sources"],
                    "warnings": enriched["warnings"],
                },
                "server_llm_used": {"routing": False, "enrichment": False},
            }
        if request.dry_run:
            return {
                "stored": False,
                "dry_run": True,
                "taste_records_created": 0,
                "taste_records_updated": 0,
                "taste_records": [
                    {
                        "id": request.id or stable_id("dry_taste", request.type, request.canonical_name),
                        "type": request.type,
                        "canonical_name": request.canonical_name,
                        "attributes": enriched["attributes"],
                        "metadata": enriched["normalized_metadata"],
                    }
                ],
                "enrichment": {
                    "status": enriched["enrichment_status"],
                    "sources": enriched["sources"],
                    "warnings": enriched["warnings"],
                },
                "server_llm_used": {"routing": False, "enrichment": False},
            }

        entity, entity_created = self._resolve_taste_entity(
            request.type,
            request.canonical_name,
            enriched["normalized_metadata"],
        )
        projected = self._project_to_brain(
            request=request,
            taste_entity=entity,
            enrichment=enriched,
        )
        item_payload = {
            "id": request.id,
            "brain_entity_id": entity["id"],
            "type": request.type,
            "canonical_name": request.canonical_name,
            "source_text": request.description,
            "notes": request.notes or enriched.get("notes") or request.description,
            "metadata_json": enriched["normalized_metadata"],
            "enrichment_metadata_json": enriched["enrichment_metadata"],
            "enrichment_status": enriched["enrichment_status"],
            "attributes": enriched["attributes"],
            "attribute_intervals_95": enriched["attribute_intervals_95"],
            "signals": self._signals_for_request(request, projected),
        }
        taste_item, created = self.store.upsert_item(item_payload)
        self._attach_taste_metadata_to_memory(projected["memory_id"], taste_item["id"])

        return {
            "stored": True,
            "taste_records_created": 1 if created else 0,
            "taste_records_updated": 0 if created else 1,
            "taste_records": [
                {
                    "id": taste_item["id"],
                    "type": taste_item["type"],
                    "canonical_name": taste_item["canonical_name"],
                    "brain_entity_id": taste_item["brain_entity_id"],
                    "evidence_memory_id": projected["memory_id"],
                    "attributes": taste_item["attributes"],
                    "attribute_intervals_95": taste_item["attribute_intervals_95"],
                    "metadata": taste_item["metadata"],
                    "enrichment_metadata": taste_item["enrichment_metadata"],
                    "signals": taste_item["signals"],
                }
            ],
            "brain_projection": {
                "entity_id": entity["id"],
                "entity_created": entity_created,
                "memory_ids": [projected["memory_id"]],
                "relationship_ids": projected["relationship_ids"],
                "open_loop_ids": projected["open_loop_ids"],
                "closed_open_loop_ids": projected.get("closed_open_loop_ids", []),
                "open_loop_confirmation_proposal_ids": projected.get(
                    "open_loop_confirmation_proposal_ids",
                    [],
                ),
            },
            "enrichment": {
                "status": enriched["enrichment_status"],
                "sources": enriched["sources"],
                "warnings": enriched["warnings"],
            },
            "server_llm_used": {"routing": False, "enrichment": False},
        }

    def query(self, request: TasteQueryRequest) -> dict[str, Any]:
        intent = normalize_intent(request.intent or intent_from_query(request.query))
        extracted_entities = request.extracted_entities
        if extracted_entities is None and request.options_text:
            extracted_entities = extract_option_entities(
                request.options_text,
                intent.get("entity_type"),
            )
        retrieval = retrieve_candidates(self.store, intent, extracted_entities or [])
        feedback = self.store.decision_feedback(
            request.query,
            [entity["id"] for entity in retrieval["candidates"]],
        )
        ranked = rank_candidates(retrieval["candidates"], intent, decision_feedback=feedback)
        grounding = build_grounding(ranked)
        decision_id = self.store.log_decision(
            query=request.query,
            context=request.context,
            options=extracted_entities or [],
            ranked=grounding,
        )
        return {
            "decision_id": decision_id,
            "intent": intent,
            "extracted_entities": extracted_entities or [],
            "retrieval": describe_retrieval(retrieval),
            "ranked_results": grounding,
            "answer": render_taste_answer(grounding, retrieval),
            "explanation": detailed_ranking_explanation(ranked, intent)
            if request.explain
            else None,
            "server_llm_used": {
                "intent": False,
                "entity_extraction": False,
                "explanation": False,
            },
        }

    def evaluate_options(self, request: TasteQueryRequest) -> dict[str, Any]:
        if not request.options_text and not request.extracted_entities:
            raise ValueError("options_text or extracted_entities is required.")
        return self.query(request)

    def log_decision(self, request: TasteLogDecisionRequest) -> dict[str, Any]:
        if request.decision_id:
            changes = self.store.update_decision_choice(
                request.decision_id,
                request.chosen_taste_item_id,
            )
            if changes == 0:
                return {"logged": False, "error": f"No decision found for {request.decision_id}."}
            decision_id = request.decision_id
            updated = True
        else:
            decision_id = self.store.log_decision(
                query=request.query,
                context=request.context,
                options=[],
                ranked=[],
                chosen_taste_item_id=request.chosen_taste_item_id,
            )
            updated = False
        return {
            "logged": True,
            "decision_id": decision_id,
            "chosen_taste_item_id": request.chosen_taste_item_id,
            "updated_existing_decision": updated,
        }

    def create_proposal_from_text(
        self,
        text: str,
        *,
        route: dict[str, Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        route = route or taste_domain_router(text)
        if route.get("taste_intent") == "remember":
            request = remember_request_from_route(text, route)
            enriched = self.enrichment.describe_item(
                item_text=request.description,
                entity_type=request.type,
                canonical_name=request.canonical_name,
                attributes=request.attributes,
                attribute_intervals_95=request.attribute_intervals_95,
                metadata=request.metadata,
                notes=request.notes,
                fetch_external_ratings=False,
                allow_broader_web_search=False,
            )
            proposal = self._proposal_payload_for_request(request, enriched, route)
        else:
            proposal = {
                "route": route,
                "remember_payload": None,
                "query_payload": {"query": text} if route.get("taste_intent") == "query" else None,
                "proposed_taste_records": [],
                "proposed_brain_entities": [],
                "proposed_memory_cards": [],
                "proposed_relationships": [],
                "proposed_open_loops": [],
                "allowed_actions": ["confirm", "cancel", "correct"],
            }
        return self.store.create_proposal(
            original_text=text,
            proposal=proposal,
            warnings=route.get("ambiguity_reasons") or [],
            source_metadata=source_metadata or {},
        )

    def create_proposal_for_request(
        self,
        request: TasteRememberRequest,
        enriched: dict[str, Any],
    ) -> dict[str, Any]:
        route = {
            "domain": "taste",
            "taste_intent": "remember",
            "entity_type_hint": request.type,
            "confidence": enriched.get("confidence", 0.6),
            "requires_enrichment": True,
            "requires_confirmation": True,
            "ambiguity_reasons": enriched.get("warnings") or [],
        }
        proposal = self._proposal_payload_for_request(request, enriched, route)
        return self.store.create_proposal(
            original_text=request.description,
            proposal=proposal,
            warnings=enriched.get("warnings") or [],
            source_metadata={"source": request.source, "context": request.context},
        )

    def _proposal_payload_for_request(
        self,
        request: TasteRememberRequest,
        enriched: dict[str, Any],
        route: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "route": route,
            "remember_payload": request.model_dump(mode="json"),
            "query_payload": None,
            "proposed_taste_records": [
                {
                    "id": request.id
                    or stable_id(
                        "taste",
                        request.type,
                        normalize_name(request.canonical_name),
                    ),
                    "type": request.type,
                    "canonical_name": request.canonical_name,
                    "attributes": enriched.get("attributes") or {},
                    "attribute_intervals_95": enriched.get("attribute_intervals_95") or {},
                    "metadata": enriched.get("normalized_metadata") or {},
                    "enrichment_metadata_summary": enriched.get("enrichment_metadata") or {},
                }
            ],
            "proposed_brain_entities": [
                {
                    "id": stable_id("ent", request.type, normalize_name(request.canonical_name)),
                    "type": request.type,
                    "canonical_name": request.canonical_name,
                }
            ],
            "proposed_memory_cards": [
                {
                    "statement": taste_statement(request, self.settings.brain_owner_name),
                    "kind": "preference"
                    if request.recommended_by or request.wanted
                    else "experience",
                }
            ],
            "proposed_relationships": proposed_relationships_for_request(
                request,
                self.settings.brain_owner_name,
            ),
            "proposed_open_loops": proposed_open_loops_for_request(request),
            "allowed_actions": ["confirm", "cancel", "correct"],
            "broader_search_policy": (
                "Strict-source lookup did not verify this item. Broader web search "
                "requires explicit user approval; broad-web data stays in "
                "enrichment metadata unless category validation promotes it."
            ),
        }

    def confirm(self, proposal_id: str) -> dict[str, Any]:
        proposal = self._pending_proposal(proposal_id)
        payload = proposal["proposal_json"]
        remember_payload = payload.get("remember_payload")
        if not remember_payload:
            self.store.update_proposal(proposal_id, status="cancelled")
            return {"confirmed": False, "proposal_id": proposal_id, "error": "Nothing to confirm."}
        result = self.remember(
            TasteRememberRequest.model_validate(remember_payload).model_copy(
                update={"store_anyway": True}
            )
        )
        closure = payload.get("proposed_open_loop_closure") or {}
        closed_open_loop_id = None
        if closure.get("open_loop_id"):
            self.brain_store.update_open_loop_status(closure["open_loop_id"], "closed")
            closed_open_loop_id = closure["open_loop_id"]
        self.store.update_proposal(proposal_id, status="confirmed")
        return {
            "confirmed": True,
            "proposal_id": proposal_id,
            "closed_open_loop_id": closed_open_loop_id,
            "result": result,
        }

    def cancel(self, proposal_id: str) -> dict[str, Any]:
        proposal = self.store.get_proposal(proposal_id)
        if proposal is None:
            return {"cancelled": False, "proposal_id": proposal_id, "error": "Proposal not found."}
        self.store.update_proposal(proposal_id, status="cancelled")
        return {"cancelled": True, "proposal_id": proposal_id}

    def correct_proposal(self, proposal_id: str, correction: str) -> dict[str, Any]:
        proposal = self._pending_proposal(proposal_id)
        corrected_text = f"{proposal['original_text']} Correction: {correction}"
        route = taste_domain_router(corrected_text)
        base_request = TasteRememberRequest.model_validate(
            proposal["proposal_json"]["remember_payload"]
        )
        request = base_request
        request = apply_correction_to_request(request, correction)
        route = {
            **route,
            "entity_type_hint": request.type,
            "requires_enrichment": request.fetch_external_ratings,
            "requires_confirmation": True,
        }
        enriched = self.enrichment.describe_item(
            item_text=request.description,
            entity_type=request.type,
            canonical_name=request.canonical_name,
            attributes=request.attributes,
            attribute_intervals_95=request.attribute_intervals_95,
            metadata=request.metadata,
            notes=request.notes,
            fetch_external_ratings=request.fetch_external_ratings,
            allow_broader_web_search=request.allow_broader_web_search,
        )
        new_payload = self._proposal_payload_for_request(request, enriched, route)
        updated = self.store.update_proposal(
            proposal_id,
            proposal=new_payload,
            warnings=[
                *(route.get("ambiguity_reasons") or []),
                *(enriched.get("warnings") or []),
            ],
            correction_text=correction,
        )
        return {"corrected": True, "proposal": updated}

    def refresh_enrichment(self, request: TasteRefreshRequest) -> dict[str, Any]:
        item = self.store.get_item(request.taste_item_id)
        if item is None:
            return {"refreshed": False, "error": "Taste item not found."}
        previous = item.get("enrichment_metadata") or {}
        enriched = self.enrichment.describe_item(
            item_text=item.get("source_text") or item["canonical_name"],
            entity_type=item["type"],
            canonical_name=item["canonical_name"],
            metadata=item.get("metadata") or {},
            allow_broader_web_search=False,
        )
        next_metadata = enriched["normalized_metadata"]
        next_attributes = enriched["attributes"] or item.get("attributes") or {}
        next_intervals = (
            enriched["attribute_intervals_95"]
            or item.get("attribute_intervals_95")
            or {}
        )
        changed_fields = changed_enrichment_fields(
            item,
            next_metadata=next_metadata,
            next_attributes=next_attributes,
            next_intervals=next_intervals,
            next_status=enriched["enrichment_status"],
        )
        material_changes = material_enrichment_changes(
            item.get("metadata") or {},
            next_metadata,
        )
        self.store.upsert_item(
            {
                **item,
                "metadata_json": next_metadata,
                "enrichment_metadata_json": enriched["enrichment_metadata"],
                "enrichment_status": enriched["enrichment_status"],
                "attributes": next_attributes,
                "attribute_intervals_95": next_intervals,
            }
        )
        material_memory_id = None
        if material_changes:
            memory, _ = self.brain_store.upsert_memory_card(
                {
                    "kind": "experience",
                    "statement": (
                        f"Taste enrichment for {item['canonical_name']} changed: "
                        f"{', '.join(material_changes)}."
                    ),
                    "confidence": "high",
                    "metadata_json": {
                        "taste": True,
                        "taste_item_id": item["id"],
                        "taste_refresh": True,
                        "material_changes": material_changes,
                    },
                }
            )
            self.brain_store.link_memory_entity(
                memory_id=memory["id"],
                entity_id=item["brain_entity_id"],
                role="taste_item",
                confidence="high",
            )
            material_memory_id = memory["id"]
        return {
            "refreshed": True,
            "taste_record_id": item["id"],
            "previous_enrichment_checked_at": previous.get("checked_at"),
            "new_enrichment_checked_at": enriched["enrichment_metadata"].get("checked_at"),
            "changed_fields": changed_fields,
            "material_changes": material_changes,
            "material_memory_id": material_memory_id,
            "warnings": enriched["warnings"],
        }

    def _resolve_taste_entity(
        self,
        entity_type: str,
        canonical_name: str,
        metadata: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        resolver = EntityResolver(self.brain_store)
        resolution = resolver.resolve_entity(
            entity_type=entity_type,
            canonical_name=canonical_name,
            confidence="high",
            metadata_json={"taste": True, **metadata},
        )
        return resolution.entity, resolution.created

    def _project_to_brain(
        self,
        *,
        request: TasteRememberRequest,
        taste_entity: dict[str, Any],
        enrichment: dict[str, Any],
    ) -> dict[str, Any]:
        statement = taste_statement(request, self.settings.brain_owner_name)
        memory, _ = self.brain_store.upsert_memory_card(
            {
                "kind": "preference" if request.recommended_by or request.wanted else "experience",
                "statement": statement,
                "confidence": "high",
                "metadata_json": {
                    "taste": True,
                    "taste_type": request.type,
                    "enrichment_status": enrichment["enrichment_status"],
                    "source": request.source,
                    **request.context,
                },
            }
        )
        self.brain_store.link_memory_entity(
            memory_id=memory["id"],
            entity_id=taste_entity["id"],
            role="taste_item",
            confidence="high",
        )
        projection_hash = content_hash(memory["id"], memory["statement"], memory["status"])
        self.brain_store.mark_cognee_pending(
            object_type="memory",
            object_id=memory["id"],
            dataset=self.settings.brain_cognee_memory_dataset,
            projection_hash=projection_hash,
        )

        relationship_ids = []
        open_loop_ids = []
        subject = None
        predicate = None
        if request.recommended_by:
            person = self.brain_store.upsert_entity(
                entity_type="person",
                canonical_name=request.recommended_by,
                confidence="high",
            )[0]
            self.brain_store.link_memory_entity(
                memory_id=memory["id"],
                entity_id=person["id"],
                role="recommender",
                confidence="high",
            )
            subject = person
            predicate = "recommended"
        elif request.wanted:
            subject = self._owner_entity()
            predicate = wanted_predicate(request.type)
        elif request.rating is not None:
            subject = self._owner_entity()
            predicate = "rated"
        elif request.disliked or request.avoid or request.not_my_style or request.bad_fit:
            subject = self._owner_entity()
            predicate = negative_predicate(request)
        elif request.tried or request.watched or request.listened:
            subject = self._owner_entity()
            predicate = "experienced"

        if subject is not None and predicate is not None:
            rel, _ = self.brain_store.create_relationship(
                subject_entity_id=subject["id"],
                predicate=predicate,
                object_entity_id=taste_entity["id"],
                evidence_memory_id=memory["id"],
                confidence="high",
                metadata_json={"taste": True},
            )
            relationship_ids.append(rel["id"])

        if request.wanted:
            loop, _ = self.brain_store.create_open_loop(
                memory_id=memory["id"],
                metadata_json={"taste": True, "taste_type": request.type},
            )
            open_loop_ids.append(loop["id"])
        closed = {"closed_open_loop_ids": [], "open_loop_confirmation_proposal_ids": []}
        if request.tried or request.watched or request.listened or request.rating is not None:
            closed = self._close_matching_open_loops(request)

        return {
            "memory_id": memory["id"],
            "relationship_ids": relationship_ids,
            "open_loop_ids": open_loop_ids,
            **closed,
        }

    def _signals_for_request(
        self,
        request: TasteRememberRequest,
        projected: dict[str, Any],
    ) -> list[dict[str, Any]]:
        signals = []
        if request.rating is not None:
            signals.append(
                {
                    "type": "rating",
                    "value": float(request.rating),
                    "provenance_memory_id": projected["memory_id"],
                    "source": request.source,
                }
            )
        if request.tried or request.rating is not None:
            signals.append(
                {
                    "type": "tried",
                    "value": True,
                    "provenance_memory_id": projected["memory_id"],
                    "source": request.source,
                }
            )
        if request.watched:
            signals.append(
                {
                    "type": "watched",
                    "value": True,
                    "provenance_memory_id": projected["memory_id"],
                    "source": request.source,
                }
            )
        if request.listened:
            signals.append(
                {
                    "type": "listened",
                    "value": True,
                    "provenance_memory_id": projected["memory_id"],
                    "source": request.source,
                }
            )
        if request.wanted:
            signals.append(
                {
                    "type": wanted_signal_type(request.type),
                    "value": True,
                    "provenance_memory_id": projected["memory_id"],
                    "source": request.source,
                }
            )
        for field, signal_type in {
            "disliked": "disliked",
            "avoid": "avoid",
            "not_my_style": "not_my_style",
            "bad_fit": "bad_fit",
        }.items():
            if getattr(request, field):
                signals.append(
                    {
                        "type": signal_type,
                        "value": True,
                        "provenance_memory_id": projected["memory_id"],
                        "source": request.source,
                    }
                )
        if request.recommended_by:
            signals.append(
                {
                    "type": "recommended_by",
                    "value": request.recommended_by,
                    "provenance_memory_id": projected["memory_id"],
                    "source": request.source,
                }
            )
        return signals

    def _owner_entity(self) -> dict[str, Any]:
        return self.brain_store.upsert_entity(
            entity_type="person",
            canonical_name=self.settings.brain_owner_name,
            confidence="high",
        )[0]

    def _close_matching_open_loops(self, request: TasteRememberRequest) -> dict[str, list[str]]:
        closed_ids: list[str] = []
        proposal_ids: list[str] = []
        for loop in self.brain_store.list_open_loops(
            topic=request.canonical_name,
            status="open",
            limit=20,
        ):
            confidence = open_loop_match_confidence(request.canonical_name, loop["statement"])
            if confidence >= self.settings.brain_taste_open_loop_close_threshold:
                self.brain_store.update_open_loop_status(loop["id"], "closed")
                closed_ids.append(loop["id"])
                continue
            if confidence >= self.settings.brain_taste_open_loop_confirmation_threshold:
                proposal = self.store.create_proposal(
                    original_text=request.description,
                    proposal={
                        "route": {
                            "domain": "taste",
                            "taste_intent": "remember",
                            "entity_type_hint": request.type,
                            "confidence": confidence,
                            "requires_enrichment": False,
                            "requires_confirmation": True,
                            "ambiguity_reasons": [
                                "Completion may close a matching taste open loop."
                            ],
                        },
                        "remember_payload": request.model_dump(mode="json"),
                        "proposed_open_loop_closure": {
                            "open_loop_id": loop["id"],
                            "statement": loop["statement"],
                            "confidence": round(confidence, 3),
                        },
                        "allowed_actions": ["confirm", "cancel", "correct"],
                    },
                    warnings=["Confirm before closing the matching taste open loop."],
                )
                proposal_ids.append(proposal["id"])
        return {
            "closed_open_loop_ids": closed_ids,
            "open_loop_confirmation_proposal_ids": proposal_ids,
        }

    def _attach_taste_metadata_to_memory(self, memory_id: str, taste_item_id: str) -> None:
        memory = self.brain_store.get_memory(memory_id)
        if memory is None:
            return
        metadata = dict(memory.get("metadata_json") or {})
        metadata["taste_item_id"] = taste_item_id
        with self.brain_store.engine.begin() as conn:
            from memory_stack import brain_schema as brain_schema
            from sqlalchemy import update

            conn.execute(
                update(brain_schema.memory_cards)
                .where(brain_schema.memory_cards.c.id == memory_id)
                .values(metadata_json=metadata)
            )

    def _match_existing(self, name: str, entity_type: str) -> dict[str, Any]:
        matches = self.store.match_entities_by_names([name])
        typed = [
            match
            for match in matches.get("matches", [])
            if self.store.get_item(match["matched_id"]) is not None
            and self.store.get_item(match["matched_id"])["type"] == entity_type
        ]
        if not typed:
            return {"record": None, "match": None, "needs_confirmation": []}
        best = max(typed, key=lambda match: float(match.get("confidence") or 0))
        record = self.store.get_item(best["matched_id"])
        if best.get("needs_confirmation"):
            return {"record": None, "match": None, "needs_confirmation": [best]}
        return {"record": record, "match": best, "needs_confirmation": []}

    def _pending_proposal(self, proposal_id: str) -> dict[str, Any]:
        proposal = self.store.get_proposal(proposal_id)
        if proposal is None:
            raise ValueError(f"Proposal not found: {proposal_id}")
        if proposal["status"] != "pending":
            raise ValueError(f"Proposal is not pending: {proposal['status']}")
        expires_at = proposal.get("expires_at")
        if expires_at is not None:
            from memory_stack.brain_store import as_utc, now_utc

            if as_utc(expires_at) < now_utc():
                self.store.update_proposal(proposal_id, status="expired")
                raise ValueError("Proposal has expired and must be regenerated.")
        return proposal

    def _suggest_remember_payload(self, enriched: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": enriched["entity_type"],
            "canonical_name": enriched["canonical_name"],
            "description": enriched.get("notes") or enriched["canonical_name"],
            "attributes": enriched["attributes"],
            "attribute_intervals_95": enriched["attribute_intervals_95"],
            "metadata": enriched["normalized_metadata"],
            "fetch_external_ratings": False,
        }


def remember_request_from_route(text: str, route: dict[str, Any]) -> TasteRememberRequest:
    extracted = route.get("extracted") or {}
    item = extracted.get("item") or text
    entity_type = route.get("entity_type_hint") or "experience"
    return TasteRememberRequest(
        type=entity_type,
        canonical_name=item,
        description=text,
        rating=extracted.get("rating"),
        tried=bool(extracted.get("tried")),
        watched=bool(extracted.get("watched")),
        listened=bool(extracted.get("listened")),
        wanted=bool(extracted.get("wanted")),
        recommended_by=extracted.get("recommended_by"),
        disliked=bool(extracted.get("disliked")),
        avoid=bool(extracted.get("avoid")),
        not_my_style=bool(extracted.get("not_my_style")),
        bad_fit=bool(extracted.get("bad_fit")),
    )


def apply_correction_to_request(
    request: TasteRememberRequest,
    correction: str,
) -> TasteRememberRequest:
    updates: dict[str, Any] = {}
    kind = category_from_correction(correction)
    if kind:
        updates["type"] = kind

    vintage = vintage_from_correction(correction)
    if vintage:
        updates["canonical_name"] = corrected_vintage_name(request.canonical_name, vintage)

    corrected_name = canonical_name_from_correction(correction)
    if corrected_name:
        updates["canonical_name"] = corrected_name

    if broad_web_search_requested(correction):
        updates["allow_broader_web_search"] = True
        updates["fetch_external_ratings"] = True

    return request.model_copy(update=updates) if updates else request


def category_from_correction(correction: str) -> str | None:
    lower = correction.casefold()
    category_pattern = "|".join(re.escape(kind) for kind in ENTITY_TYPES)
    explicit = re.search(
        rf"\b(?:category|type)\s+(?:is|=|to)\s+(?P<kind>{category_pattern})\b",
        lower,
    )
    if explicit:
        return explicit.group("kind")
    this_is = re.search(rf"\bthis\s+is\s+(?:a|an)?\s*(?P<kind>{category_pattern})\b", lower)
    if this_is:
        return this_is.group("kind")
    for kind in ENTITY_TYPES:
        if re.search(rf"(?<!not\s)\b{re.escape(kind)}\b", lower):
            return kind
    return None


def vintage_from_correction(correction: str) -> str | None:
    match = re.search(
        r"\b(?:vintage|year)\s+(?:is|=|to)\s+(?P<vintage>(?:19|20)\d{2})\b",
        correction,
        re.IGNORECASE,
    )
    return match.group("vintage") if match else None


def canonical_name_from_correction(correction: str) -> str | None:
    match = re.search(
        r"\b(?:item|name|canonical\s+name)\s+(?:is|=|to)\s+(?P<name>[^.;]+)",
        correction,
        re.IGNORECASE,
    )
    if not match:
        return None
    name = match.group("name").strip(" \"'")
    return name or None


def broad_web_search_requested(correction: str) -> bool:
    lower = correction.casefold()
    return any(
        phrase in lower
        for phrase in (
            "broader web",
            "broad web",
            "web search",
            "search the web",
            "search online",
            "look online",
        )
    )


def corrected_vintage_name(canonical_name: str, vintage: str) -> str:
    if re.search(r"\b(?:19|20)\d{2}\b", canonical_name):
        return re.sub(r"\b(?:19|20)\d{2}\b", vintage, canonical_name, count=1)
    return f"{canonical_name} {vintage}"


def remember_request_from_text(
    text: str,
    *,
    settings: Settings,
    llm_client: Any = None,
) -> TasteRememberRequest | None:
    route = classify_taste_route(text, settings=settings, llm_client=llm_client)
    if route.get("taste_intent") != "remember" or route.get("domain") != "taste":
        return None
    return remember_request_from_route(text, route)


def normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    entity_type = intent.get("entity_type") if intent.get("entity_type") in ENTITY_TYPES else None
    allowed = set(attribute_keys_for_type(entity_type))
    filters = intent.get("filters") if isinstance(intent.get("filters"), dict) else {}
    return {
        "intent": intent.get("intent") if intent.get("intent") in INTENTS else "hybrid_query",
        "attributes": [item for item in intent.get("attributes") or [] if item in allowed],
        "context": {
            key: bool(value)
            for key, value in (intent.get("context") or {}).items()
            if key in allowed and value
        },
        "filters": {
            "min_rating": filters.get("min_rating"),
            "recommended_by": filters.get("recommended_by"),
            "cuisine": filters.get("cuisine") or [],
        },
        "entity_type": entity_type,
        "search_text": str(intent.get("search_text") or ""),
    }


def intent_from_query(query: str) -> dict[str, Any]:
    lower = query.casefold()
    entity_type = None
    for kind in ENTITY_TYPES:
        if kind in lower or f"{kind}s" in lower:
            entity_type = kind
            break
    attributes = [
        attr
        for attr in attribute_keys_for_type(entity_type)
        if attr.replace("_", " ") in lower or attr in lower
    ]
    return {
        "intent": "contextual_decision" if "should" in lower or "which" in lower else "hybrid_query",
        "attributes": attributes,
        "context": {},
        "filters": {
            "min_rating": None,
            "recommended_by": recommended_by_from_query(query),
            "cuisine": [],
        },
        "entity_type": entity_type,
        "search_text": query,
    }


def recommended_by_from_query(query: str) -> str | None:
    marker = "recommended by "
    lower = query.casefold()
    if marker not in lower:
        return None
    tail = query[lower.index(marker) + len(marker) :]
    return tail.split("?", 1)[0].strip() or None


def extract_option_entities(options_text: str, entity_type: str | None) -> list[dict[str, Any]]:
    return [
        {"canonical_name": line.strip("-* \t"), "type": entity_type, "source_text": line.strip()}
        for line in options_text.splitlines()
        if line.strip("-* \t")
    ]


def describe_retrieval(retrieval: dict[str, Any]) -> dict[str, Any]:
    return {
        "constrained_to_options": retrieval["constrained_to_options"],
        "unmatched_options": retrieval["unmatched_options"],
        "option_matches": retrieval.get("option_matches", []),
        "needs_confirmation": retrieval.get("needs_confirmation", []),
        "candidate_count": len(retrieval["candidates"]),
    }


def detailed_ranking_explanation(
    ranked: list[dict[str, Any]],
    intent: dict[str, Any],
) -> dict[str, Any]:
    from dataclasses import asdict

    from memory_stack.taste.ranking import DEFAULT_WEIGHTS

    return {
        "weights": asdict(DEFAULT_WEIGHTS),
        "filters": intent.get("filters") or {},
        "attributes": intent.get("attributes") or [],
        "candidates": [
            {
                "id": result["entity"]["id"],
                "name": result["entity"]["canonical_name"],
                "score": result["score"],
                "components": {
                    key: value
                    for key, value in result["facts"].items()
                    if key
                    in {
                        "preference",
                        "attribute_match",
                        "cuisine_match",
                        "context_match",
                        "search_match",
                        "provenance",
                        "familiarity",
                        "decision_feedback",
                        "penalties",
                        "external_rating_tiebreak",
                    }
                },
                "matched_attributes": result["facts"].get("matched_attributes", []),
                "negative_signals": result["facts"].get("negative_signals", []),
                "signal_facts": result["facts"].get("signal_facts", []),
                "attribute_intervals_95": result["entity"].get("attribute_intervals_95") or {},
                "evidence_ids": [
                    signal.get("provenance_memory_id")
                    for signal in result["entity"].get("signals") or []
                    if signal.get("provenance_memory_id")
                ],
            }
            for result in ranked
        ],
    }


def render_taste_answer(grounding: list[dict[str, Any]], retrieval: dict[str, Any]) -> str:
    if not grounding:
        if retrieval.get("unmatched_options"):
            return "No supplied options matched saved taste records."
        return "No matching taste records found."
    top = grounding[0]
    return f"{top['name']} is the strongest match."


def changed_enrichment_fields(
    item: dict[str, Any],
    *,
    next_metadata: dict[str, Any],
    next_attributes: dict[str, Any],
    next_intervals: dict[str, Any],
    next_status: str,
) -> list[str]:
    changed = []
    if normalize_jsonable(item.get("metadata") or {}) != normalize_jsonable(next_metadata):
        changed.append("metadata")
    if normalize_jsonable(item.get("attributes") or {}) != normalize_jsonable(next_attributes):
        changed.append("attributes")
    if normalize_jsonable(item.get("attribute_intervals_95") or {}) != normalize_jsonable(next_intervals):
        changed.append("attribute_intervals_95")
    if item.get("enrichment_status") != next_status:
        changed.append("enrichment_status")
    return changed


def material_enrichment_changes(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    changes: list[str] = []
    michelin_paths = [
        ("michelin", "stars"),
        ("michelin", "status"),
        ("michelin", "green_star"),
    ]
    for path in michelin_paths:
        if nested_value(previous, path) != nested_value(current, path):
            changes.append(".".join(path))

    previous_google = nested_float(previous, ("google", "rating"))
    current_google = nested_float(current, ("google", "rating"))
    if previous_google is not None and current_google is not None:
        if abs(current_google - previous_google) >= 0.3:
            changes.append("google.rating")
    elif previous_google != current_google:
        changes.append("google.rating")

    previous_count = nested_float(previous, ("google", "rating_count"))
    current_count = nested_float(current, ("google", "rating_count"))
    if previous_count is not None and current_count is not None:
        count_delta = abs(current_count - previous_count)
        denominator = max(previous_count, 1.0)
        if count_delta >= 500 or count_delta / denominator >= 0.25:
            changes.append("google.rating_count")
    elif previous_count != current_count:
        changes.append("google.rating_count")

    previous_imdb = nested_float(previous, ("external_ratings", "imdb", "rating"))
    current_imdb = nested_float(current, ("external_ratings", "imdb", "rating"))
    if previous_imdb is not None and current_imdb is not None:
        if abs(current_imdb - previous_imdb) >= 0.3:
            changes.append("external_ratings.imdb.rating")
    elif previous_imdb != current_imdb:
        changes.append("external_ratings.imdb.rating")

    previous_rt = nested_float(
        previous,
        ("external_ratings", "rotten_tomatoes", "critic_score"),
    )
    current_rt = nested_float(
        current,
        ("external_ratings", "rotten_tomatoes", "critic_score"),
    )
    if previous_rt is not None and current_rt is not None:
        if abs(current_rt - previous_rt) >= 10:
            changes.append("external_ratings.rotten_tomatoes.critic_score")
    elif previous_rt != current_rt:
        changes.append("external_ratings.rotten_tomatoes.critic_score")

    for key in ("runtime", "seasons", "country", "language", "genre"):
        if normalize_jsonable(previous.get(key)) != normalize_jsonable(current.get(key)):
            changes.append(key)

    return list(dict.fromkeys(changes))


def nested_value(mapping: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def nested_float(mapping: dict[str, Any], path: tuple[str, ...]) -> float | None:
    value = nested_value(mapping, path)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_jsonable(value: Any) -> str:
    return json.dumps(value or {}, sort_keys=True, default=str)


def taste_statement(request: TasteRememberRequest, owner_name: str = "Daniele") -> str:
    name = request.canonical_name
    if request.recommended_by:
        return f"{request.recommended_by} recommended {name}."
    if request.wanted:
        return f"{owner_name} wants to {wanted_verb(request.type)} {name}."
    if request.rating is not None:
        return f"{owner_name} rated {name} {float(request.rating):g}/10."
    if request.watched:
        return f"{owner_name} watched {name}."
    if request.tried:
        return f"{owner_name} tried {name}."
    return request.description.strip().rstrip(".") + "."


def wanted_signal_type(entity_type: str) -> str:
    if entity_type in {"movie", "series"}:
        return "wanted_to_watch"
    if entity_type == "music":
        return "wanted_to_listen"
    return "wanted_to_try"


def wanted_predicate(entity_type: str) -> str:
    return wanted_signal_type(entity_type)


def negative_predicate(request: TasteRememberRequest) -> str:
    if request.avoid:
        return "avoids"
    if request.not_my_style:
        return "not_my_style"
    if request.bad_fit:
        return "bad_fit"
    return "disliked"


def proposed_relationships_for_request(
    request: TasteRememberRequest,
    owner_name: str,
) -> list[dict[str, Any]]:
    if request.recommended_by:
        return [
            {
                "subject": request.recommended_by,
                "predicate": "recommended",
                "object": request.canonical_name,
            }
        ]
    predicate = None
    if request.wanted:
        predicate = wanted_predicate(request.type)
    elif request.rating is not None:
        predicate = "rated"
    elif request.disliked or request.avoid or request.not_my_style or request.bad_fit:
        predicate = negative_predicate(request)
    elif request.tried or request.watched or request.listened:
        predicate = "experienced"
    if predicate is None:
        return []
    return [
        {
            "subject": owner_name,
            "predicate": predicate,
            "object": request.canonical_name,
        }
    ]


def proposed_open_loops_for_request(request: TasteRememberRequest) -> list[dict[str, Any]]:
    if not request.wanted:
        return []
    return [
        {
            "text": f"{wanted_verb(request.type).capitalize()} {request.canonical_name}.",
            "signal_type": wanted_signal_type(request.type),
        }
    ]


def wanted_verb(entity_type: str) -> str:
    if entity_type in {"movie", "series"}:
        return "watch"
    if entity_type == "music":
        return "listen to"
    return "try"


def open_loop_match_confidence(canonical_name: str, statement: str) -> float:
    normalized_name = normalize_name(canonical_name)
    normalized_statement = normalize_name(statement)
    if not normalized_name or not normalized_statement:
        return 0.0
    if normalized_name in normalized_statement:
        return 1.0
    name_tokens = set(normalized_name.split())
    statement_tokens = set(normalized_statement.split())
    if not name_tokens:
        return 0.0
    return len(name_tokens & statement_tokens) / len(name_tokens)
