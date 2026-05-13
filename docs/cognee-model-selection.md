# Cognee Model Selection

Ingestion timing for the Manetti corpus:

| Candidate dataset | Ingestion model setting | Add step | Cognee graph/cognify step | Total wall time | Peak RSS |
|---|---:|---:|---:|---:|---:|
| `menotti-54-mini` | `gpt-5.4-mini` | 0.56s | 40.615s | 43.31s | ~793 MiB |
| `menotti-55-low` | `gpt-5.5` low-effort run | 0.466s | 280.668s | 283.27s | ~1.07 GiB |
| `menotti-55-high` | `gpt-5.5` high-effort run | 0.461s | 882.753s | 885.39s | ~1.32 GiB |

The ingestion data strongly separates the candidates before answer quality is scored. The `gpt-5.4-mini` ingestion run completed in about 43 seconds. The `gpt-5.5` low-effort run took about 4.7 minutes, and the high-effort run took about 14.8 minutes. For this corpus, high effort is about 20x slower than `gpt-5.4-mini` ingestion.

## What We Are Testing

This test is a model-selection benchmark for local Cognee ingestion. The goal is to decide which model setting should be used to build a Cognee graph/vector dataset for a large scholarly source.

Each candidate dataset was built from the same source file, then queried with the same generated 100-question evaluation set. The candidate names are dataset names, not source names:

- `menotti-54-mini`: the source ingested with `gpt-5.4-mini`.
- `menotti-55-low`: the source ingested with `gpt-5.5` in the low-effort candidate run.
- `menotti-55-high`: the source ingested with `gpt-5.5` in the high-effort candidate run.

The answer synthesis step used `gpt-5.5` for the query harness, so the comparison is primarily about what the ingestion model produced in Cognee's stored graph/vector representation, not about changing the answer model.

## Corpus

The test corpus is:

`/Volumes/xpg_usb4/sandbox/git/banti/md_sources/Secondary Sources/Manetti_DaUnPaeseLontano_Banti.pdf.md`

The artifact logs record it as a 489,900-byte markdown source with 66,726 words. The text contains Lucy Delogu's dissertation, "Chi sono io? Narrazione storica e soggettivita nella Camicia bruciata di Anna Banti", submitted to Rutgers. It analyzes Anna Banti, her historical fiction, feminism, female subjectivity, and especially `La camicia bruciata`.

This is a good stress test because it is long enough to require multi-hop retrieval and graph structure. The question set covers front-matter facts, chapter titles, named people, historical and literary relationships, interpretive claims, and fine distinctions between documented history and Banti's hypothetical reconstruction.

## Evaluation Method

The 100-question set was generated from the full line-numbered corpus and saved here:

- `artifacts/manetti_candidate_eval_questions_latest.json`
- `artifacts/manetti_candidate_eval_questions_latest.md`
- `artifacts/manetti_candidate_eval_questions_latest.txt`

The question distribution is:

| Difficulty | Count |
|---:|---:|
| 1 | 31 |
| 2 | 41 |
| 3 | 20 |
| 4 | 7 |
| 5 | 1 |

The main category coverage is factual recall, named entities, themes, interpretation, semantic relationships, temporal questions, historical method, and uncertainty.

Each candidate was queried with `artifacts/ask_cognee_dataset.py`, using:

- `--query-type GRAPH_COMPLETION`
- `--top-k 10` by default
- answer model `gpt-5.5`
- the same 100 questions in the same order

The intended scoring phase is one row per candidate/question with a 1-5 score and a short scoring note. That final scored table has not been written yet in the current artifact set.

## Current Artifact Status

| Candidate dataset | Raw answers available | Status |
|---|---:|---|
| `menotti-54-mini` | 100/100 | Complete raw answer run |
| `menotti-55-low` | 100/100 | Complete raw answer run |
| `menotti-55-high` | 55/100 | Partial raw answer run |

Raw answer artifacts:

- `artifacts/manetti_candidate_eval_menotti-54-mini_latest_raw.jsonl`
- `artifacts/manetti_candidate_eval_menotti-55-low_latest_raw.jsonl`
- `artifacts/manetti_candidate_eval_menotti-55-high_20260513_141703_raw.jsonl`

Because the `menotti-55-high` query run is partial and the scored table is missing, the current data should be treated as a benchmark snapshot, not the final model-selection result.

## Initial Read On `menotti-54-mini`

`menotti-54-mini` returned an answer for every one of the 100 questions. A spot check shows it is strong on direct factual recall and many medium-depth interpretive questions, but it has several clear retrieval or graph confusions.

Good examples:

- `mq001` through `mq009`: correctly answers dissertation author, university, director, date, Banti's real name, dates, focus novel, publication year, and dedication.
- `mq013`: correctly identifies Hibbert's `The House of Medici` and Acton's `The Last Medici`.
- `mq032` through `mq050`: mostly handles the women's movement, fascism, Banti's historical interpretation, and "black holes" of history.
- `mq093` and `mq094`: gives plausible high-level answers about historical truth and the historian/novelist distinction.

Observed failure modes:

- Chapter/title confusion. `mq010` asks for Delogu's Chapter One title but receives a chapter title from `La camicia bruciata`; `mq012` asks for Delogu's Chapter Four title but receives Chapter Three's topic.
- Theme overgeneralization. `mq021` asks for the central question "Chi sono io?", but the answer generalizes to the `questione femminile`.
- Named-entity substitution. `mq027` expects Emilio Cecchi as the person who first suggested Marguerite Louise's story, but the answer gives Harold Acton.
- Plausible but wrong interpretive expansion. `mq072` asks why Marguerite Louise is compared to a mosquito in Delogu's reading; the answer gives a generic disruptive-character interpretation instead of the expected "draw life from the writer" explanation.
- Late-source precision misses. `mq098` asks about Anne Louise at Montargis, but the answer shifts to Anna Ludovica and a broader femininity contrast.

This means `gpt-5.4-mini` ingestion is viable enough to answer many questions, but the first complete run does not prove it is reliable for chapter structure and fine-grained interpretive attribution.

## Model-Selection Implication

The current evidence favors `menotti-54-mini` as the default ingestion candidate for speed-sensitive local Cognee use. It is dramatically faster and already produces usable answers across a long corpus.

The open question is whether `menotti-55-low` materially improves the failure cases enough to justify a roughly 6.5x ingestion-time cost over `menotti-54-mini`. Since `menotti-55-low` has a complete raw answer run, the next useful step is to score `menotti-54-mini` and `menotti-55-low` side by side.

The current data does not justify `menotti-55-high` as a default. Its ingestion is much slower, and the query artifact is incomplete at 55/100 answers. It should be rerun or excluded from final selection until a complete answer set exists.

## Next Steps

1. Complete or rerun the `menotti-55-high` 100-question query.
2. Run the scoring phase from `artifacts/run_manetti_candidate_eval.py` once all desired raw answer files are complete.
3. Compare average score, low-score clusters, and failure modes for `menotti-54-mini` versus `menotti-55-low`.
4. Select the cheaper ingestion model unless the slower model clearly fixes structural and interpretive retrieval errors.

