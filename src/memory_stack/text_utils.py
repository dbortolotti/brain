from __future__ import annotations

import re
from typing import Any


NUMBER_WORDS = {
    "no": 0,
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def slug(value: str) -> str:
    return "_".join(re.findall(r"[a-z0-9]+", value.casefold()))


def number_word_to_int(value: str) -> int:
    lowered = value.casefold()
    if lowered in NUMBER_WORDS:
        return NUMBER_WORDS[lowered]
    return int(value)
