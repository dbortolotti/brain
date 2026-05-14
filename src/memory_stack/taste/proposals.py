from __future__ import annotations

from typing import Any


def proposal_response(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "proposal_id": proposal["id"],
        "status": proposal["status"],
        "expires_at": proposal.get("expires_at"),
        "proposal": proposal.get("proposal_json") or {},
        "warnings": proposal.get("warnings_json") or [],
    }
