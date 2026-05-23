.PHONY: setup up down check docs-generate docs-check docs-hash docs-llm llm-docs model-smoke brain-eval targeted-fine-grained-eval palate-probe reset reset-hard mcp-config mcp-http ui-proxy deploy-local-production prod-check ui-prod-check backup maintenance cloudflare-verify test lint

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

docs-generate:
	uv run python scripts/docs_check.py --update-facts

docs-check:
	uv run python scripts/docs_check.py

docs-hash:
	uv run python scripts/docs_llm_generate.py --hash-only

docs-llm:
	uv run python scripts/docs_llm_generate.py

llm-docs: docs-llm

model-smoke:
	uv run python scripts/live_model_smoke.py --scope active --json-output $(MODEL_SMOKE_OUTPUT) $(MODEL_SMOKE_ARGS)

brain-eval:
	uv run python -m memory_stack.evals.cli --output eval_runs/brain-golden.json

targeted-fine-grained-eval:
	uv run python -m memory_stack.evals.cli models \
		--mode fine-grained \
		--fixture-set brain-model-test-v2 \
		--roles durability_filter,atomic_card_extractor,entity_mention_extractor,eval_judge,intent_router,memory_kind_classifier,open_loop_detector,relationship_extractor,repair_option_generator,source_classifier,source_takeaway_extractor,table_policy_handler \
		--models openai:gpt-5.5 \
		--repeat-runs 3 \
		--endpoint-max-concurrency 10 \
		--retry-attempts 3 \
		--output-json eval_runs/targeted_fine_grained/results.json

palate-probe:
	uv run python scripts/palate_cognee_capability_probe.py

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

maintenance:
	uv run python scripts/nightly_maintenance.py --env prod

test:
	uv run pytest

lint:
	uv run ruff check .
