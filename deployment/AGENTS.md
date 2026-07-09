# Purpose

- Own checked-in deployment templates and service definitions for Brain runtime environments.

## Ownership

- `caddy/` owns public reverse-proxy templates.
- `cloudflare/` owns example Cloudflare Tunnel configuration.
- `docker-compose.prod.yml` owns production compose service wiring.
- `launchd/` owns macOS service templates.
- `systemd/` owns Linux service and timer templates.
- `mcp/` owns MCP client configuration templates.
- `newsyslog/` owns log rotation config.
- `postgres/initdb/` owns database initialization SQL.

## Local Contracts

- Templates must not contain rendered secrets or host-private credentials.
- Service names, ports, paths, and labels must stay aligned with `cfg/`, `scripts/deploy-*.sh`, `scripts/run_launchd_service.sh`, and production docs.
- Postgres init changes must stay compatible with migrations and backup or restore expectations.

## Work Guidance

- Keep templates declarative and parameterized where deployment scripts inject environment-specific values.
- When changing a service boundary, update the relevant deploy script, docs, and verification script in the same change.

## Verification

- Run `uv run pytest tests/test_deployment_requirements.py` after deployment template changes.
- For production-facing changes, run or update `make prod-check` and `make ui-prod-check` where relevant.

## Child DOX Index

- No child AGENTS.md files. All deployment subdirectories are owned here.
