from __future__ import annotations

import time

from rich.console import Console
from rich.table import Table
import typer

from memory_stack.cfg import Settings, load_settings
from memory_stack.evals.cli import app as eval_app
from memory_stack.provider_auth import (
    OPENAI_CODEX_PROVIDER,
    ProviderAuthError,
    get_openai_codex_profile,
    get_token_sink_client_token,
    list_openai_codex_profiles,
    login_openai_codex,
    openai_uses_token_sink,
    refresh_openai_codex_profile,
)


app = typer.Typer(no_args_is_help=True)
app.add_typer(eval_app, name="eval")
models_app = typer.Typer(no_args_is_help=True)
auth_app = typer.Typer(no_args_is_help=True)
models_app.add_typer(auth_app, name="auth")
app.add_typer(models_app, name="models")
console = Console()


def require_supported_provider(provider: str) -> None:
    if provider != OPENAI_CODEX_PROVIDER:
        raise typer.BadParameter("Only openai-codex is supported for OAuth auth profiles.")


@auth_app.command("login")
def auth_login(
    provider: str = typer.Option(..., "--provider"),
    env_file: str | None = typer.Option(None, "--env-file"),
    manual: bool = typer.Option(False, "--manual", help="Skip localhost callback and paste code."),
    timeout_seconds: int = typer.Option(120, "--timeout-seconds"),
) -> None:
    require_supported_provider(provider)
    settings = load_settings(env_file)
    try:
        credential = login_openai_codex(
            settings,
            manual=manual,
            timeout_seconds=timeout_seconds,
        )
    except ProviderAuthError as exc:
        console.print(str(exc), style="red")
        raise typer.Exit(1) from exc
    console.print(
        f"Stored OpenAI Codex OAuth profile '{settings.openai_codex_auth_profile}' "
        f"(expires {format_expires(credential.expires)})."
    )


@auth_app.command("list")
def auth_list(
    provider: str = typer.Option(..., "--provider"),
    env_file: str | None = typer.Option(None, "--env-file"),
) -> None:
    require_supported_provider(provider)
    settings = load_settings(env_file)
    rows = list_openai_codex_profiles(settings)
    table = Table(title="OpenAI Codex OAuth Profiles")
    table.add_column("Provider")
    table.add_column("Profile")
    table.add_column("Status")
    table.add_column("Expires")
    table.add_column("Account")
    for row in rows:
        table.add_row(
            OPENAI_CODEX_PROVIDER,
            str(row["profile"]),
            str(row["status"]),
            format_expires(row.get("expires")),
            str(row.get("email") or row.get("account_id") or ""),
        )
    console.print(table)


@auth_app.command("status")
def auth_status(
    provider: str = typer.Option(..., "--provider"),
    env_file: str | None = typer.Option(None, "--env-file"),
) -> None:
    require_supported_provider(provider)
    settings = load_settings(env_file)
    credential = get_openai_codex_profile(settings)
    if settings.openai_auth_mode == "api_key":
        key_status = "configured" if settings.configured_provider_api_key("openai") else "missing"
        console.print(f"openai text: API key mode ({key_status})")
    elif openai_uses_token_sink(settings):
        console.print(f"openai text: {token_sink_status(settings)}")
    elif credential and credential.usable():
        console.print(f"openai text: OAuth profile {settings.openai_codex_auth_profile}")
    elif credential:
        console.print(f"openai text: OAuth profile {settings.openai_codex_auth_profile} expired")
    else:
        console.print(f"openai text: OAuth profile {settings.openai_codex_auth_profile} missing")

    if settings.openai_auth_mode == "api_key":
        embedding_status = (
            "OPENAI_API_KEY configured"
            if settings.configured_provider_api_key("openai")
            else "missing OPENAI_API_KEY"
        )
    elif settings.embedding_provider == "openai":
        embedding_status = (
            token_sink_status(settings)
            if openai_uses_token_sink(settings)
            else f"OAuth profile {settings.openai_codex_auth_profile}"
        )
    else:
        embedding_status = "not using OpenAI embeddings"
    console.print(f"openai embedding: {embedding_status}")


@auth_app.command("refresh")
def auth_refresh(
    provider: str = typer.Option(..., "--provider"),
    env_file: str | None = typer.Option(None, "--env-file"),
) -> None:
    require_supported_provider(provider)
    settings = load_settings(env_file)
    try:
        credential = refresh_openai_codex_profile(settings)
    except ProviderAuthError as exc:
        console.print(str(exc), style="red")
        raise typer.Exit(1) from exc
    console.print(
        f"Refreshed OpenAI Codex OAuth profile '{settings.openai_codex_auth_profile}' "
        f"(expires {format_expires(credential.expires)})."
    )


def format_expires(expires: object) -> str:
    if not isinstance(expires, int | float) or expires <= 0:
        return ""
    return time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(expires / 1000))


def token_sink_status(settings: Settings) -> str:
    try:
        get_token_sink_client_token(settings)
    except ProviderAuthError as exc:
        return f"token sink client unavailable ({exc})"
    return "token sink client configured"


if __name__ == "__main__":
    app()
