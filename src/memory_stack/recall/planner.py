from __future__ import annotations


def infer_recall_mode(query: str) -> str:
    lower = query.casefold()
    if lower.startswith(("debug ", "debug:", "why did you recall ")):
        return "debug"
    if "source" in lower and any(word in lower for word in ("show", "find", "saved", "evidence")):
        return "sources"
    if "evidence" in lower or "show your work" in lower:
        return "evidence"
    if "open question" in lower or "open idea" in lower or "open loops" in lower:
        return "open_loops"
    if lower.startswith(("tell me everything about ", "tell me about ", "what do i know about ")):
        return "profile"
    return "memories"


def extract_profile_name(query: str) -> str:
    lower = query.casefold()
    prefixes = [
        "tell me everything about ",
        "tell me about ",
        "what do i know about ",
    ]
    for prefix in prefixes:
        if lower.startswith(prefix):
            return query[len(prefix) :].strip(" ?.")
    return query.strip(" ?.")
