.PHONY: setup up down check model-smoke brain-eval targeted-fine-grained-eval reset reset-hard mcp-config mcp-http slack-agent ui-proxy deploy-local-production prod-check slack-agent-check ui-prod-check backup cloudflare-verify test lint

MODEL_SMOKE_OUTPUT ?= eval_runs/live_model_smoke_active.json
MODEL_SMOKE_ARGS ?=

setup:
	uv sync --all-extras

up:
	docker compose up -d

down:
	docker compose down

check:
	uv run python scripts/check_env.py

model-smoke:
	uv run python scripts/live_model_smoke.py --scope active --json-output $(MODEL_SMOKE_OUTPUT) $(MODEL_SMOKE_ARGS)

brain-eval:
	uv run python -m memory_stack.evals.cli --output eval_runs/brain-golden.json

targeted-fine-grained-eval:
	uv run python -m memory_stack.evals.cli models \
		--mode fine-grained \
		--fixture-set brain-model-test-v2 \
		--roles durability_filter,atomic_card_extractor,entity_candidate_ranker,recall_synthesizer,debug_explainer,eval_judge \
		--models openai:gpt-5.5 \
		--repeat-runs 3 \
		--endpoint-max-concurrency 10 \
		--retry-attempts 3 \
		--output-json eval_runs/targeted_fine_grained/results.json

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

test:
	uv run pytest

lint:
	uv run ruff check .
