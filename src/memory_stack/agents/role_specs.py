from __future__ import annotations

from pathlib import Path


ROLE_SPEC_DIR = Path(__file__).resolve().parent / "roles"

REQUIRED_ROLE_SPEC_SECTIONS = (
    "Purpose",
    "Scope",
    "Inputs",
    "Output Contract",
    "Decision Procedure",
    "Must Do",
    "Must Not Do",
    "Safety / Failure Modes",
    "Verification Notes",
)


def role_spec_path(role: str) -> Path:
    return ROLE_SPEC_DIR / f"{role}.md"


def role_spec_role_names() -> set[str]:
    if not ROLE_SPEC_DIR.exists():
        return set()
    return {path.stem for path in ROLE_SPEC_DIR.glob("*.md")}


def role_spec_markdown(role: str) -> str | None:
    path = role_spec_path(role)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def role_spec_lines(role: str) -> list[str]:
    text = role_spec_markdown(role)
    if text is None:
        return []
    return [
        f"Role markdown from src/memory_stack/agents/roles/{role}.md:",
        *compact_markdown_lines(text.splitlines()),
    ]


def markdown_heading_positions(lines: list[str]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("## "):
            continue
        positions[stripped[3:].strip()] = index
    return positions


def markdown_section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    section: list[str] = []
    in_section = False
    heading_level = 0
    target = heading.strip()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            if in_section and level <= heading_level:
                break
            if title == target:
                in_section = True
                heading_level = level
                continue
        elif in_section:
            section.append(line)
    return compact_markdown_lines(section)


def compact_markdown_lines(lines: list[str]) -> list[str]:
    compacted: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not stripped or stripped == "---":
            continue
        compacted.append(stripped)
    return compacted
