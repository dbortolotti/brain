#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


COARSE_BRIEFS = {
    "router": "Classify incoming user intent and route messages to recall, ingestion, debug/admin, or no-op paths.",
    "slack_intake": "Convert Slack messages into safe ingestion decisions and user-facing receipts without committing low-value, ambiguous, or unsafe memories.",
    "memory_compiler": "Turn notes, articles, summaries, transcripts, and structured sources into atomic memory cards while preserving source boundaries and avoiding invention.",
    "entity_resolution": "Resolve entity mentions and candidate identities while preferring clarification over unsafe merges.",
    "conflict_handling": "Detect candidate conflicts and explain contradiction, correction, supersession, duplicate, or additive relationships without silently overwriting facts.",
    "recall": "Plan retrieval and synthesize grounded answers from DB/Cognee results without returning deleted/superseded facts as current.",
    "debug": "Explain recall plans, filtered candidates, and sync/debug state for operators.",
    "judge": "Offline model-output quality judging; not part of normal runtime.",
    "embeddings": "Embedding model coverage for retrieval tests.",
}

FINE_BRIEFS = {
    "intent_router": "Classify intent across router, Slack intake, memory compiler, recall, and debug/admin flows.",
    "source_classifier": "Identify source type and source/material boundaries before extraction.",
    "durability_filter": "Decide whether input contains durable memory value or should be rejected as junk, vague, unresolved, or non-committable.",
    "memory_kind_classifier": "Classify candidate memory kind and avoid unsafe splitting or merging of facts.",
    "repair_option_generator": "Propose safe user-facing repair options when clarification or conflict resolution is required.",
    "success_receipt_generator": "Produce concise user-facing confirmations for successful Slack or memory operations.",
    "commit_policy_decider": "Decide whether a validated proposal can commit, must ask, or must be rejected.",
    "success_receipt_template": "Render required success receipt fields from deterministic ingestion data rather than model-authored prose.",
    "zero_tolerance_validator": "Enforce non-negotiable safety checks before memory output is accepted.",
    "commit_policy": "Decide whether validated intake output can be committed.",
    "atomic_card_extractor": "Extract atomic memory cards from durable source material without inventing unsupported facts or collapsing long sources into one card.",
    "entity_mention_extractor": "Extract explicit entity mentions, aliases, types, and roles without inventing identities.",
    "relationship_extractor": "Extract directed relationships and attributes between entities without inverting meaning or altering numeric values.",
    "open_loop_detector": "Detect unresolved questions, todos, and open loops that should remain explicit rather than becoming false facts.",
    "table_policy_handler": "Decide how small and large tables should be handled without dropping values, atomizing large tables by default, or changing numbers.",
    "source_takeaway_extractor": "Extract grounded takeaways from source documents while preserving evidence boundaries and avoiding source invention.",
    "table_parser": "Parse table structure before model-facing interpretation.",
    "source_loader": "Load and normalize source material before extraction.",
    "entity_candidate_ranker": "Rank candidate entity matches while avoiding unsafe overmerge.",
    "entity_final_resolver": "Make the final entity resolution choice from ranked candidates and evidence.",
    "conflict_candidate_detector": "Detect memories that may duplicate, supersede, correct, or contradict existing facts.",
    "conflict_explainer": "Explain conflict type and evidence without making the final policy decision or silently overwriting current facts.",
    "conflict_policy_decider": "Choose ask, keep, duplicate, reject, or supersede policy from conflict evidence.",
    "recall_planner": "Plan retrieval scope and query strategy without dumping irrelevant memory or making unsupported absence claims.",
    "recall_relevance_filter": "Filter and order visible recall candidates by query relevance after hard status filtering.",
    "recall_synthesizer": "Synthesize grounded answers from retrieved memory records without unsupported inference, irrelevant dumps, or stale deleted facts.",
    "recall_status_filter": "Filter deleted, rejected, archived, or superseded records before model-facing relevance filtering.",
    "recall_filter": "Filter deleted, superseded, irrelevant, or unauthorized records before synthesis.",
    "debug_explainer": "Explain internal retrieval, filtering, and sync state for debugging while avoiding exposure of raw private source content.",
    "eval_judge": "Judge model output quality offline for eval reporting and adjudication; not part of normal runtime.",
    "embeddings": "Produce embeddings for retrieval tests.",
}

FINE_BRIEFS_BY_COARSE = {
    ("slack_intake", "zero_tolerance_validator"): "Enforce non-negotiable safety checks before any memory commit.",
    ("memory_compiler", "zero_tolerance_validator"): "Enforce non-negotiable safety checks before memory output is accepted.",
}


def extract_decision_section(registry_text: str, section_name: str) -> dict[str, str]:
    pattern = re.compile(rf"^  {re.escape(section_name)}:\n(?P<body>(?:    .+\n|      .+\n)+)", re.MULTILINE)
    match = pattern.search(registry_text)
    if not match:
        return {}

    models: dict[str, str] = {}
    current_role: str | None = None
    for line in match.group("body").splitlines():
        role_match = re.match(r"^    ([A-Za-z0-9_]+):\s*$", line)
        if role_match:
            current_role = role_match.group(1)
            continue
        model_match = re.match(r"^      model:\s*(.+?)\s*$", line)
        if current_role and model_match:
            models[current_role] = model_match.group(1).strip().strip('"')
    return models


def role_row(coarse: str, role: str, value: str, color: str) -> list[str]:
    brief = FINE_BRIEFS_BY_COARSE.get((coarse, role), FINE_BRIEFS.get(role, "TODO: add role brief."))
    return [
        f'####  <span style="color: {color};">{role}: [{value}]</span>',
        f" >    *Brief: {brief}*",
    ]


def render(repo: Path) -> str:
    registry_path = repo / "brain_model_registry.yaml"
    registry_text = registry_path.read_text()
    registry = yaml.safe_load(registry_text) or {}
    capabilities = registry.get("fine_grained_capabilities") or {}
    if not capabilities:
        raise RuntimeError(f"fine_grained_capabilities not found in {registry_path}")
    eligible = extract_decision_section(registry_text, "use")
    close = extract_decision_section(registry_text, "likely_after_more_samples")

    lines = ["# Model Eval Role Hierarchy", ""]
    for coarse, cfg in capabilities.items():
        lines.extend(["", f"## `{coarse}`", f"*{COARSE_BRIEFS.get(coarse, 'TODO: add coarse role brief.')}*", ""])

        for role in cfg.get("required_model_roles", []):
            if role in eligible:
                lines.extend(role_row(coarse, role, eligible[role], "green"))
            elif role in close:
                lines.extend(role_row(coarse, role, close[role], "orange"))
            else:
                lines.extend(role_row(coarse, role, "", "red"))
            lines.append("")

        for role in cfg.get("deterministic_roles", []):
            lines.extend(role_row(coarse, role, "deterministic", "green"))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Brain repo root.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/model_eval_phase_role_hierarchy.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(repo))
    print(output)


if __name__ == "__main__":
    main()
