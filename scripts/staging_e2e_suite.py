#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from memory_stack.brain_store import normalize_user_id
from memory_stack.cfg import Settings, load_settings
from memory_stack.llm.client import ConfiguredLLMClient


DEFAULT_BASE_URL = "http://127.0.0.1:18100"
DEFAULT_ADMIN_PASSWORD_FILE = Path(
    "/Volumes/xpg_usb4/staging/brain/shared/secrets/brain-auth-root-password"
)
DEFAULT_TEST_PASSWORD_FILE = Path(
    "/Volumes/xpg_usb4/staging/brain/shared/secrets/brain-auth-e2e-password"
)
DEFAULT_JUDGE_ENV_FILE = Path("/Volumes/xpg_usb4/staging/brain/shared/secrets/brain.env")


@dataclass(frozen=True)
class E2ECase:
    case_id: str
    query: str
    observed: dict[str, Any]
    expected: tuple[str, ...]
    forbidden: tuple[str, ...] = ()
    min_score: float = 0.82


class StagingClient:
    def __init__(self, base_url: str, *, timeout_seconds: float = 240) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout_seconds, follow_redirects=True)
        self.session_cookie: str | None = None
        self.csrf_token: str | None = None
        self.rpc_counter = 0

    def close(self) -> None:
        self.client.close()

    def login(self, user_id: str, password: str) -> dict[str, Any]:
        response = self.client.post(
            f"{self.base_url}/login",
            json={"user_id": user_id, "password": password},
        )
        response.raise_for_status()
        payload = response.json()
        cookie = response.cookies.get("brain_web_session")
        if not cookie:
            raise RuntimeError("Login succeeded but did not return brain_web_session cookie.")
        self.session_cookie = cookie
        self.csrf_token = str(payload["csrf_token"])
        return payload

    def headers(self, *, csrf: bool = True) -> dict[str, str]:
        if not self.session_cookie:
            raise RuntimeError("Client is not logged in.")
        headers = {"Cookie": f"brain_web_session={self.session_cookie}"}
        if csrf:
            if not self.csrf_token:
                raise RuntimeError("Client is missing CSRF token.")
            headers["x-brain-csrf"] = self.csrf_token
        return headers

    def request_json(
        self,
        method: str,
        path: str,
        *,
        csrf: bool = True,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self.client.request(
            method,
            f"{self.base_url}{path}",
            headers=self.headers(csrf=csrf),
            json=json_payload,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Expected JSON from {method} {path}, got "
                f"{response.headers.get('content-type', 'unknown content type')}: "
                f"{response.text[:240]}"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError(f"Expected JSON object from {path}.")
        return payload

    def mcp_call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        self.rpc_counter += 1
        payload = {
            "jsonrpc": "2.0",
            "id": f"staging-e2e-{self.rpc_counter}",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        response = self.client.post(
            f"{self.base_url}/mcp",
            headers=self.headers(csrf=True),
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("error"):
            raise RuntimeError(f"{name} failed: {body['error'].get('message')}")
        result = body.get("result") or {}
        structured = result.get("structuredContent")
        if not isinstance(structured, dict):
            raise RuntimeError(f"{name} did not return structuredContent.")
        return structured


def ensure_password_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(32)
    path.write_text(password + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return password


def ensure_test_user(
    *,
    base_url: str,
    admin_user: str,
    admin_password: str,
    test_user: str,
    test_password: str,
    display_name: str,
) -> str:
    normalized_test_user = normalize_user_id(test_user)
    admin = StagingClient(base_url)
    try:
        admin.login(admin_user, admin_password)
        users_payload = admin.request_json("GET", "/admin/users", csrf=False)
        users = users_payload.get("users") or []
        exists = any(
            normalize_user_id(str(user.get("id") or "")) == normalized_test_user
            for user in users
            if isinstance(user, dict)
        )
        body = {
            "password": test_password,
            "display_name": display_name,
            "email": "",
            "superuser": False,
        }
        if exists:
            admin.request_json("PUT", f"/admin/users/{normalized_test_user}", json_payload=body)
            return "updated"
        admin.request_json(
            "POST",
            "/admin/users",
            json_payload={"id": normalized_test_user, **body},
        )
        return "created"
    finally:
        admin.close()


def remember(client: StagingClient, text: str, *, input_type: str = "fact") -> dict[str, Any]:
    payload = client.mcp_call(
        "brain_remember",
        {
            "input": text,
            "input_type": input_type,
            "confirmed_by_user": True,
            "dry_run": False,
            "context": {"confirmed_by_user": True, "e2e_suite": "staging"},
        },
    )
    if not payload.get("memory_cards"):
        raise RuntimeError(f"brain_remember created no memory cards for: {text[:80]}")
    return payload


def ingest_article(client: StagingClient, *, run_id: str) -> dict[str, Any]:
    article = f"""
Title: Brain staging retrieval notes for {run_id}

This article is part of the Brain staging E2E suite. It says the Starlake Analytics
prototype should keep local experiments in DuckDB, shared staging state in Postgres,
and Brain retrieval indexes in pgvector because colocating vector data with Postgres
simplifies backup checks. It also says graph projections are rebuildable from source
records, so raw article text should stay separate from derived memory cards.
"""
    payload = client.mcp_call(
        "brain_ingest_source",
        {
            "source": article.strip(),
            "source_kind": "article",
            "title": f"Brain staging retrieval notes {run_id}",
            "why_saved": "Staging E2E source-ingestion coverage.",
            "extract_memories": True,
            "dry_run": False,
            "confirmed_by_user": True,
            "metadata": {"run_id": run_id, "suite": "staging_e2e"},
        },
    )
    if not payload.get("source_id"):
        raise RuntimeError("brain_ingest_source did not create a source.")
    return payload


def remember_and_confirm_palate(client: StagingClient, text: str) -> dict[str, Any]:
    proposal = client.mcp_call(
        "brain_remember",
        {
            "input": text,
            "input_type": "auto",
            "confirmed_by_user": True,
            "dry_run": False,
            "context": {"confirmed_by_user": True, "e2e_suite": "staging_palate"},
        },
    )
    taste = proposal.get("taste") or {}
    proposal_id = ((taste.get("proposal") or {}).get("proposal_id")) or taste.get("proposal_id")
    if not proposal_id:
        raise RuntimeError(f"Palate remember did not return a proposal_id for: {text}")
    confirmed = client.mcp_call("brain_palate_confirm", {"proposal_id": proposal_id})
    if not confirmed.get("confirmed"):
        raise RuntimeError(f"Palate proposal was not confirmed: {proposal_id}")
    return {"proposal": proposal, "confirmed": confirmed}


def prime_database(client: StagingClient, *, run_id: str) -> dict[str, Any]:
    session = client.mcp_call("brain_session")
    memories = [
        remember(
            client,
            f"E2E RUN {run_id}: I prefer concise technical updates that mention blockers and verification status.",
            input_type="person_interaction",
        ),
        remember(
            client,
            f"E2E RUN {run_id}: The Starlake Analytics project uses DuckDB for local experiments and Postgres for shared staging.",
            input_type="fact",
        ),
        remember(
            client,
            f"E2E RUN {run_id}: Ask me to confirm before deleting production data.",
            input_type="fact",
        ),
        remember(
            client,
            f"E2E RUN {run_id}: Open question: decide whether the Starlake launch checklist should include a rollback drill.",
            input_type="open_question",
        ),
    ]
    article = ingest_article(client, run_id=run_id)
    palate = [
        remember_and_confirm_palate(client, "remember 2016 Cuvee Sasha in palate"),
        remember_and_confirm_palate(
            client,
            "remember Mayfair Food Fayre Caesar salad wrap in palate; saw on Instagram",
        ),
        remember_and_confirm_palate(
            client,
            "remember the album Kind of Blue in palate; I like spacious jazz trumpet sessions",
        ),
    ]
    return {"session": session, "memories": memories, "article": article, "palate": palate}


def build_usage_cases(client: StagingClient, *, run_id: str) -> list[E2ECase]:
    concise = client.mcp_call(
        "brain_recall",
        {
            "query": f"For E2E RUN {run_id}, how should technical updates be written?",
            "mode": "auto",
            "include_sources": True,
            "limit": 10,
        },
    )
    stack = client.mcp_call(
        "brain_recall",
        {
            "query": f"For E2E RUN {run_id}, what storage choices were recorded for Starlake Analytics?",
            "mode": "auto",
            "include_sources": True,
            "limit": 10,
        },
    )
    article = client.mcp_call(
        "brain_recall",
        {
            "query": f"For E2E RUN {run_id}, why was pgvector selected in the saved article?",
            "mode": "sources",
            "include_sources": True,
            "limit": 10,
        },
    )
    open_loop = client.mcp_call(
        "brain_recall",
        {
            "query": f"For E2E RUN {run_id}, what open question remains about the launch checklist?",
            "mode": "open_loops",
            "include_sources": True,
            "limit": 10,
        },
    )
    wine = client.mcp_call(
        "brain_palate_query",
        {
            "query": "What do we know about 2016 Cuvee Sasha?",
            "explain": True,
            "context": {"e2e_run_id": run_id},
        },
    )
    restaurant = client.mcp_call(
        "brain_palate_query",
        {
            "query": "What was the Instagram Caesar salad wrap place I wanted to try?",
            "explain": True,
            "context": {"e2e_run_id": run_id},
        },
    )
    return [
        E2ECase(
            case_id="memory.communication_style",
            query="Recall the user's technical-update preference.",
            observed=concise,
            expected=(
                "concise technical updates",
                "mention blockers",
                "mention verification status",
                run_id,
            ),
        ),
        E2ECase(
            case_id="memory.project_storage",
            query="Recall the Starlake Analytics storage stack.",
            observed=stack,
            expected=("Starlake Analytics", "DuckDB", "local experiments", "Postgres", "shared staging", run_id),
        ),
        E2ECase(
            case_id="source.article_retrieval",
            query="Recall facts derived from an ingested article.",
            observed=article,
            expected=("pgvector", "colocating vector data with Postgres", "backup", "graph projections are rebuildable"),
        ),
        E2ECase(
            case_id="memory.open_loop",
            query="Recall the launch-checklist open question.",
            observed=open_loop,
            expected=("open question", "Starlake launch checklist", "rollback drill", run_id),
        ),
        E2ECase(
            case_id="palate.wine",
            query="Retrieve and explain the saved wine record.",
            observed=wine,
            expected=("2016", "Cuvee Sasha", "wine"),
            forbidden=("restaurant", "bar"),
        ),
        E2ECase(
            case_id="palate.restaurant",
            query="Retrieve and explain the saved restaurant/food wishlist record.",
            observed=restaurant,
            expected=("Mayfair Food Fayre", "Caesar salad wrap", "Instagram"),
        ),
    ]


def build_judge(settings: Settings, *, model: str, reasoning_effort: str) -> ConfiguredLLMClient:
    _ = reasoning_effort
    judge_settings = settings.model_copy(
        update={
            "brain_llm_enabled": True,
            "llm_provider": "openai",
            "llm_model": model,
            "openai_auth_mode": "api_key",
        }
    )
    return ConfiguredLLMClient(judge_settings)


def score_case(
    case: E2ECase,
    *,
    judge: ConfiguredLLMClient,
    judge_model: str,
    judge_reasoning_effort: str,
) -> dict[str, Any]:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["score", "passed", "missing", "incorrect", "rationale"],
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "passed": {"type": "boolean"},
            "missing": {"type": "array", "items": {"type": "string"}},
            "incorrect": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
    }
    prompt = "\n".join(
        [
            "You are judging a Brain staging end-to-end test.",
            "Score whether the observed tool output contains the expected facts and avoids forbidden facts.",
            "Give score 1.0 only when all expected facts are present or clearly entailed.",
            "Do not reward generic answers that omit the run-specific evidence.",
            f"Case id: {case.case_id}",
            f"User-level query: {case.query}",
            "Expected facts:",
            json.dumps(case.expected, ensure_ascii=False),
            "Forbidden facts:",
            json.dumps(case.forbidden, ensure_ascii=False),
            "Observed tool output JSON:",
            json.dumps(case.observed, ensure_ascii=False, default=str)[:12000],
        ]
    )
    result = judge.complete_json(
        prompt,
        schema,
        model=judge_model,
        reasoning_effort=judge_reasoning_effort,
        schema_name="brain_staging_e2e_judgement",
    )
    score = float(result.get("score") or 0)
    return {
        "case_id": case.case_id,
        "status": "pass" if bool(result.get("passed")) and score >= case.min_score else "fail",
        "min_score": case.min_score,
        "judge": result,
        "observed": case.observed,
        "expected": list(case.expected),
        "forbidden": list(case.forbidden),
    }


def run_isolation_check(
    *,
    base_url: str,
    admin_user: str,
    admin_password: str,
    test_session_id: str,
    run_id: str,
) -> dict[str, Any]:
    admin = StagingClient(base_url)
    try:
        admin.login(admin_user, admin_password)
        admin_session = admin.mcp_call("brain_session")
        recall = admin.mcp_call(
            "brain_recall",
            {
                "query": f"For E2E RUN {run_id}, what storage choices were recorded for Starlake Analytics?",
                "mode": "auto",
                "include_sources": True,
                "limit": 10,
            },
        )
    finally:
        admin.close()
    serialized = json.dumps(recall, ensure_ascii=False, default=str)
    passed = (
        admin_session.get("session_id") != test_session_id
        and run_id not in serialized
        and "Starlake Analytics" not in serialized
    )
    return {
        "case_id": "auth.user_isolation",
        "status": "pass" if passed else "fail",
        "admin_session_id": admin_session.get("session_id"),
        "test_session_id": test_session_id,
        "admin_recall_answer": recall.get("answer"),
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live Brain E2E tests against staging.")
    parser.add_argument("--base-url", default=os.getenv("BRAIN_STAGING_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-user", default="default")
    parser.add_argument("--admin-password-file", type=Path, default=DEFAULT_ADMIN_PASSWORD_FILE)
    parser.add_argument("--test-user", default="brain_e2e")
    parser.add_argument("--test-display-name", default="Brain E2E Test User")
    parser.add_argument("--test-password-file", type=Path, default=DEFAULT_TEST_PASSWORD_FILE)
    parser.add_argument("--judge-env-file", type=Path, default=Path(os.getenv("ENV_FILE", DEFAULT_JUDGE_ENV_FILE)))
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument("--judge-reasoning-effort", default="high")
    parser.add_argument("--run-id", default=datetime.now(UTC).strftime("e2e_%Y%m%d_%H%M%S"))
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Defaults to .reports/staging-e2e/<run-id>.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.test_user = normalize_user_id(args.test_user)
    started = time.perf_counter()
    report_path = args.report_path or Path(".reports") / "staging-e2e" / f"{args.run_id}.json"
    admin_password = args.admin_password_file.read_text(encoding="utf-8").strip()
    test_password = ensure_password_file(args.test_password_file)
    user_status = ensure_test_user(
        base_url=args.base_url,
        admin_user=args.admin_user,
        admin_password=admin_password,
        test_user=args.test_user,
        test_password=test_password,
        display_name=args.test_display_name,
    )

    client = StagingClient(args.base_url)
    try:
        client.login(args.test_user, test_password)
        seed = prime_database(client, run_id=args.run_id)
        cases = build_usage_cases(client, run_id=args.run_id)
    finally:
        client.close()

    settings = load_settings(args.judge_env_file, config_env="staging")
    judge = build_judge(
        settings,
        model=args.judge_model,
        reasoning_effort=args.judge_reasoning_effort,
    )
    scored = [
        score_case(
            case,
            judge=judge,
            judge_model=args.judge_model,
            judge_reasoning_effort=args.judge_reasoning_effort,
        )
        for case in cases
    ]
    isolation = run_isolation_check(
        base_url=args.base_url,
        admin_user=args.admin_user,
        admin_password=admin_password,
        test_session_id=str(seed["session"]["session_id"]),
        run_id=args.run_id,
    )
    all_records = [*scored, isolation]
    fail_count = sum(1 for record in all_records if record["status"] != "pass")
    report = {
        "suite": "brain_staging_e2e",
        "base_url": args.base_url,
        "run_id": args.run_id,
        "test_user": args.test_user,
        "test_user_status": user_status,
        "judge_model": args.judge_model,
        "judge_reasoning_effort": args.judge_reasoning_effort,
        "pass_count": len(all_records) - fail_count,
        "fail_count": fail_count,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "seed": seed,
        "records": all_records,
    }
    write_report(report_path, report)
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "test_user": args.test_user,
                "test_user_status": user_status,
                "pass_count": report["pass_count"],
                "fail_count": fail_count,
                "report_path": str(report_path),
            },
            indent=2,
        )
    )
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
