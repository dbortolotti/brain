from __future__ import annotations

from pathlib import Path

from memory_stack.agents.role_specs import markdown_section_lines, role_spec_lines


MEMORY_COMPILER_RUNTIME_ROLES = (
    "source_classifier",
    "source_takeaway_extractor",
    "atomic_card_extractor",
    "memory_kind_classifier",
    "entity_mention_extractor",
    "relationship_extractor",
    "durability_filter",
    "table_policy_handler",
)


def prompt_contract_lines(role: str) -> list[str]:
    lines = agent_markdown_contract_lines(role)
    lines.extend(role_spec_lines(role))
    return list(dict.fromkeys(lines))


def multi_role_prompt_contract_lines(roles: tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for role in roles:
        lines.append(f"Runtime role: {role}")
        lines.extend(prompt_contract_lines(role))
    return list(dict.fromkeys(lines))


def prompt_contract_block(roles: tuple[str, ...]) -> str:
    lines = multi_role_prompt_contract_lines(roles)
    if not lines:
        return ""
    return "\n".join(["Role contracts:", *(f"- {line}" for line in lines)])


def agent_markdown_contract_lines(role: str) -> list[str]:
    lines = agent_markdown_excerpt_lines(
        [
            ("src/memory_stack/agents/shared/memory_agent_rules.md", "Mission"),
            ("src/memory_stack/agents/shared/memory_agent_rules.md", "Non-Goals"),
            ("src/memory_stack/agents/shared/agent_architecture.md", "1.2 Memory intake agent has an extra LLM layer"),
        ],
        max_lines_per_section=10,
    )
    if role == "intent_router":
        lines += agent_markdown_excerpt_lines(
            [
                ("src/memory_stack/agents/shared/agent_architecture.md", "6. Memory intake commands"),
                ("src/memory_stack/agents/shared/agent_architecture.md", "7. Memory intake message routing"),
            ],
            max_lines_per_section=21,
        )
    elif role == "source_classifier":
        lines += agent_markdown_excerpt_lines(
            [("src/memory_stack/agents/shared/agent_architecture.md", "6.2 `/brain source`")],
            max_lines_per_section=14,
        )
    elif role == "durability_filter":
        lines += agent_markdown_excerpt_lines(
            [
                ("src/memory_stack/agents/shared/memory_agent_rules.md", "Refusal Criteria"),
                ("src/memory_stack/agents/shared/memory_agent_rules.md", "Clarification Criteria"),
            ],
            max_lines_per_section=12,
        )
    elif role == "memory_kind_classifier":
        lines += agent_markdown_excerpt_lines(
            [
                ("src/memory_stack/agents/shared/memory_agent_rules.md", "Allowed Memory Kinds"),
                ("src/memory_stack/agents/shared/memory_agent_rules.md", "Required Proposal Fields"),
            ],
            max_lines_per_section=16,
        )
    elif role == "open_loop_detector":
        lines += agent_markdown_excerpt_lines(
            [("src/memory_stack/agents/shared/memory_agent_rules.md", "Clarification Criteria")],
            max_lines_per_section=12,
        )
    elif role == "repair_option_generator":
        lines += agent_markdown_excerpt_lines(
            [
                ("src/memory_stack/agents/shared/agent_architecture.md", "2. Core behaviour"),
                ("src/memory_stack/agents/shared/memory_agent_rules.md", "Conflict Behavior"),
            ],
            max_lines_per_section=25,
        )
    return lines


def agent_markdown_excerpt_lines(
    sections: list[tuple[str, str]],
    *,
    max_lines_per_section: int,
) -> list[str]:
    lines: list[str] = []
    for relative_path, heading in sections:
        content = markdown_section(relative_path, heading)
        if not content:
            continue
        lines.append(f"Agent markdown excerpt from {relative_path}#{heading}:")
        lines.extend(f"  {line}" for line in content[:max_lines_per_section])
    return lines


def markdown_section(relative_path: str, heading: str) -> list[str]:
    path = Path(__file__).resolve().parents[3] / relative_path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return markdown_section_lines(text, heading)
