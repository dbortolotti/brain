from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
import time
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from memory_stack.cognee_adapter import add_text, cognify_dataset, recall_text
from memory_stack.config import Settings, load_settings
from memory_stack.evals.model_matrix import candidate_from_ref
from memory_stack.evals.provider_client import LiveProviderClient


FIXTURE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = FIXTURE_DIR / "runs"
MANETTI_QUESTIONS = FIXTURE_DIR / "manetti_100_questions.json"
MANETTI_DOCUMENT = FIXTURE_DIR / "manetti_document.md"
ORGANIC_FIXTURE = FIXTURE_DIR / "organic_recall_100_cases.json"
JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class EvalQuestion:
    suite: str
    question_id: str
    difficulty: int
    query: str
    expected: Any
    evidence: str | None = None
    relevant_seed_ids: list[str] | None = None


def model_arg(value: str) -> str:
    return value.split(":", 1)[1] if value.startswith("openai:") else value


def model_ref(value: str) -> str:
    return value if ":" in value else f"openai:{value}"


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def now_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def settings_for_model(model: str, dataset: str) -> Settings:
    base = load_settings()
    return base.model_copy(
        update={
            "brain_cognee_execution_backend": "local",
            "brain_taste_enabled": False,
            "brain_cognee_memory_dataset": dataset,
            "llm_provider": "openai",
            "llm_model": model_arg(model),
        }
    )


def cognee_answer_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        pieces: list[str] = []
        for item in value:
            result = getattr(item, "search_result", item)
            pieces.append(cognee_answer_text(result))
        return "\n\n".join(piece for piece in pieces if piece)
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return str(value)


def organic_seed_text(seed: dict[str, Any], index: int) -> str:
    lines = [
        f"Organic recall fixture seed {index}: {seed['id']}",
        f"Status: {seed['status']}",
        f"Write path: {seed['write_path']}",
        f"Tags: {', '.join(seed.get('tags', []))}",
        f"Expected terms: {', '.join(seed.get('expected_terms', []))}",
        "",
        "Content:",
        seed["input"].strip(),
    ]
    return "\n".join(lines).strip()


def load_questions(
    *,
    limit_manetti: int | None = None,
    limit_organic: int | None = None,
) -> tuple[list[EvalQuestion], list[dict[str, Any]], str]:
    manetti_doc = MANETTI_DOCUMENT.read_text(encoding="utf-8")
    manetti_payload = load_json(MANETTI_QUESTIONS)
    organic_payload = load_json(ORGANIC_FIXTURE)

    questions: list[EvalQuestion] = []
    manetti_questions = manetti_payload["questions"]
    if limit_manetti is not None:
        manetti_questions = manetti_questions[:limit_manetti]
    for item in manetti_questions:
        questions.append(
            EvalQuestion(
                suite="manetti",
                question_id=item["question_id"],
                difficulty=int(item["difficulty"]),
                query=item["question"],
                expected=item["expected_answer"],
                evidence=item.get("evidence"),
            )
        )

    organic_cases = organic_payload["recall_cases"]
    if limit_organic is not None:
        organic_cases = organic_cases[:limit_organic]
    for item in organic_cases:
        questions.append(
            EvalQuestion(
                suite="organic",
                question_id=item["id"],
                difficulty=int(item["difficulty"]),
                query=item["query"],
                expected=item["expected"],
                relevant_seed_ids=list(item.get("relevant_seed_ids", [])),
            )
        )
    return questions, organic_payload["seed_inserts"], manetti_doc


@contextmanager
def append_jsonl(path: Path) -> Iterator[Any]:
    with path.open("a", encoding="utf-8") as handle:
        yield handle


def write_jsonl(handle: Any, record: dict[str, Any]) -> None:
    handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    handle.flush()


async def ingest_fixture_material(
    *,
    dataset: str,
    remember_model: str,
    manetti_doc: str,
    organic_seeds: list[dict[str, Any]],
    output_dir: Path,
    add_timeout_s: float,
    cognify_timeout_s: float,
) -> dict[str, Any]:
    settings = settings_for_model(remember_model, dataset)
    timings_path = output_dir / "ingestion_timings.jsonl"
    summary: dict[str, Any] = {
        "remember_model": model_ref(remember_model),
        "dataset": dataset,
        "manetti": {},
        "organic": {"seed_count": len(organic_seeds), "seeds": []},
    }

    with append_jsonl(timings_path) as timings:
        started = time.perf_counter()
        add_started = time.perf_counter()
        await asyncio.wait_for(
            add_text(
                "Manetti document fixture\n\n" + manetti_doc,
                dataset_name=dataset,
                settings=settings,
            ),
            timeout=add_timeout_s,
        )
        manetti_add_s = time.perf_counter() - add_started
        cognify_started = time.perf_counter()
        await asyncio.wait_for(
            cognify_dataset(dataset, temporal=False, settings=settings),
            timeout=cognify_timeout_s,
        )
        manetti_cognify_s = time.perf_counter() - cognify_started
        manetti_total_s = time.perf_counter() - started
        summary["manetti"] = {
            "source": str(MANETTI_DOCUMENT),
            "bytes": len(manetti_doc.encode("utf-8")),
            "add_seconds": round(manetti_add_s, 3),
            "cognify_seconds": round(manetti_cognify_s, 3),
            "total_seconds": round(manetti_total_s, 3),
        }
        write_jsonl(timings, {"phase": "ingest_manetti", **summary["manetti"]})

        organic_started = time.perf_counter()
        organic_add_total = 0.0
        for index, seed in enumerate(organic_seeds, 1):
            text = organic_seed_text(seed, index)
            seed_started = time.perf_counter()
            await asyncio.wait_for(
                add_text(text, dataset_name=dataset, settings=settings),
                timeout=add_timeout_s,
            )
            elapsed = time.perf_counter() - seed_started
            organic_add_total += elapsed
            seed_timing = {
                "phase": "ingest_organic_seed",
                "index": index,
                "seed_id": seed["id"],
                "status": seed["status"],
                "write_path": seed["write_path"],
                "add_seconds": round(elapsed, 3),
                "input_bytes": len(text.encode("utf-8")),
            }
            summary["organic"]["seeds"].append(seed_timing)
            write_jsonl(timings, seed_timing)

        organic_cognify_started = time.perf_counter()
        await asyncio.wait_for(
            cognify_dataset(dataset, temporal=False, settings=settings),
            timeout=cognify_timeout_s,
        )
        organic_cognify_s = time.perf_counter() - organic_cognify_started
        organic_total_s = time.perf_counter() - organic_started
        summary["organic"].update(
            {
                "add_seconds": round(organic_add_total, 3),
                "cognify_seconds": round(organic_cognify_s, 3),
                "total_seconds": round(organic_total_s, 3),
            }
        )
        write_jsonl(
            timings,
            {
                "phase": "ingest_organic_total",
                "seed_count": len(organic_seeds),
                "add_seconds": round(organic_add_total, 3),
                "cognify_seconds": round(organic_cognify_s, 3),
                "total_seconds": round(organic_total_s, 3),
            },
        )

    (output_dir / "ingestion_timings.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return summary


async def recall_questions(
    *,
    dataset: str,
    recall_model: str,
    questions: list[EvalQuestion],
    output_dir: Path,
    search_type: str,
    top_k: int,
    timeout_s: float,
) -> list[dict[str, Any]]:
    settings = settings_for_model(recall_model, dataset)
    answers: list[dict[str, Any]] = []
    answers_path = output_dir / "answers.jsonl"

    with append_jsonl(answers_path) as handle:
        for index, question in enumerate(questions, 1):
            print(f"[{index}/{len(questions)}] recall {question.suite}:{question.question_id}", flush=True)
            started = time.perf_counter()
            status = "ok"
            error = None
            raw: Any = None
            try:
                with redirect_stdout(sys.stderr):
                    raw = await asyncio.wait_for(
                        recall_text(
                            query=question.query,
                            dataset=dataset,
                            search_type=search_type,
                            top_k=top_k,
                            settings=settings,
                        ),
                        timeout=timeout_s,
                    )
            except Exception as exc:
                status = "error"
                error = str(exc)
            elapsed = time.perf_counter() - started
            answer = cognee_answer_text(raw) if status == "ok" else ""
            record = {
                "suite": question.suite,
                "question_id": question.question_id,
                "difficulty": question.difficulty,
                "query": question.query,
                "expected": question.expected,
                "evidence": question.evidence,
                "relevant_seed_ids": question.relevant_seed_ids,
                "recall_model": model_ref(recall_model),
                "dataset": dataset,
                "search_type": search_type,
                "top_k": top_k,
                "status": status,
                "error": error,
                "answer": answer,
                "raw_result": raw,
                "recall_seconds": round(elapsed, 3),
            }
            answers.append(record)
            write_jsonl(handle, record)
    return answers


def organic_context(
    question: EvalQuestion,
    seeds_by_id: dict[str, dict[str, Any]],
) -> str:
    ids = question.relevant_seed_ids or []
    selected = [seeds_by_id[seed_id] for seed_id in ids if seed_id in seeds_by_id]
    return json.dumps(selected, indent=2, ensure_ascii=False)


def judge_prompt(
    *,
    answer_record: dict[str, Any],
    question: EvalQuestion,
    manetti_doc: str,
    seeds_by_id: dict[str, dict[str, Any]],
) -> str:
    if question.suite == "manetti":
        source_context = (
            "The full Manetti document follows. Use it as the authoritative source.\n\n"
            f"{manetti_doc}"
        )
    else:
        source_context = (
            "The relevant organic recall seed fixture records follow. Use these records, "
            "including status fields, as the authoritative source.\n\n"
            f"{organic_context(question, seeds_by_id)}"
        )
    return f"""You are scoring a model answer for a recall evaluation.

Score only the answer's factual correctness against the authoritative context and expected answer.
Return JSON matching the schema.

Rubric:
1 = wrong or unrelated.
2 = mostly wrong, but contains one relevant fragment.
3 = partially correct, with missing required facts or important unsupported claims.
4 = correct on the main point, with minor omissions or imprecision.
5 = fully correct and directly answers the question without material unsupported claims.

Question suite: {question.suite}
Question id: {question.question_id}
Difficulty: {question.difficulty}
Question: {question.query}
Expected answer/checks: {json.dumps(question.expected, ensure_ascii=False)}
Expected evidence: {question.evidence or ""}

Candidate answer:
{answer_record.get("answer") or ""}

Authoritative context:
{source_context}
"""


def score_answers(
    *,
    judge_model: str,
    answers: list[dict[str, Any]],
    questions: list[EvalQuestion],
    manetti_doc: str,
    organic_seeds: list[dict[str, Any]],
    output_dir: Path,
    timeout_s: float,
) -> list[dict[str, Any]]:
    settings = load_settings()
    candidate = candidate_from_ref(model_ref(judge_model), roles={"judge"})
    client = LiveProviderClient(settings, timeout_seconds=timeout_s, retry_attempts=1)
    question_by_key = {(q.suite, q.question_id): q for q in questions}
    seeds_by_id = {seed["id"]: seed for seed in organic_seeds}
    scores: list[dict[str, Any]] = []

    with append_jsonl(output_dir / "scores.jsonl") as handle:
        for index, answer in enumerate(answers, 1):
            key = (answer["suite"], answer["question_id"])
            question = question_by_key[key]
            print(f"[{index}/{len(answers)}] judge {question.suite}:{question.question_id}", flush=True)
            result = client.complete_json(
                candidate,
                prompt=judge_prompt(
                    answer_record=answer,
                    question=question,
                    manetti_doc=manetti_doc,
                    seeds_by_id=seeds_by_id,
                ),
                schema=JUDGE_SCHEMA,
            )
            payload = result.payload if result.status == "ok" and result.payload else {}
            score = payload.get("score")
            record = {
                "suite": answer["suite"],
                "question_id": answer["question_id"],
                "difficulty": answer["difficulty"],
                "query": answer["query"],
                "expected": answer["expected"],
                "answer": answer["answer"],
                "recall_model": answer["recall_model"],
                "judge_model": candidate.ref,
                "score": score,
                "judge_reason": payload.get("reason"),
                "judge_status": result.status,
                "judge_error": result.error,
                "judge_latency_ms": result.latency_ms,
                "judge_input_tokens_est": result.input_tokens,
                "judge_output_tokens_est": result.output_tokens,
                "judge_estimated_cost_usd": result.estimated_cost_usd,
                "recall_seconds": answer["recall_seconds"],
            }
            scores.append(record)
            write_jsonl(handle, record)
    return scores


def write_scores_csv(path: Path, scores: list[dict[str, Any]]) -> None:
    fields = [
        "suite",
        "question_id",
        "difficulty",
        "score",
        "recall_seconds",
        "judge_latency_ms",
        "query",
        "expected",
        "answer",
        "judge_reason",
        "judge_status",
        "judge_error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(scores)


def markdown_report(
    *,
    config: dict[str, Any],
    ingestion: dict[str, Any],
    scores: list[dict[str, Any]],
) -> str:
    scored = [row for row in scores if isinstance(row.get("score"), int)]
    avg = sum(row["score"] for row in scored) / len(scored) if scored else 0
    lines = [
        "# Model Eval Test Run",
        "",
        f"- Run id: `{config['run_id']}`",
        f"- Dataset: `{config['dataset']}`",
        f"- Remember model: `{config['remember_model']}`",
        f"- Recall model: `{config['recall_model']}`",
        f"- Judge model: `{config['judge_model']}`",
        f"- Questions: {len(scores)}",
        f"- Average score: {avg:.2f}",
        f"- Manetti ingestion: {ingestion['manetti']['total_seconds']}s",
        f"- Organic ingestion: {ingestion['organic']['total_seconds']}s",
        "",
        "## Average Score by Suite and Difficulty",
        "",
        "| Suite | Difficulty | Questions | Average score | Average recall seconds |",
        "|---|---:|---:|---:|---:|",
    ]
    for suite in ("manetti", "organic"):
        for difficulty in range(1, 6):
            rows = [
                row
                for row in scores
                if row["suite"] == suite
                and row["difficulty"] == difficulty
                and isinstance(row.get("score"), int)
            ]
            if not rows:
                continue
            score_avg = sum(row["score"] for row in rows) / len(rows)
            recall_avg = sum(float(row["recall_seconds"]) for row in rows) / len(rows)
            lines.append(
                f"| {suite} | {difficulty} | {len(rows)} | {score_avg:.2f} | {recall_avg:.3f} |"
            )
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `answers.jsonl`: one recall answer per question, including recall timing.",
            "- `scores.jsonl`: one judged answer per question, including score and judge timing.",
            "- `scores.csv`: flat table for spreadsheet analysis.",
            "- `ingestion_timings.jsonl`: Manetti, per-seed organic, and aggregate ingestion timings.",
        ]
    )
    return "\n".join(lines) + "\n"


async def run(args: argparse.Namespace) -> dict[str, Any]:
    run_id = args.run_id or now_id()
    dataset = args.dataset or (
        f"model_eval_tests_{slug(args.remember_model)}_remember_"
        f"{slug(args.recall_model)}_recall_{run_id}"
    )
    output_dir = (args.output_dir or DEFAULT_OUTPUT_DIR) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    questions, organic_seeds, manetti_doc = load_questions(
        limit_manetti=args.limit_manetti,
        limit_organic=args.limit_organic,
    )
    config = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": dataset,
        "judge_model": model_ref(args.judge_model),
        "remember_model": model_ref(args.remember_model),
        "recall_model": model_ref(args.recall_model),
        "search_type": args.search_type,
        "top_k": args.top_k,
        "question_count": len(questions),
        "manetti_question_count": sum(1 for q in questions if q.suite == "manetti"),
        "organic_question_count": sum(1 for q in questions if q.suite == "organic"),
        "fixture_dir": str(FIXTURE_DIR),
    }
    (output_dir / "config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    ingestion = await ingest_fixture_material(
        dataset=dataset,
        remember_model=args.remember_model,
        manetti_doc=manetti_doc,
        organic_seeds=organic_seeds,
        output_dir=output_dir,
        add_timeout_s=args.add_timeout_s,
        cognify_timeout_s=args.cognify_timeout_s,
    )
    answers = await recall_questions(
        dataset=dataset,
        recall_model=args.recall_model,
        questions=questions,
        output_dir=output_dir,
        search_type=args.search_type,
        top_k=args.top_k,
        timeout_s=args.recall_timeout_s,
    )
    scores = score_answers(
        judge_model=args.judge_model,
        answers=answers,
        questions=questions,
        manetti_doc=manetti_doc,
        organic_seeds=organic_seeds,
        output_dir=output_dir,
        timeout_s=args.judge_timeout_s,
    )
    write_scores_csv(output_dir / "scores.csv", scores)
    report = markdown_report(config=config, ingestion=ingestion, scores=scores)
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    summary = {
        **config,
        "output_dir": str(output_dir),
        "average_score": round(
            sum(row["score"] for row in scores if isinstance(row.get("score"), int))
            / max(1, sum(1 for row in scores if isinstance(row.get("score"), int))),
            3,
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a fresh Cognee dataset, ingest Manetti plus organic recall fixtures, "
            "recall all 200 questions, and judge every answer."
        )
    )
    parser.add_argument("--judge-model", required=True, help="Judge model, e.g. gpt-5.5.")
    parser.add_argument("--remember-model", required=True, help="Cognee ingestion model.")
    parser.add_argument("--recall-model", required=True, help="Cognee recall model.")
    parser.add_argument("--dataset", help="Dataset name. Defaults to a unique run dataset.")
    parser.add_argument("--run-id", help="Run id. Defaults to UTC timestamp.")
    parser.add_argument("--output-dir", type=Path, help=f"Default: {DEFAULT_OUTPUT_DIR}")
    parser.add_argument("--search-type", default="GRAPH_COMPLETION")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--add-timeout-s", type=float, default=180)
    parser.add_argument("--cognify-timeout-s", type=float, default=1800)
    parser.add_argument("--recall-timeout-s", type=float, default=180)
    parser.add_argument("--judge-timeout-s", type=float, default=240)
    parser.add_argument("--limit-manetti", type=int, help="Development-only question limit.")
    parser.add_argument("--limit-organic", type=int, help="Development-only question limit.")
    return parser.parse_args()


def main() -> None:
    summary = asyncio.run(run(parse_args()))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
