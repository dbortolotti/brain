.PHONY: setup up down check smoke ingest-sample recall-sample eval brain-eval tokens reset reset-hard mcp-config mcp-http ui-proxy deploy-local-production prod-check ui-prod-check backup cloudflare-verify test lint

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

ui-proxy:
	uv run python -m uvicorn memory_stack.ui_proxy:app --host 127.0.0.1 --port 8002

deploy-local-production:
	./scripts/deploy-local-production.sh

prod-check:
	uv run python scripts/verify_mcp_production.py

ui-prod-check:
	uv run python scripts/verify_cognee_ui_production.py

backup:
	uv run python scripts/backup_stores.py

cloudflare-verify:
	uv run python scripts/verify_cloudflare_mcp.py

test:
	uv run pytest

lint:
	uv run ruff check .
