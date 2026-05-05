from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from typing import Any

from memory_stack.cognee_adapter import list_datasources, normalize_optional_string_list
from memory_stack.config import Settings, repo_path


class NameResolutionError(ValueError):
    """Raised when a dataset or node-set name needs explicit user choice."""


@dataclass(frozen=True)
class NameChoice:
    value: str
    reason: str


SEPARATOR_RE = re.compile(r"[\s_]+")
MULTI_DASH_RE = re.compile(r"-+")


def canonical_name(value: str) -> str:
    normalized = SEPARATOR_RE.sub("-", value.strip().casefold())
    return MULTI_DASH_RE.sub("-", normalized).strip("-")


def compact_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().casefold())


def node_set_registry_path(settings: Settings) -> Path:
    return repo_path(settings.system_root_directory) / "brain-node-sets.json"


def load_node_set_registry(settings: Settings) -> list[str]:
    path = node_set_registry_path(settings)
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid node-set registry JSON: {path}") from exc

    values = payload.get("node_sets", []) if isinstance(payload, dict) else payload
    return sorted({str(value).strip() for value in values if str(value).strip()})


def save_node_set_registry(settings: Settings, node_sets: list[str]) -> None:
    path = node_set_registry_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"node_sets": sorted(set(node_sets))}, indent=2),
        encoding="utf-8",
    )


def register_node_sets(settings: Settings, node_sets: list[str] | None) -> None:
    normalized = normalize_optional_string_list(node_sets, field_name="node_set")
    if normalized is None:
        return

    existing = load_node_set_registry(settings)
    merged = sorted({*existing, *normalized})
    if merged != existing:
        save_node_set_registry(settings, merged)


async def resolve_dataset_name(
    value: str,
    *,
    settings: Settings,
) -> str:
    requested = value.strip()
    if not requested:
        raise NameResolutionError("Dataset name must not be empty.")

    datasources = await list_datasources(settings=settings)
    known = sorted(
        {
            str(datasource.get("name")).strip()
            for datasource in datasources
            if datasource.get("name")
        }
    )
    if requested in known:
        return requested

    choices = close_name_choices(requested, known)
    if choices:
        raise NameResolutionError(
            choice_message("dataset", requested, choices, create_tool="create_dataset")
        )

    if known:
        raise NameResolutionError(
            f"I couldn't find dataset '{requested}'. "
            f"Known datasets are: {', '.join(known)}. "
            f"If you intended a new dataset, create '{requested}' first using create_dataset."
        )

    raise NameResolutionError(
        f"I couldn't find dataset '{requested}'. "
        f"If you intended a new dataset, create '{requested}' first using create_dataset."
    )


def resolve_node_set_names(
    values: Any,
    *,
    settings: Settings,
    for_write: bool,
) -> list[str] | None:
    requested = normalize_optional_string_list(values, field_name="node_set")
    if requested is None:
        return None

    known = load_node_set_registry(settings)
    resolved: list[str] = []
    for value in requested:
        if value in known:
            resolved.append(value)
            continue

        choices = close_name_choices(value, known)
        if choices:
            raise NameResolutionError(
                choice_message("node set", value, choices, create_tool="create_node_set")
            )

        if known:
            raise NameResolutionError(
                f"I couldn't find node set '{value}'. Known node sets are: {', '.join(known)}. "
                f"If you intended a new node set, create '{value}' first using create_node_set."
            )

        action = "write with" if for_write else "search"
        raise NameResolutionError(
            f"I couldn't find node set '{value}' to {action}. "
            f"If you intended a new node set, create '{value}' first using create_node_set."
        )

    return resolved


def close_name_choices(requested: str, known: list[str]) -> list[NameChoice]:
    requested_canonical = canonical_name(requested)
    requested_compact = compact_name(requested)

    exact_normalized = [
        NameChoice(value=name, reason="normalizes to the same name")
        for name in known
        if canonical_name(name) == requested_canonical or compact_name(name) == requested_compact
    ]
    if exact_normalized:
        return exact_normalized

    by_canonical = {canonical_name(name): name for name in known}
    close_keys = get_close_matches(requested_canonical, list(by_canonical), n=3, cutoff=0.82)
    choices = [NameChoice(value=by_canonical[key], reason="close match") for key in close_keys]

    if choices:
        return choices

    scored = [
        (SequenceMatcher(a=requested_canonical, b=canonical_name(name)).ratio(), name)
        for name in known
    ]
    return [
        NameChoice(value=name, reason="close match")
        for score, name in sorted(scored, reverse=True)[:3]
        if score >= 0.78
    ]


def choice_message(
    kind: str,
    requested: str,
    choices: list[NameChoice],
    *,
    create_tool: str,
) -> str:
    primary = choices[0].value
    lines = [f"I couldn't find {kind} '{requested}', but found '{primary}'."]
    lines.append("Did you mean:")
    for idx, choice in enumerate(choices, start=1):
        letter = chr(ord("a") + idx - 1)
        lines.append(f"{letter}) {choice.value}")
    lines.append(
        f"Please choose one and retry with the exact name. "
        f"If you intended '{requested}' as new, create it first using {create_tool}."
    )
    return " ".join(lines)
