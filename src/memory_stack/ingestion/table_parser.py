from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from pydantic import BaseModel, Field


class TableParseResult(BaseModel):
    kind: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, str]] = Field(default_factory=list)
    row_count: int = 0
    sample_rows: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def parse_table(text: str, *, sample_size: int = 3) -> TableParseResult:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if looks_like_markdown_table(lines):
        result = parse_markdown_table(lines)
    else:
        result = parse_csv_table(text)
    return result.model_copy(update={"sample_rows": result.rows[:sample_size]})


def looks_like_markdown_table(lines: list[str]) -> bool:
    return len(lines) >= 2 and "|" in lines[0] and "|" in lines[1]


def parse_markdown_table(lines: list[str]) -> TableParseResult:
    headers = split_markdown_row(lines[0])
    body_lines = [
        line
        for index, line in enumerate(lines[1:], start=1)
        if index != 1 or not is_markdown_separator(line)
    ]
    rows = [row_from_values(headers, split_markdown_row(line)) for line in body_lines]
    return TableParseResult(
        kind="markdown",
        columns=headers,
        rows=rows,
        row_count=len(rows),
        metadata={"parser": "markdown_table"},
    )


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def is_markdown_separator(line: str) -> bool:
    cells = split_markdown_row(line)
    return bool(cells) and all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells)


def parse_csv_table(text: str) -> TableParseResult:
    reader = csv.DictReader(StringIO(text))
    rows = [{str(key): value or "" for key, value in row.items() if key is not None} for row in reader]
    columns = list(reader.fieldnames or [])
    return TableParseResult(
        kind="csv",
        columns=columns,
        rows=rows,
        row_count=len(rows),
        metadata={"parser": "csv"},
    )


def row_from_values(headers: list[str], values: list[str]) -> dict[str, str]:
    row: dict[str, str] = {}
    for index, header in enumerate(headers):
        row[header] = values[index] if index < len(values) else ""
    return row


def table_summary(result: TableParseResult) -> str:
    if not result.columns:
        return "Stored a table-like source."
    columns = ", ".join(result.columns)
    return f"Stored a {result.kind} table with {result.row_count} rows and columns: {columns}."
