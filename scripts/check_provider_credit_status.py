#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.config import Settings, load_settings, normalize_provider_name


console = Console()


@dataclass(frozen=True)
class ProviderBillingCapability:
    provider: str
    configured: bool
    credential_hint: str
    can_query_credit_balance_programmatically: str
    can_query_usage_or_cost_programmatically: str
    scope: str
    requires_extra_admin_or_cloud_auth: bool
    console_url: str
    notes: str


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.env_file)
    capabilities = provider_billing_capabilities(settings)

    if args.json:
        console.print_json(data=[asdict(item) for item in capabilities])
    else:
        print_capabilities(capabilities)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report whether each configured model provider supports programmatic "
            "credit/usage inspection with the currently available auth shape."
        )
    )
    parser.add_argument("--env-file", default=None, help="Optional env file to load.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    return parser


def provider_billing_capabilities(settings: Settings) -> list[ProviderBillingCapability]:
    providers = active_providers(settings)
    return [provider_billing_capability(provider, settings) for provider in providers]


def active_providers(settings: Settings) -> list[str]:
    active = {
        canonical_provider(settings.llm_provider),
        canonical_provider(settings.embedding_provider),
    }
    for provider in ("openai", "google", "anthropic", "aws-bedrock", "groq", "voyage"):
        if credential_present(settings, provider):
            active.add(provider)
    active.discard("")
    return sorted(active)


def provider_billing_capability(
    provider: str,
    settings: Settings,
) -> ProviderBillingCapability:
    configured = credential_present(settings, provider)
    credential_hint = configured_credential_hint(settings, provider)

    if provider == "openai":
        return ProviderBillingCapability(
            provider=provider,
            configured=configured,
            credential_hint=credential_hint,
            can_query_credit_balance_programmatically="partial",
            can_query_usage_or_cost_programmatically="yes",
            scope="organization/project",
            requires_extra_admin_or_cloud_auth=False,
            console_url="https://platform.openai.com/settings/organization/billing/credit-grants",
            notes=(
                "Usage and cost are available programmatically, but prepaid credit "
                "balance is primarily exposed in billing pages; treat balance lookup "
                "as org-level, not API-key-level."
            ),
        )

    if provider == "google":
        return ProviderBillingCapability(
            provider=provider,
            configured=configured,
            credential_hint=credential_hint,
            can_query_credit_balance_programmatically="partial",
            can_query_usage_or_cost_programmatically="partial",
            scope="Google Cloud project / billing account",
            requires_extra_admin_or_cloud_auth=True,
            console_url="https://console.cloud.google.com/billing",
            notes=(
                "Gemini API keys alone do not expose remaining paid balance. Usage, "
                "quota, and credit state live in Google Cloud / AI Studio and usually "
                "require project billing access beyond the API key."
            ),
        )

    if provider == "anthropic":
        return ProviderBillingCapability(
            provider=provider,
            configured=configured,
            credential_hint=credential_hint,
            can_query_credit_balance_programmatically="no",
            can_query_usage_or_cost_programmatically="partial",
            scope="organization/workspace",
            requires_extra_admin_or_cloud_auth=True,
            console_url="https://console.anthropic.com/settings/billing",
            notes=(
                "Usage and cost reporting exist via the Admin API for organizations. "
                "There is no general API-key-level credit balance endpoint."
            ),
        )

    if provider == "groq":
        return ProviderBillingCapability(
            provider=provider,
            configured=configured,
            credential_hint=credential_hint,
            can_query_credit_balance_programmatically="no",
            can_query_usage_or_cost_programmatically="no",
            scope="organization",
            requires_extra_admin_or_cloud_auth=False,
            console_url="https://console.groq.com/settings/billing",
            notes=(
                "Spend limits and billing are documented in the console. Public "
                "programmatic billing/credit APIs are not exposed in the normal API surface."
            ),
        )

    if provider == "aws-bedrock":
        return ProviderBillingCapability(
            provider=provider,
            configured=configured,
            credential_hint=credential_hint,
            can_query_credit_balance_programmatically="partial",
            can_query_usage_or_cost_programmatically="yes",
            scope="AWS account / billing account",
            requires_extra_admin_or_cloud_auth=True,
            console_url="https://console.aws.amazon.com/costmanagement/home",
            notes=(
                "Cost Explorer and billing tooling can be queried with appropriate AWS "
                "permissions, but remaining promotional credits are account-level billing "
                "data, not model-key-level data."
            ),
        )

    if provider == "voyage":
        return ProviderBillingCapability(
            provider=provider,
            configured=configured,
            credential_hint=credential_hint,
            can_query_credit_balance_programmatically="no",
            can_query_usage_or_cost_programmatically="no",
            scope="organization/account",
            requires_extra_admin_or_cloud_auth=False,
            console_url="https://dash.voyageai.com/",
            notes=(
                "Voyage documents billing and prepaid credits in the dashboard. A public "
                "usage/credit API is not documented."
            ),
        )

    return ProviderBillingCapability(
        provider=provider,
        configured=configured,
        credential_hint=credential_hint,
        can_query_credit_balance_programmatically="unknown",
        can_query_usage_or_cost_programmatically="unknown",
        scope="unknown",
        requires_extra_admin_or_cloud_auth=False,
        console_url="",
        notes="Provider not recognized by the billing capability checker.",
    )


def configured_credential_hint(settings: Settings, provider: str) -> str:
    if provider == "openai":
        return "OPENAI_API_KEY" if settings.openai_api_key else "missing"
    if provider == "google":
        if settings.google_api_key:
            return "GOOGLE_API_KEY"
        if settings.gemini_api_key:
            return "GEMINI_API_KEY"
        return "missing"
    if provider == "anthropic":
        return "ANTHROPIC_API_KEY" if settings.anthropic_api_key else "missing"
    if provider == "groq":
        return "GROQ_API_KEY" if settings.groq_api_key else "missing"
    if provider == "voyage":
        return "VOYAGE_API_KEY" if settings.voyage_api_key else "missing"
    if provider == "aws-bedrock":
        if settings.aws_bearer_token_bedrock:
            return "AWS_BEARER_TOKEN_BEDROCK"
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            return "AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY"
        return "missing"
    return "unknown"


def credential_present(settings: Settings, provider: str) -> bool:
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "google":
        return bool(settings.google_api_key or settings.gemini_api_key)
    if provider == "anthropic":
        return bool(settings.anthropic_api_key)
    if provider == "groq":
        return bool(settings.groq_api_key)
    if provider == "voyage":
        return bool(settings.voyage_api_key)
    if provider == "aws-bedrock":
        return bool(
            settings.aws_bearer_token_bedrock
            or (settings.aws_access_key_id and settings.aws_secret_access_key)
        )
    return False


def canonical_provider(provider: str | None) -> str:
    normalized = normalize_provider_name(provider)
    if normalized == "gemini":
        return "google"
    if normalized == "bedrock":
        return "aws-bedrock"
    return normalized or ""


def print_capabilities(capabilities: list[ProviderBillingCapability]) -> None:
    table = Table(title="Provider Credit / Usage Checkability")
    table.add_column("Provider")
    table.add_column("Configured")
    table.add_column("Credential")
    table.add_column("Credit Left API?")
    table.add_column("Usage/Cost API?")
    table.add_column("Scope")
    table.add_column("Extra Admin/Auth?")
    table.add_column("Console")

    for item in capabilities:
        table.add_row(
            item.provider,
            yes_no(item.configured),
            item.credential_hint,
            item.can_query_credit_balance_programmatically,
            item.can_query_usage_or_cost_programmatically,
            item.scope,
            yes_no(item.requires_extra_admin_or_cloud_auth),
            item.console_url,
        )
    console.print(table)
    console.print()
    for item in capabilities:
        console.print(f"[bold]{item.provider}[/bold]: {item.notes}")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    raise SystemExit(main())
