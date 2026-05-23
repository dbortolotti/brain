from __future__ import annotations


def infer_recall_mode(query: str) -> str:
    lower = query.casefold()
    if lower.startswith(("debug ", "debug:", "why did you recall ")):
        return "debug"
    if "evidence" in lower or "show your work" in lower:
        return "evidence"
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
