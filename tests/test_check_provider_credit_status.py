from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

from memory_stack.config import Settings


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_provider_credit_status.py"
SPEC = importlib.util.spec_from_file_location("check_provider_credit_status", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_provider_billing_capabilities_include_configured_providers() -> None:
    settings = Settings(
        profile="openai",
        openai_api_key="sk-openai",
        gemini_api_key="AIza-gemini",
        anthropic_api_key="sk-ant",
        voyage_api_key="pa-voyage",
        llm_provider="openai",
    )

    capabilities = MODULE.provider_billing_capabilities(settings)
    providers = {item.provider for item in capabilities}

    assert {"openai", "google", "anthropic", "voyage"} <= providers


def test_google_credential_hint_prefers_google_api_key() -> None:
    settings = Settings(google_api_key="AIza-google", gemini_api_key="AIza-gemini")

    item = MODULE.provider_billing_capability("google", settings)

    assert item.credential_hint == "GOOGLE_API_KEY"
    assert item.can_query_credit_balance_programmatically == "partial"
    assert item.requires_extra_admin_or_cloud_auth is True


def test_groq_is_console_only_for_billing() -> None:
    settings = Settings(groq_api_key="gsk-groq")

    item = MODULE.provider_billing_capability("groq", settings)

    assert item.configured is True
    assert item.can_query_credit_balance_programmatically == "no"
    assert item.can_query_usage_or_cost_programmatically == "no"
