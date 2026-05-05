from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


SPEAKER_RE = re.compile(r"^\s*(?P<speaker>[A-Za-z][A-Za-z0-9 ._'/-]{0,40}):\s*(?P<text>.+?)\s*$")


class TranscriptParseResult(BaseModel):
    participants: list[str] = Field(default_factory=list)
    turns: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def parse_transcript(text: str) -> TranscriptParseResult:
    participants: list[str] = []
    turns: list[dict[str, str]] = []
    for line in text.splitlines():
        match = SPEAKER_RE.match(line)
        if match is None:
            continue
        speaker = match.group("speaker").strip()
        utterance = match.group("text").strip()
        if speaker not in participants:
            participants.append(speaker)
        turns.append({"speaker": speaker, "text": utterance})

    return TranscriptParseResult(
        participants=participants,
        turns=turns,
        metadata={
            "participant_count": len(participants),
            "turn_count": len(turns),
            "parser": "speaker_line",
        },
    )


def transcript_summary(parse_result: TranscriptParseResult, text: str) -> str:
    if parse_result.participants:
        return (
            "Transcript with "
            f"{len(parse_result.participants)} participants: "
            f"{', '.join(parse_result.participants)}."
        )
    return text[:500]
