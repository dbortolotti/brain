.PHONY: setup up down check smoke model-smoke-all ingest-sample recall-sample eval brain-eval tokens reset reset-hard mcp-config mcp-http slack-agent ui-proxy deploy-local-production prod-check slack-agent-check ui-prod-check backup cloudflare-verify model-eval-role-hierarchy pre-commit test lint

MODEL_SMOKE_OUTPUT ?= eval_runs/live_model_smoke_all.json
MODEL_SMOKE_ARGS ?=

setup:
	uv sync --all-extras

up:
	docker compose up -d

down:
	docker compose down

check:
	uv run python scripts/check_env.py

smoke:
	uv run python scripts/smoke_cognee.py

model-smoke-all:
	uv run python scripts/live_model_smoke.py --all-registry --json-output $(MODEL_SMOKE_OUTPUT) $(MODEL_SMOKE_ARGS)

ingest-sample:
	uv run python -m memory_stack.ingest_cognee --input data/samples/synthetic_property_emails.jsonl --temporal

recall-sample:
	uv run python -m memory_stack.recall_cognee --dataset property_trial --search-type TEMPORAL --query "What is our current position on the Principal Designer question?"

eval:
	uv run python -m memory_stack.eval_runner --queries eval/queries.yaml --output eval/results/results.csv

brain-eval:
	uv run python -m memory_stack.evals.cli --output eval/results/brain-golden.json

tokens:
	uv run python scripts/estimate_tokens.py --input data/samples/synthetic_property_emails.jsonl

reset:
	uv run python scripts/reset_stores.py --soft

reset-hard:
	uv run python scripts/reset_stores.py --hard

mcp-config:
	uv run python scripts/export_mcp_config.py

mcp-http:
	uv run python -m memory_stack.mcp_server

slack-agent:
	uv run python -m memory_stack.slack_agent_server

ui-proxy:
	uv run python -m uvicorn memory_stack.ui_proxy:app --host 127.0.0.1 --port 8002

deploy-local-production:
	./scripts/deploy-local-production.sh

prod-check:
	uv run python scripts/verify_mcp_production.py

slack-agent-check:
	uv run python scripts/verify_slack_agent.py

ui-prod-check:
	uv run python scripts/verify_cognee_ui_production.py

backup:
	uv run python scripts/backup_stores.py

cloudflare-verify:
	uv run python scripts/verify_cloudflare_mcp.py

model-eval-role-hierarchy:
	uv run python skills/brain-model-eval-role-hierarchy/scripts/generate_model_eval_role_hierarchy.py --repo . --output artifacts/model_eval_phase_role_hierarchy.md

pre-commit: model-eval-role-hierarchy
	@git status --short artifacts/model_eval_phase_role_hierarchy.md skills/brain-model-eval-role-hierarchy

test:
	uv run pytest

lint:
	uv run ruff check .
