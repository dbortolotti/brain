# Purpose

- Own source classification and parsing for articles, transcripts, tables, and ingestion input types.

## Ownership

- `classifier.py` owns source-kind to input-type classification.
- `article_loader.py`, `transcript_parser.py`, and `table_parser.py` own source extraction and normalization.

## Local Contracts

- Parsers should produce deterministic text or structured data suitable for Brain service ingestion.
- Do not persist full source payloads outside explicit ingestion paths or tests.
- Keep source-kind behavior aligned with `brain_service.py`, request models, and agent docs.

## Work Guidance

- Prefer structured parsing over brittle string slicing when a parser is available.
- Include focused tests for new source formats or ambiguous classification behavior.

## Verification

- Run targeted ingestion or service tests affected by parser changes.
- Run `uv run pytest tests/test_brain_service.py` when ingestion behavior reaches the service layer.

## Child DOX Index

- No child AGENTS.md files. All ingestion helpers are owned here.
