# Cognee-Native Memory Stack — Coding Agent Implementation Plan
## Goal
Build a configurable local memory evaluation harness for a Mac Mini using:
```text
Cognee-native memory
Neo4j graph store
LanceDB vector store
SQLite relational metadata
Claude Desktop / Claude Code via MCP

Model profiles:

1. Google Gemini free-tier challenger
2. OpenAI quality-ceiling baseline
3. Fully local Ollama no-cloud lane

This plan intentionally skips the direct Graphiti lane. Cognee-native temporal memory is tested first via:

remember(..., temporal_cognify=True)
recall(..., search_type="TEMPORAL")

⸻

0. Implementation Principles

Non-negotiables

1. One-command workflow

make setup
make up
make smoke
make eval

2. Provider-switchable

Support:

Google Gemini
OpenAI
Local Ollama

No hard-coded model names in ingestion or recall code.

3. No accidental cloud calls in local mode

When:

PROFILE=local

the system must fail fast if configuration would call OpenAI, Gemini, or another cloud provider.

4. Explicit temporal source anchoring

Every ingested item must include:

origin_id
source_type
source_sent_at
source_from
thread_id
dataset_name
body

5. Eval-first

Every eval run should produce:

profile
provider
model
dataset
query_id
search_type
latency_seconds
raw_result_path
score
notes

⸻

1. Repository Layout

Create:

memory-stack/
  README.md
  Makefile
  pyproject.toml
  docker-compose.yml
  .env.example
  .env.gemini.example
  .env.openai.example
  .env.local.example
  scripts/
    check_env.py
    reset_stores.py
    smoke_cognee.py
    estimate_tokens.py
    export_mcp_config.py
  src/
    memory_stack/
      __init__.py
      config.py
      models.py
      io.py
      normalize_email.py
      ingest_cognee.py
      recall_cognee.py
      eval_cases.py
      eval_runner.py
      scoring.py
      token_costs.py
  data/
    samples/
      synthetic_property_emails.jsonl
      syllabus_notes.jsonl
      palate_notes.jsonl
  eval/
    queries.yaml
    rubric.yaml
    results/
  mcp/
    claude_desktop_config.template.json

⸻

2. Docker Services

Create docker-compose.yml.

services:
  neo4j:
    image: neo4j:5.26
    container_name: neo4j-cognee
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - ${NEO4J_DATA_DIR:-./.data/neo4j}:/data
    environment:
      NEO4J_AUTH: "neo4j/${GRAPH_DATABASE_PASSWORD}"
      NEO4J_PLUGINS: '["apoc"]'

For v1, use:

Neo4j
SQLite
LanceDB

Do not add Postgres, Qdrant, Graphiti, or a web UI in v1.

⸻

3. Python Environment

Use uv.

Create pyproject.toml.

[project]
name = "memory-stack"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "cognee[neo4j,docs]",
  "python-dotenv",
  "pydantic",
  "pydantic-settings",
  "rich",
  "typer",
  "pandas",
  "pyyaml",
  "tiktoken",
]
[project.optional-dependencies]
local = [
  "fastembed",
]

Install:

uv sync --all-extras

⸻

4. Environment Profiles

.env.gemini.example

Google free-tier / paid-tier challenger.

PROFILE=gemini
LLM_PROVIDER=gemini
LLM_MODEL=gemini/gemini-3.1-flash-lite-preview
LLM_API_KEY=AIza...
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=8192
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini/gemini-embedding-001
EMBEDDING_API_KEY=AIza...
EMBEDDING_DIMENSIONS=768
GOOGLE_FREE_TIER=true
GRAPH_DATABASE_PROVIDER=neo4j
GRAPH_DATABASE_URL=bolt://localhost:7687
GRAPH_DATABASE_NAME=neo4j
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=change-me
VECTOR_DB_PROVIDER=lancedb
VECTOR_DB_URL=./.data/lancedb/cognee.lancedb
DB_PROVIDER=sqlite
DB_NAME=cognee_db
SYSTEM_ROOT_DIRECTORY=./.data/system
DATA_ROOT_DIRECTORY=./.data/data

.env.openai.example

Quality-ceiling profile.

PROFILE=openai
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-mini
LLM_API_KEY=sk-...
OPENAI_API_KEY=sk-...
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=8192
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-...
EMBEDDING_DIMENSIONS=1536
GRAPH_DATABASE_PROVIDER=neo4j
GRAPH_DATABASE_URL=bolt://localhost:7687
GRAPH_DATABASE_NAME=neo4j
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=change-me
VECTOR_DB_PROVIDER=lancedb
VECTOR_DB_URL=./.data/lancedb/cognee.lancedb
DB_PROVIDER=sqlite
DB_NAME=cognee_db
SYSTEM_ROOT_DIRECTORY=./.data/system
DATA_ROOT_DIRECTORY=./.data/data

.env.local.example

No-cloud local profile.

PROFILE=local
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:8b
LLM_ENDPOINT=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=4096
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384
GRAPH_DATABASE_PROVIDER=neo4j
GRAPH_DATABASE_URL=bolt://localhost:7687
GRAPH_DATABASE_NAME=neo4j
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=change-me
VECTOR_DB_PROVIDER=lancedb
VECTOR_DB_URL=./.data/lancedb/cognee.lancedb
DB_PROVIDER=sqlite
DB_NAME=cognee_db
SYSTEM_ROOT_DIRECTORY=./.data/system
DATA_ROOT_DIRECTORY=./.data/data

⸻

5. Config Loader

Implement src/memory_stack/config.py.

Use pydantic-settings.

from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    profile: Literal["gemini", "openai", "local"] = "gemini"
    llm_provider: str
    llm_model: str
    llm_api_key: str | None = None
    llm_endpoint: str | None = None
    llm_temperature: float = 0.0
    llm_max_tokens: int = 8192
    embedding_provider: str
    embedding_model: str
    embedding_api_key: str | None = None
    embedding_dimensions: int
    graph_database_provider: str = "neo4j"
    graph_database_url: str
    graph_database_name: str = "neo4j"
    graph_database_username: str
    graph_database_password: str
    vector_db_provider: str = "lancedb"
    vector_db_url: str
    db_provider: str = "sqlite"
    db_name: str = "cognee_db"
    system_root_directory: str
    data_root_directory: str
    google_free_tier: bool = False
    allow_cloud_keys_in_local: bool = False
    @model_validator(mode="after")
    def validate_profile(self):
        if self.profile == "local":
            if self.llm_provider != "ollama":
                raise ValueError("PROFILE=local requires LLM_PROVIDER=ollama")
            if self.embedding_provider not in {"fastembed", "ollama"}:
                raise ValueError(
                    "PROFILE=local requires EMBEDDING_PROVIDER=fastembed or ollama"
                )
            if not self.allow_cloud_keys_in_local:
                cloud_indicators = [
                    self.llm_api_key and self.llm_api_key.startswith("sk-"),
                    self.embedding_api_key and self.embedding_api_key.startswith("sk-"),
                    self.llm_api_key and self.llm_api_key.startswith("AIza"),
                    self.embedding_api_key and self.embedding_api_key.startswith("AIza"),
                ]
                if any(cloud_indicators):
                    raise ValueError(
                        "PROFILE=local appears to contain cloud API keys. "
                        "Set ALLOW_CLOUD_KEYS_IN_LOCAL=true only if intentional."
                    )
        if self.profile == "gemini":
            if self.llm_provider != "gemini":
                raise ValueError("PROFILE=gemini requires LLM_PROVIDER=gemini")
            if self.embedding_provider != "gemini":
                raise ValueError("PROFILE=gemini requires EMBEDDING_PROVIDER=gemini")
        if self.profile == "openai":
            if self.llm_provider != "openai":
                raise ValueError("PROFILE=openai requires LLM_PROVIDER=openai")
            if self.embedding_provider != "openai":
                raise ValueError("PROFILE=openai requires EMBEDDING_PROVIDER=openai")
        return self
def load_settings() -> Settings:
    return Settings()

⸻

6. Environment Checker

Implement scripts/check_env.py.

Requirements:

Load Settings
Print active profile
Print LLM provider/model
Print embedding provider/model
Print graph/vector/db paths
Fail on invalid local/cloud mix

CLI:

uv run python scripts/check_env.py

Expected output:

[OK] profile=gemini
[OK] llm=gemini/gemini-3.1-flash-lite-preview
[OK] embeddings=gemini/gemini-embedding-001
[OK] graph=neo4j bolt://localhost:7687
[OK] vector=lancedb ./.data/lancedb/cognee.lancedb

⸻

7. Canonical Memory Item Schema

Implement src/memory_stack/models.py.

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
class MemoryItem(BaseModel):
    origin_id: str
    source_type: Literal["email", "note", "manual", "document"]
    source_sent_at: datetime
    source_from: str | None = None
    thread_id: str
    dataset_name: str
    title: str | None = None
    body: str
    tags: list[str] = Field(default_factory=list)
    def to_ingestion_text(self) -> str:
        return f"""
Origin-ID: {self.origin_id}
Source-Type: {self.source_type}
Source-Sent-At: {self.source_sent_at.isoformat()}
Source-From: {self.source_from or ""}
Thread: {self.thread_id}
Dataset: {self.dataset_name}
Tags: {", ".join(self.tags)}
Title:
{self.title or ""}
Body:
{self.body}
""".strip()

Purpose: source dates must be explicit in the text so Cognee’s temporal extraction has a reliable anchor.

⸻

8. JSONL I/O

Implement src/memory_stack/io.py.

import json
from pathlib import Path
from typing import Iterable
from memory_stack.models import MemoryItem
def load_memory_items(path: str | Path) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(MemoryItem.model_validate(json.loads(line)))
            except Exception as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
    return items
def write_json(path: str | Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

⸻

9. Sample Data

Create data/samples/synthetic_property_emails.jsonl.

{"origin_id":"email:melcombe:001","source_type":"email","source_sent_at":"2026-04-18T09:13:00+01:00","source_from":"Jason <jason@asbestech.example>","thread_id":"melcombe-section20-asbestos","dataset_name":"property_trial","title":"Principal Designer confirmation","body":"Jason from Asbestech confirmed that Asbestech will act as Principal Designer for the Melcombe Court asbestos works. Quote is £47k and valid for 30 days.","tags":["property","section20","asbestos","principal-designer"]}
{"origin_id":"email:melcombe:002","source_type":"email","source_sent_at":"2026-04-19T14:25:00+01:00","source_from":"Irwin <irwin@example.com>","thread_id":"melcombe-section20-asbestos","dataset_name":"property_trial","title":"CDM Principal Designer disagreement","body":"Irwin disagrees that a separate CDM Principal Designer is needed for the asbestos works. He says the existing arrangements may already satisfy the dutyholder requirements.","tags":["property","section20","asbestos","principal-designer","dispute"]}
{"origin_id":"email:melcombe:003","source_type":"email","source_sent_at":"2026-04-22T10:00:00+01:00","source_from":"Managing Agent <agent@example.com>","thread_id":"melcombe-section20-asbestos","dataset_name":"property_trial","title":"Current position after review","body":"After reviewing the asbestos works scope, the current working position is that Asbestech will remain responsible for design coordination, but the team will seek written confirmation on whether a separate CDM Principal Designer appointment is legally required.","tags":["property","section20","asbestos","current-position"]}

⸻

10. Cognee Ingestion

Implement src/memory_stack/ingest_cognee.py.

Requirements:

Load JSONL memory items
Call cognee.remember(...)
Use temporal_cognify=True by default
Allow temporal flag to be disabled
Allow self_improvement=False by default
Print per-item progress

Implementation sketch:

import asyncio
import time
import typer
from rich.console import Console
import cognee
from memory_stack.io import load_memory_items
app = typer.Typer()
console = Console()
async def ingest_items(
    input_path: str,
    temporal: bool = True,
    self_improvement: bool = False,
) -> None:
    items = load_memory_items(input_path)
    for idx, item in enumerate(items, start=1):
        text = item.to_ingestion_text()
        start = time.perf_counter()
        await cognee.remember(
            text,
            dataset_name=item.dataset_name,
            temporal_cognify=temporal,
            self_improvement=self_improvement,
        )
        elapsed = time.perf_counter() - start
        console.print(
            f"[green]ingested[/green] {idx}/{len(items)} "
            f"{item.origin_id} dataset={item.dataset_name} "
            f"temporal={temporal} elapsed={elapsed:.2f}s"
        )
@app.command()
def main(
    input_path: str = typer.Option(..., "--input"),
    temporal: bool = typer.Option(True, "--temporal/--no-temporal"),
    self_improvement: bool = typer.Option(False, "--self-improvement/--no-self-improvement"),
):
    asyncio.run(ingest_items(input_path, temporal, self_improvement))
if __name__ == "__main__":
    app()

CLI:

uv run python -m memory_stack.ingest_cognee \
  --input data/samples/synthetic_property_emails.jsonl \
  --temporal

⸻

11. Cognee Recall

Implement src/memory_stack/recall_cognee.py.

Requirements:

Accept query
Accept dataset
Accept search_type
Write raw JSON result
Print concise result
Measure latency

Implementation sketch:

import asyncio
import time
from datetime import datetime
from pathlib import Path
import typer
from rich.console import Console
import cognee
from cognee.api.v1.search import SearchType
from memory_stack.io import write_json
app = typer.Typer()
console = Console()
def parse_search_type(value: str) -> SearchType:
    value = value.upper()
    try:
        return SearchType[value]
    except KeyError as exc:
        allowed = ", ".join([x.name for x in SearchType])
        raise typer.BadParameter(f"Unknown search type {value}. Allowed: {allowed}") from exc
async def recall(
    query: str,
    dataset: str,
    search_type: str,
    top_k: int,
    output_dir: str,
):
    query_type = parse_search_type(search_type)
    start = time.perf_counter()
    result = await cognee.recall(
        query_text=query,
        query_type=query_type,
        datasets=[dataset],
        top_k=top_k,
    )
    elapsed = time.perf_counter() - start
    payload = {
        "query": query,
        "dataset": dataset,
        "search_type": search_type,
        "top_k": top_k,
        "latency_seconds": elapsed,
        "result": result,
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(output_dir) / f"recall_{dataset}_{search_type}_{ts}.json"
    write_json(path, payload)
    console.print(f"[green]OK[/green] latency={elapsed:.2f}s output={path}")
    console.print(result)
@app.command()
def main(
    query: str = typer.Option(..., "--query"),
    dataset: str = typer.Option("property_trial", "--dataset"),
    search_type: str = typer.Option("TEMPORAL", "--search-type"),
    top_k: int = typer.Option(10, "--top-k"),
    output_dir: str = typer.Option("eval/results/raw", "--output-dir"),
):
    asyncio.run(recall(query, dataset, search_type, top_k, output_dir))
if __name__ == "__main__":
    app()

CLI:

uv run python -m memory_stack.recall_cognee \
  --dataset property_trial \
  --search-type TEMPORAL \
  --query "What is our current position on the Principal Designer question?"

⸻

12. Smoke Test

Implement scripts/smoke_cognee.py.

Smoke test should:

1. Load settings
2. Ingest synthetic_property_emails.jsonl
3. Run TEMPORAL query
4. Run GRAPH_COMPLETION or equivalent graph query
5. Print pass/warn/fail

Queries:

What happened about the Principal Designer issue?
What is our current position on whether a separate CDM Principal Designer is required?
Who is involved in the Melcombe Court asbestos works and what are their roles?

Pass conditions:

Result mentions Asbestech
Result mentions Jason or Irwin
Result mentions Principal Designer
Result distinguishes confirmation from disagreement at least partially

Output example:

[PASS] ingest succeeded
[PASS] temporal recall returned Principal Designer context
[WARN] contradiction distinction weak
[PASS] relation query returned Asbestech

⸻

13. Eval Queries

Create eval/queries.yaml.

queries:
  - id: current_pd_position
    dataset: property_trial
    search_type: TEMPORAL
    query: "What is our current position on whether a separate CDM Principal Designer is required?"
    must_include:
      - "Principal Designer"
      - "Asbestech"
      - "Irwin"
    rubric:
      temporal_anchor: 0.25
      contradiction_separation: 0.30
      source_trace: 0.25
      current_state: 0.20
  - id: involved_asbestos_work
    dataset: property_trial
    search_type: GRAPH_COMPLETION
    query: "Who is currently involved in the Melcombe Court asbestos works and what is their role?"
    must_include:
      - "Asbestech"
      - "Melcombe Court"
    rubric:
      entity_recall: 0.35
      role_accuracy: 0.35
      source_trace: 0.30
  - id: what_happened_last_week
    dataset: property_trial
    search_type: TEMPORAL
    query: "What happened last week about the Melcombe Court asbestos works?"
    must_include:
      - "Melcombe Court"
      - "asbestos"
    rubric:
      temporal_filtering: 0.40
      completeness: 0.30
      source_trace: 0.30
  - id: dispute_summary
    dataset: property_trial
    search_type: TEMPORAL
    query: "Who disagreed with the Principal Designer position and what exactly was the disagreement?"
    must_include:
      - "Irwin"
      - "disagrees"
      - "CDM"
    rubric:
      contradiction_separation: 0.50
      source_trace: 0.30
      wording_accuracy: 0.20
  - id: open_threads_week
    dataset: property_trial
    search_type: TEMPORAL
    query: "What happened across my open property threads this week?"
    must_include:
      - "Melcombe"
    rubric:
      temporal_filtering: 0.40
      thread_grouping: 0.30
      completeness: 0.30

⸻

14. Scoring

Implement src/memory_stack/scoring.py.

v1 scoring can be simple and semi-automatic.

def score_must_include(result_text: str, must_include: list[str]) -> float:
    if not must_include:
        return 1.0
    lower = result_text.lower()
    hits = sum(1 for term in must_include if term.lower() in lower)
    return hits / len(must_include)
def score_result(result_text: str, must_include: list[str]) -> dict:
    inclusion_score = score_must_include(result_text, must_include)
    return {
        "score": inclusion_score,
        "method": "must_include_v1",
        "notes": "Manual rubric review still required for contradiction/current-state quality.",
    }

Manual review remains required for:

current_state
contradiction_separation
source_trace
temporal_filtering

⸻

15. Eval Runner

Implement src/memory_stack/eval_runner.py.

Requirements:

Load eval/queries.yaml
Run each query
Record latency
Save raw JSON
Save CSV summary
Include profile/provider/model

Output CSV columns:

timestamp
profile
llm_provider
llm_model
embedding_provider
embedding_model
dataset
query_id
search_type
query
latency_seconds
score
raw_result_path
notes

CLI:

uv run python -m memory_stack.eval_runner \
  --queries eval/queries.yaml \
  --output eval/results/results.csv

⸻

16. Token and Cost Estimator

Implement src/memory_stack/token_costs.py.

Price table:

PRICES = {
    "gpt-5-mini": {
        "input": 0.25,
        "output": 2.00,
        "embedding": 0.02,
    },
    "gpt-5.4-mini": {
        "input": 0.75,
        "output": 4.50,
        "embedding": 0.02,
    },
    "gemini-3.1-flash-lite-preview": {
        "input": 0.25,
        "output": 1.50,
        "embedding": 0.15,
    },
    "gemini-3-flash-preview": {
        "input": 0.50,
        "output": 3.00,
        "embedding": 0.15,
    },
}

Estimator assumptions:

source_tokens = estimated from text
chunk_size = default 1024 unless overridden
chunks = ceil(source_tokens / chunk_size)
llm_calls = chunks * 2
input_tokens_low = source_tokens * 3.5
input_tokens_high = source_tokens * 5.5
output_tokens_low = source_tokens * 0.4
output_tokens_high = source_tokens * 1.4
embedding_tokens_low = source_tokens * 1.2
embedding_tokens_high = source_tokens * 2.0
temporal_multiplier = 1.25 to 1.75

Implement scripts/estimate_tokens.py.

CLI:

uv run python scripts/estimate_tokens.py \
  --input data/samples/synthetic_property_emails.jsonl \
  --model gemini-3.1-flash-lite-preview \
  --google-free-tier true

Output:

source_tokens: 2400
chunks: 3
llm_calls: 6
standard_ingest_paid_estimate: $...
temporal_ingest_paid_estimate: $...
reported_cost_with_free_tier: $0

⸻

17. Store Reset

Implement scripts/reset_stores.py.

Modes:

uv run python scripts/reset_stores.py --soft
uv run python scripts/reset_stores.py --hard

Soft reset:

Cognee metadata prune if available
Clear eval/results/raw
Keep Docker volume

Hard reset:

Delete ./.data/
Restart Neo4j container

Important: switching embedding dimensions requires reset.

OpenAI embeddings: 1536 dims
Gemini embeddings: 768 dims
Fastembed MiniLM: 384 dims

If dimension changes, force reset or refuse to run unless:

ALLOW_EMBEDDING_DIMENSION_CHANGE=true

⸻

18. MCP Config Export

Implement scripts/export_mcp_config.py.

Goal: generate Claude Desktop config from current .env.

Output shape:

{
  "mcpServers": {
    "cognee": {
      "command": "/absolute/path/to/python",
      "args": ["/absolute/path/to/cognee-mcp/src/server.py"],
      "env": {
        "LLM_PROVIDER": "...",
        "LLM_MODEL": "...",
        "LLM_API_KEY": "...",
        "EMBEDDING_PROVIDER": "...",
        "EMBEDDING_MODEL": "...",
        "EMBEDDING_API_KEY": "...",
        "GRAPH_DATABASE_PROVIDER": "neo4j",
        "GRAPH_DATABASE_URL": "bolt://localhost:7687",
        "GRAPH_DATABASE_USERNAME": "neo4j",
        "GRAPH_DATABASE_PASSWORD": "...",
        "VECTOR_DB_PROVIDER": "lancedb",
        "VECTOR_DB_URL": "...",
        "DB_PROVIDER": "sqlite",
        "DB_NAME": "cognee_db",
        "SYSTEM_ROOT_DIRECTORY": "...",
        "DATA_ROOT_DIRECTORY": "..."
      }
    }
  }
}

Command:

uv run python scripts/export_mcp_config.py

Do not overwrite Claude config automatically unless:

--write

Print target path:

~/Library/Application Support/Claude/claude_desktop_config.json

⸻

19. Makefile

Create Makefile.

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
tokens:
	uv run python scripts/estimate_tokens.py --input data/samples/synthetic_property_emails.jsonl
reset:
	uv run python scripts/reset_stores.py --soft
reset-hard:
	uv run python scripts/reset_stores.py --hard
mcp-config:
	uv run python scripts/export_mcp_config.py

⸻

20. Local Ollama Setup

For no-cloud profile:

brew install ollama
ollama serve
ollama pull qwen3:8b

If using Ollama embeddings instead of Fastembed:

ollama pull nomic-embed-text:latest

But v1 local profile should use:

qwen3:8b for LLM
Fastembed for embeddings

Reason: avoids Ollama embedding throughput bottleneck.

⸻

21. Model Profiles to Compare

Profile A — Google free-tier challenger

LLM_PROVIDER=gemini
LLM_MODEL=gemini/gemini-3.1-flash-lite-preview
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini/gemini-embedding-001
GOOGLE_FREE_TIER=true

Purpose:

Free or cheap first pass.

Profile B — OpenAI quality ceiling

LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-mini
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

Purpose:

Determine whether Gemini free-tier quality is acceptable.

Profile C — Local no-cloud lane

LLM_PROVIDER=ollama
LLM_MODEL=qwen3:8b
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

Purpose:

Privacy-first smoke test.

Do not judge Cognee architecture from local failure. A local 8B model failing temporal extraction usually indicates model-capacity limits, not necessarily architecture failure.

⸻

22. Acceptance Criteria

Phase 1 — Infrastructure

Pass if:

Neo4j starts
Cognee imports
.env profile validates
Gemini profile loads
OpenAI profile loads
Local profile loads
MCP config can be generated

Phase 2 — Cognee-native Memory

Pass if:

temporal_cognify=True succeeds
TEMPORAL recall works
source dates are reflected in answers
Principal Designer sample can be retrieved
Irwin disagreement is retrieved

Phase 3 — Model Comparison

Pass if eval table contains results for:

gemini-3.1-flash-lite-preview
gpt-5.4-mini
qwen3:8b

against the same dataset and same queries.

Phase 4 — Decision

Promote Gemini free-tier only if it matches the OpenAI quality-ceiling profile on:

entity extraction
role extraction
temporal anchoring
contradiction separation
source/audit trail
current-position retrieval

⸻

23. Coding Agent Task Breakdown

Task 1 — Create repo skeleton

Deliverables:

repo layout
pyproject.toml
Makefile
.env examples
docker-compose.yml

Done when:

make setup
make up

run successfully.

⸻

Task 2 — Implement config validation

Deliverables:

src/memory_stack/config.py
scripts/check_env.py

Done when:

uv run python scripts/check_env.py

validates each profile and rejects unsafe local/cloud mixes.

⸻

Task 3 — Implement canonical memory item

Deliverables:

src/memory_stack/models.py
src/memory_stack/io.py
data/samples/synthetic_property_emails.jsonl

Done when a sample email becomes deterministic ingestion text with explicit date metadata.

⸻

Task 4 — Implement Cognee ingestion and recall

Deliverables:

src/memory_stack/ingest_cognee.py
src/memory_stack/recall_cognee.py

Done when:

make ingest-sample
make recall-sample

work.

⸻

Task 5 — Implement smoke test

Deliverables:

scripts/smoke_cognee.py

Done when:

make smoke

passes or emits actionable warnings.

⸻

Task 6 — Implement eval harness

Deliverables:

eval/queries.yaml
src/memory_stack/scoring.py
src/memory_stack/eval_runner.py

Done when:

make eval

produces CSV and raw JSON results.

⸻

Task 7 — Implement token estimator

Deliverables:

src/memory_stack/token_costs.py
scripts/estimate_tokens.py

Done when:

make tokens

returns estimated standard and temporal ingest costs.

⸻

Task 8 — Implement MCP config exporter

Deliverables:

scripts/export_mcp_config.py
mcp/claude_desktop_config.template.json

Done when it prints a valid Claude Desktop MCP config using absolute paths.

⸻

Task 9 — Implement reset strategy

Deliverables:

scripts/reset_stores.py

Done when:

make reset
make reset-hard

work and warn on embedding-dimension changes.

⸻

24. Things Not to Build in v1

Do not build:

direct Graphiti lane
custom Graphiti MCP wrapper
custom ontology editor
automatic Gmail ingestion
multi-user auth
web UI
production backup system
palate integration
Postgres deployment
Qdrant deployment

These are Phase 2+.

⸻

25. Final Instruction to Coding Agent

Build a configurable local memory evaluation harness, not a production product.

Primary execution order:

1. Repo skeleton
2. Docker Neo4j
3. Env validation
4. Canonical memory item schema
5. Cognee ingest/recall
6. Smoke test
7. Eval harness
8. Model profile switching
9. MCP config exporter
10. Token estimator
11. Reset tooling

Primary model comparison:

A. gemini-3.1-flash-lite-preview  # free-tier challenger
B. gpt-5.4-mini                   # quality ceiling
C. qwen3:8b                       # no-cloud local lane

Primary success criterion:

Gemini free-tier is acceptable only if it matches gpt-5.4-mini on:
  temporal anchoring
  contradiction separation
  source/audit trail
  current-position retrieval

Core hypothesis being tested:

Cognee-native temporal memory is sufficient for the personal memory system without adding direct Graphiti integration.