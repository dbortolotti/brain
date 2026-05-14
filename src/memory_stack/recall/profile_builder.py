from __future__ import annotations

from memory_stack.brain_models import RecallResponse
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.recall.evidence_builder import build_evidence, build_facts


def build_profile_response(
    name: str,
    settings: Settings,
    *,
    entity_type: str | None = None,
    include_superseded: bool = False,
    include_conflicts: bool = True,
) -> RecallResponse | None:
    store = BrainStore(settings)
    profile = store.entity_profile(
        name,
        entity_type=entity_type,
        include_superseded=include_superseded,
        include_conflicts=include_conflicts,
    )
    if profile is None:
        return None

    entity = profile["entity"]
    memories = profile["memories"]
    relationships = profile["relationships"]
    facts = build_facts(memories)
    evidence = build_evidence(memories)
    lines = [entity["canonical_name"], "Identity"]
    lines.append(f"- {entity['type']}; confidence {entity['confidence']}.")
    if profile["aliases"]:
        alias_names = sorted({alias["alias"] for alias in profile["aliases"]})
        lines.append(f"- Aliases: {', '.join(alias_names)}.")
    lines.append("Known facts")
    known = [
        memory
        for memory in memories
        if memory["kind"] not in {"person_interaction", "open_question"}
    ]
    lines.extend([f"- {memory['statement']} [{memory['id']}]" for memory in known] or ["- None known."])
    lines.append("Interactions")
    interactions = [memory for memory in memories if memory["kind"] == "person_interaction"]
    lines.extend(
        [f"- {memory['statement']} [{memory['id']}]" for memory in interactions]
        or ["- None known."]
    )
    lines.append("Relationships")
    lines.extend(
        [
            f"- {relationship['subject_name']} --{relationship['predicate']}--> "
            f"{relationship['object_name']} [evidence: {relationship['evidence_memory_id']}]"
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
