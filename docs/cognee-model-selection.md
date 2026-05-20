# Cognee Model Selection

Ingestion timing for the Manetti document:

| Candidate dataset | Ingestion model setting | Add step | Cognee graph/cognify step | Total wall time | Peak RSS |
|---|---:|---:|---:|---:|---:|
| `menotti-54-mini` | `gpt-5.4-mini` | 0.56s | 40.615s | 43.31s | ~793 MiB |
| `menotti-55-low` | `gpt-5.5` low-effort run | 0.466s | 280.668s | 283.27s | ~1.07 GiB |
| `menotti-55-high` | `gpt-5.5` high-effort run | 0.461s | 882.753s | 885.39s | ~1.32 GiB |

The ingestion data strongly separates the candidates before answer quality is scored. The `gpt-5.4-mini` ingestion run completed in about 43 seconds. The `gpt-5.5` low-effort run took about 4.7 minutes, and the high-effort run took about 14.8 minutes. For this corpus, high effort is about 20x slower than `gpt-5.4-mini` ingestion.

This benchmark sits alongside the repository's durable model-evaluation fixtures under `tests/model_eval_tests/`, which stores durable model-evaluation fixtures larger than the normal unit-test fixtures. The fixture set is documented in `tests/model_eval_tests/README.md`, which describes the balanced Manetti question bank (`tests/model_eval_tests/manetti_100_questions.json` and `tests/model_eval_tests/manetti_100_questions.md`) generated from `manetti_document.md`, plus an organic recall fixture (`tests/model_eval_tests/organic_recall_100_cases.json`) with 47 service-layer seed inserts and 100 recall cases balanced across difficulties 1 through 5. The shared difficulty scale is: 1 direct single-fact recall; 2 direct recall with simple filtering, status, or source distractors; 3 multi-fact synthesis across two or more memories or sources; 4 precise filtering under distractors, status conflicts, or scoped exclusions; and 5 high-constraint synthesis across multiple domains with stale/deleted exclusions. The fixture integrity test `tests/model_eval_tests/test_fixture_integrity.py` checks the JSON fixture shapes and the copied Manetti materials. The live runner (`tests/model_eval_tests/run_model_eval.py`) creates a fresh dataset, ingests the full Manetti document followed by the ordered organic seed inserts, asks all 200 fixture questions, and scores every answer with a judge model. Each run writes a timestamped folder under `tests/model_eval_tests/runs/` with `config.json`, `ingestion_timings.json` and `ingestion_timings.jsonl`, `answers.jsonl`, `scores.jsonl`, `scores.csv`, and `report.md`.

Example:

```bash
uv run python tests/model_eval_tests/run_model_eval.py \
  --judge-model gpt-5.5 \
  --remember-model gpt-5.4-mini \
  --recall-model gpt-5.5
```

## Latest GPT-5.5 Retrieval Results

The latest retrieval run completed for all three candidate datasets using `gpt-5.5` as the `GRAPH_COMPLETION` retrieval / answer-synthesis model:

| Candidate dataset | Ingestion model setting | Retrieval / answer model for this run | Scoring judge | Raw answers | Avg score | Avg retrieval-stage time / question |
|---|---:|---:|---:|---:|---:|---:|
| `menotti-54-mini` | `gpt-5.4-mini` | `gpt-5.5` extra high | `gpt-5.5` extra high | 100/100 | 4.71 | 1.248s |
| `menotti-55-low` | `gpt-5.5` low-effort run | `gpt-5.5` extra high | `gpt-5.5` extra high | 100/100 | 4.69 | 1.151s |
| `menotti-55-high` | `gpt-5.5` high-effort run | `gpt-5.5` extra high | `gpt-5.5` extra high | 100/100 | 4.71 | 1.139s |

These are retrieval results for `gpt-5.5` answer synthesis, not final results for every possible retrieval model. This run holds retrieval/answer synthesis constant at `gpt-5.5` extra high. That means the current comparison is primarily testing how the different ingestion settings shape Cognee's stored graph/vector representation under a strong retrieval model. The matching `gpt-5.4-mini` retrieval run is recorded below, while keeping the scorer fixed at `gpt-5.5` extra high.

The completed run artifacts are written in the timestamped `tests/model_eval_tests/runs/` folders, alongside `config.json`, `ingestion_timings.json` and `ingestion_timings.jsonl`, `answers.jsonl`, `scores.jsonl`, `scores.csv`, and `report.md`.

## What We Are Testing

This test is a model-selection benchmark for local Cognee ingestion. The goal is to decide which model setting should be used to build a Cognee graph/vector dataset for a large scholarly source.

Each candidate dataset was built from the same source file, then queried with the same generated 100-question evaluation set. The candidate names are dataset names, not source names:

- `menotti-54-mini`: the source ingested with `gpt-5.4-mini`.
- `menotti-55-low`: the source ingested with `gpt-5.5` in the low-effort candidate run.
- `menotti-55-high`: the source ingested with `gpt-5.5` in the high-effort candidate run.

There are three separate model roles in this benchmark:

- Ingestion model: the model used during Cognee graph/cognify construction.
- Retrieval / answer model: the model used by `GRAPH_COMPLETION` when answering the 100 questions.
- Scoring judge: the model that grades candidate answers against the expected answers and corpus evidence.

All benchmark runs are scored by the same judge: `gpt-5.5` extra high. Completed retrieval runs include `gpt-5.5` extra high and `gpt-5.4-mini` as retrieval/answer models.

## Corpus

The test corpus is:

`/Volumes/xpg_usb4/sandbox/git/banti/md_sources/Secondary Sources/Manetti_DaUnPaeseLontano_Banti.pdf.md`

The artifact logs record it as a 489,900-byte markdown source with 66,726 words. The text contains Lucy Delogu's dissertation, 'Chi sono io? Narrazione storica e soggettività nella Camicia bruciata di Anna Banti', submitted to Rutgers. It analyzes Anna Banti, her historical fiction, feminism, female subjectivity, and especially `La camicia bruciata`.

This is a good stress test because it is long enough to require multi-hop retrieval and graph structure. The question set covers front-matter facts, chapter titles, named people, historical and literary relationships, interpretive claims, and fine distinctions between documented history and Banti's hypothetical reconstruction.

## Evaluation Method

The 100-question set was generated from the Manetti markdown source and saved here:

- `tests/model_eval_tests/manetti_100_questions.json`
- `tests/model_eval_tests/manetti_100_questions.md`
- `tests/model_eval_tests/manetti_document.md`

The repository's durable Manetti fixture is separate and balanced across difficulty levels:

- `tests/model_eval_tests/manetti_100_questions.json`
- `tests/model_eval_tests/manetti_100_questions.md`

The local copy of the Manetti source markdown used for the candidate evaluation is `tests/model_eval_tests/manetti_document.md`.

That fixture is generated from `tests/model_eval_tests/manetti_document.md` and contains 20 questions at each difficulty level from 1 through 5.

The repository also includes the organic recall fixture used by the live runner:

- `tests/model_eval_tests/organic_recall_100_cases.json`

That file contains 47 service-layer seed inserts and 100 recall cases, balanced across difficulties 1 through 5 with 20 cases per difficulty.

The recorded-run question distribution is:

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
- retrieval / answer model varies by run: `gpt-5.5` extra high for `20260513_141703`, and `gpt-5.4-mini` for `20260513_gpt54mini`
- the same 100 questions in the same order

The score table has one row per candidate/question with a 1-5 score. For comparability, every scored run in this series uses `gpt-5.5` extra high as the judge, even when the retrieval/answer model changes.

The repo's live runner follows the same separation of concerns: it creates a fresh dataset, ingests the full Manetti document, then ordered organic seed inserts, then asks all 200 fixture questions and scores every answer with a judge model.

## Average Score by Difficulty and Recall Model

This table groups the scored runs by question difficulty and recall / answer model, sorted by difficulty first. The three score columns are the ingestion-model candidate datasets. Each value is the average judge score on the 1-5 scale for that difficulty bucket.

| Difficulty / Recall model | Ingest `5.4-mini` | Ingest `5.5 low` | Ingest `5.5 high` |
|---|---:|---:|---:|
| 1 / `gpt-5.5` | 4.48 | 4.39 | 4.39 |
| 1 / `gpt-5.4-mini` | 4.00 | 4.13 | 3.87 |
| 2 / `gpt-5.5` | 4.85 | 4.88 | 4.93 |
| 2 / `gpt-5.4-mini` | 4.71 | 4.76 | 4.63 |
| 3 / `gpt-5.5` | 4.95 | 4.95 | 4.95 |
| 3 / `gpt-5.4-mini` | 4.85 | 4.95 | 4.75 |
| 4 / `gpt-5.5` | 4.14 | 4.14 | 4.14 |
| 4 / `gpt-5.4-mini` | 4.29 | 4.14 | 4.14 |
| 5 / `gpt-5.5` | 5.00 | 5.00 | 5.00 |
| 5 / `gpt-5.4-mini` | 5.00 | 5.00 | 5.00 |

## Average Time by Difficulty and Recall Model

This table uses the same grouping, but each cell reports `average time in; average time out`. `Time in` is the one-time ingestion/cognify wall time for the candidate dataset. `Time out` is the average Cognee retrieval-stage time for that difficulty and recall model, summing vector collection retrieval, ID-filtered graph retrieval, and graph projection. It does not include answer-synthesis LLM time or process overhead.

| Difficulty / Recall model | Ingest `5.4-mini` | Ingest `5.5 low` | Ingest `5.5 high` |
|---|---:|---:|---:|
| 1 / `gpt-5.5` | 43.31s in; 1.281s out | 283.27s in; 1.194s out | 885.39s in; 1.190s out |
| 1 / `gpt-5.4-mini` | 43.31s in; 1.180s out | 283.27s in; 1.202s out | 885.39s in; 1.150s out |
| 2 / `gpt-5.5` | 43.31s in; 1.114s out | 283.27s in; 1.121s out | 885.39s in; 1.114s out |
| 2 / `gpt-5.4-mini` | 43.31s in; 1.117s out | 283.27s in; 1.114s out | 885.39s in; 1.147s out |
| 3 / `gpt-5.5` | 43.31s in; 1.502s out | 283.27s in; 1.147s out | 885.39s in; 1.109s out |
| 3 / `gpt-5.4-mini` | 43.31s in; 1.115s out | 283.27s in; 1.129s out | 885.39s in; 1.130s out |
| 4 / `gpt-5.5` | 43.31s in; 1.173s out | 283.27s in; 1.116s out | 885.39s in; 1.126s out |
| 4 / `gpt-5.4-mini` | 43.31s in; 1.119s out | 283.27s in; 1.140s out | 885.39s in; 1.141s out |
| 5 / `gpt-5.5` | 43.31s in; 1.150s out | 283.27s in; 1.370s out | 885.39s in; 1.280s out |
| 5 / `gpt-5.4-mini` | 43.31s in; 1.170s out | 283.27s in; 1.260s out | 885.39s in; 1.210s out |

## Current Qualitative Read

In the `gpt-5.5` retrieval run, all three candidates returned an answer for every one of the 100 questions. A spot check shows they are strong on direct factual recall and many medium-depth interpretive questions, but that completed run still has several clear retrieval or graph confusions.

Good examples:

- `mq001` through `mq009`: correctly answers dissertation author, university, director, date, Banti's real name, dates, focus novel, publication year, and dedication.
- `mq013`: correctly identifies Hibbert's `The House of Medici` and Acton's `The Last Medici`.
- `mq032` through `mq050`: mostly handles the women's movement, fascism, Banti's historical interpretation, and 'black holes' of history.
- `mq093` and `mq094`: gives plausible high-level answers about historical truth and the historian/novelist distinction.

Observed failure modes:

- Chapter/title confusion. `mq010` asks for Delogu's Chapter One title, but all three candidates answer with a chapter title from `La camicia bruciata`. `mq012` asks for Delogu's Chapter Four title; `menotti-54-mini` answers with Chapter Three's topic, while the two `gpt-5.5` ingestion runs answer with `La tedeschina`.
- Theme overgeneralization. `mq021` asks for the central question 'Chi sono io?', but all three candidates generalize to the `questione femminile`.
- Named-entity substitution. `mq027` expects Emilio Cecchi as the person who first suggested Marguerite Louise's story. `menotti-54-mini` answers Harold Acton; both `gpt-5.5` ingestion runs answer Roberto Longhi.
- Plausible but wrong interpretive expansion. `mq072` asks why Marguerite Louise is compared to a mosquito in Delogu's reading; all three answers emphasize generic restlessness or irritation instead of the expected 'draw life from the writer' explanation.
- Late-source precision misses. `mq098` asks about Anne Louise at Montargis. `menotti-54-mini` shifts to Anna Ludovica, `menotti-55-low` gets closer by identifying Anne Louise's visit, and `menotti-55-high` shifts to Anna Maria Luisa de' Medici.

This means all three ingestion settings are viable enough to answer many questions under `gpt-5.5` extra-high retrieval, but that run does not show that higher-effort ingestion alone fixes chapter structure, named-entity attribution, or fine-grained interpretive retrieval.

## Question-by-Question GPT-5.5 Retrieval Scores and Timing

This table uses the completed `20260513_141703` run, where `gpt-5.5` was the retrieval / answer-synthesis model for every candidate dataset. `Scores` are `menotti-54-mini` / `menotti-55-low` / `menotti-55-high` on the 1-5 judge scale. `Retrieval s` is the Cognee logged retrieval-stage total per question, also in `54` / `55L` / `55H` order. It sums vector collection retrieval, ID-filtered graph retrieval, and graph projection. It does not include answer-synthesis LLM time or process overhead.

| Q | Difficulty | Question | Scores 54/55L/55H | Retrieval s 54/55L/55H |
|---:|---:|---|---:|---:|
| `mq001` | 1 | Who wrote the dissertation 'Chi sono io? Narrazione storica e soggettività nella Camicia bruciata di Anna Banti'? | 5/5/5 | 3.00/1.96/2.05 |
| `mq002` | 1 | At which university was the dissertation submitted? | 5/5/5 | 1.14/1.92/1.00 |
| `mq003` | 1 | Who directed the dissertation? | 5/5/5 | 1.09/0.98/1.07 |
| `mq004` | 1 | In what month and year was the dissertation completed? | 5/5/5 | 0.98/0.99/1.12 |
| `mq005` | 1 | What is Anna Banti’s real name according to the dissertation abstract? | 5/5/5 | 2.46/1.29/1.20 |
| `mq006` | 1 | What years of birth and death does the dissertation give for Anna Banti? | 5/5/5 | 1.31/1.25/1.34 |
| `mq007` | 1 | Which Anna Banti novel is the main focus of Delogu’s analysis? | 5/5/5 | 1.29/1.26/1.24 |
| `mq008` | 1 | In what year was La camicia bruciata published? | 5/5/5 | 1.18/1.10/1.11 |
| `mq009` | 1 | To whom is the dissertation dedicated? | 5/5/5 | 1.21/1.05/1.06 |
| `mq010` | 1 | What is the title of Chapter One? | 1/1/1 | 1.04/1.10/1.03 |
| `mq011` | 1 | What is the title of Chapter Two? | 5/5/5 | 1.19/1.14/1.19 |
| `mq012` | 1 | What is the title of Chapter Four? | 1/1/1 | 1.11/0.96/1.00 |
| `mq013` | 1 | Which two historical studies does Delogu compare with Banti’s La camicia bruciata in Chapter Four? | 5/5/5 | 1.00/0.93/0.87 |
| `mq014` | 1 | Which Banti novel is described in the abstract as the exception still in print? | 5/5/5 | 1.18/1.19/1.26 |
| `mq015` | 1 | What was the title of Banti’s first narrative work using the pseudonym Anna Banti? | 5/5/5 | 1.18/1.23/1.19 |
| `mq016` | 1 | What was Banti’s debut novel? | 5/5/5 | 1.22/1.13/1.26 |
| `mq017` | 1 | Which Banti novel made her famous according to Chapter One? | 5/5/5 | 1.05/1.01/1.03 |
| `mq018` | 1 | Who was Anna Banti’s husband? | 5/5/5 | 1.32/1.40/1.30 |
| `mq019` | 1 | What literary journal did Roberto Longhi found in 1950, with Banti as co-director of the literary series? | 5/5/5 | 1.19/1.28/1.26 |
| `mq020` | 1 | What is the name of Banti’s 1981 final novel? | 5/5/5 | 1.25/1.19/1.23 |
| `mq021` | 1 | Which question does Delogu identify as central to much of Banti’s work? | 2/2/2 | 1.22/1.12/1.10 |
| `mq022` | 1 | Which two Banti works did Cesare Garboli call masterpieces in the quoted passage? | 5/2/2 | 1.19/1.24/1.15 |
| `mq023` | 1 | Which Banti story did Garboli call perhaps the most beautiful story of the twentieth century? | 5/5/5 | 1.35/1.26/1.32 |
| `mq024` | 1 | Where and when was Anna Banti born, according to Chapter One? | 5/5/5 | 1.27/1.30/1.37 |
| `mq025` | 1 | Which faculty did Banti enroll in at Rome? | 5/5/5 | 1.21/1.15/1.17 |
| `mq026` | 1 | What early article by Banti was praised by Croce? | 4/4/4 | 1.22/1.13/1.17 |
| `mq027` | 1 | Who first suggested that Banti tell the story of Marguerite Louise, according to the dissertation? | 1/1/1 | 1.33/1.13/1.24 |
| `mq028` | 1 | Who was Marguerite Louise d’Orléans married to? | 5/5/5 | 1.05/1.13/1.13 |
| `mq029` | 1 | What are the names of Marguerite Louise and Cosimo III’s three children in the dissertation? | 5/5/5 | 1.10/1.05/1.11 |
| `mq030` | 1 | Which princess becomes central in the last two chapters of Banti’s La camicia bruciata? | 5/5/5 | 1.31/1.24/1.33 |
| `mq031` | 1 | What public role is given to Violante after Ferdinando’s death? | 5/5/5 | 1.07/0.89/0.98 |
| `mq032` | 2 | According to Delogu, what did the Italian women’s movement fight for in 1870-90? | 5/5/5 | 1.01/1.03/1.01 |
| `mq033` | 2 | Which two women are named as the most important socialist figures in the Italian women’s movement? | 5/5/5 | 1.00/0.98/1.07 |
| `mq034` | 2 | Who founded the Unione femminile nazionale in Milan in 1899? | 5/5/5 | 1.16/0.95/0.97 |
| `mq035` | 2 | What label for women’s domestic role does Delogu repeatedly cite as central to Italian patriarchal ideology? | 5/5/5 | 1.09/1.07/0.99 |
| `mq036` | 2 | Which positivist thinkers does Delogu cite as supporting women’s intellectual inferiority through biological arguments? | 5/5/5 | 1.06/1.13/1.21 |
| `mq037` | 2 | What did Giuseppe Antonio Borgese claim about women writers such as Neera, Deledda, and Serao? | 5/5/5 | 1.07/1.03/1.02 |
| `mq038` | 2 | According to Delogu, what legal dependence did married women face in liberal Italy? | 5/4/5 | 1.04/1.16/0.89 |
| `mq039` | 2 | What was the first Italian law regulating women’s and child labor mentioned by Delogu? | 5/5/5 | 0.89/1.08/1.14 |
| `mq040` | 2 | When did Italian women obtain the right to vote, according to the dissertation? | 5/5/5 | 1.01/0.89/1.07 |
| `mq041` | 2 | Which 1906 novel does Delogu call the first Italian feminist novel? | 5/5/5 | 1.15/1.04/1.10 |
| `mq042` | 2 | How does Delogu characterize fascism’s intended role for women? | 5/5/5 | 1.00/1.03/1.04 |
| `mq043` | 2 | What contradictory messages did fascism send to women, according to Delogu’s use of De Grazia? | 5/5/5 | 1.11/1.09/1.05 |
| `mq044` | 2 | How does Delogu describe Banti’s protagonists across her narrative works? | 4/5/5 | 1.26/1.26/1.23 |
| `mq045` | 2 | According to the dissertation, did Banti define herself as a feminist? | 5/5/5 | 1.29/1.27/1.16 |
| `mq046` | 2 | What two broad contributions does Delogu claim Banti made to Italian literature? | 5/5/5 | 1.07/1.21/1.10 |
| `mq047` | 2 | What does Banti call her historical writing in the quoted interview: ‘historical novel’ or ‘historical interpretation’? | 5/5/5 | 1.24/1.22/1.19 |
| `mq048` | 2 | What are the ‘black holes’ of history in Banti’s historical poetics? | 5/5/5 | 1.18/1.20/1.12 |
| `mq049` | 2 | What phrase does Banti use when urging Marguerite Louise to accept fictional reconstruction? | 5/5/5 | 1.22/1.09/1.11 |
| `mq050` | 2 | According to Delogu, why does Banti interpret rather than simply remember the past? | 5/5/5 | 1.28/1.31/1.27 |
| `mq051` | 2 | How does Delogu describe Banti’s autobiographical strategy? | 5/5/5 | 1.30/1.30/1.25 |
| `mq052` | 2 | What does Delogu say Chapter Three of the dissertation analyzes in La camicia bruciata? | 5/5/5 | 1.05/1.20/1.07 |
| `mq053` | 2 | What is Delogu’s stated purpose in comparing Banti’s fiction with Hibbert and Acton? | 5/5/5 | 1.10/1.02/1.01 |
| `mq054` | 2 | How does Delogu describe Banti’s relationship to neorealism? | 5/5/5 | 1.17/1.14/1.27 |
| `mq055` | 2 | Which kinds of women does Banti especially listen to, according to Chapter Two? | 4/3/5 | 1.07/1.27/1.18 |
| `mq056` | 2 | What sacrifice do many Banti heroines make in order to pursue their aims? | 5/5/5 | 1.11/1.25/1.16 |
| `mq057` | 2 | How does Delogu define Banti’s view of maternity? | 5/5/5 | 1.12/1.61/1.02 |
| `mq058` | 2 | What model of motherhood does Delogu say Banti creates in Artemisia? | 5/5/5 | 1.10/0.93/1.13 |
| `mq059` | 2 | Who is Porziella in relation to Artemisia? | 5/5/5 | 1.06/1.11/1.13 |
| `mq060` | 2 | How does Porziella differ from Artemisia in Delogu’s reading? | 5/5/5 | 1.18/1.16/1.18 |
| `mq061` | 2 | What female relationship does Delogu identify as essential for empowerment in Banti’s fiction? | 5/5/5 | 1.29/1.11/1.14 |
| `mq062` | 2 | What is Lavinia’s story preserved through in Lavinia fuggita? | 5/5/5 | 1.01/0.90/1.07 |
| `mq063` | 2 | How does Delogu say Banti represents marriage in many works? | 4/5/4 | 1.13/1.26/1.22 |
| `mq064` | 2 | Which three marriages are discussed in Allarme sul lago? | 5/5/5 | 1.08/1.04/1.05 |
| `mq065` | 2 | What did Banti say about being called ‘Anna Banti, wife of Roberto Longhi’? | 5/5/5 | 1.19/1.10/1.40 |
| `mq066` | 2 | How does Delogu qualify Banti’s feminism? | 5/5/5 | 1.10/1.03/0.96 |
| `mq067` | 2 | What was Banti’s reaction to militant feminism of the 1960s-70s, according to the dissertation? | 5/5/5 | 0.87/1.02/1.02 |
| `mq068` | 2 | Which Banti essays does Delogu identify as more directly concerned with concrete equality for women? | 5/5/5 | 1.02/0.91/0.86 |
| `mq069` | 2 | How is La camicia bruciata structured? | 5/5/5 | 1.12/1.11/1.17 |
| `mq070` | 2 | What are the five chapter titles of La camicia bruciata listed by Delogu? | 5/5/5 | 0.97/1.08/1.17 |
| `mq071` | 2 | What animal image does Banti use when Marguerite Louise first appears in La camicia bruciata? | 5/5/5 | 1.35/1.36/1.27 |
| `mq072` | 2 | Why is Marguerite Louise compared to a mosquito in Delogu’s reading? | 2/3/3 | 1.15/1.01/1.21 |
| `mq073` | 3 | What role does the narrator play in relation to Marguerite Louise in La camicia bruciata? | 5/5/5 | 1.16/1.22/1.24 |
| `mq074` | 3 | How does the narrator’s relationship with Marguerite Louise differ from her relationship with Artemisia? | 5/5/5 | 1.09/1.16/1.28 |
| `mq075` | 3 | What does Delogu identify as the main reason Marguerite Louise interests Banti? | 4/4/4 | 1.19/1.27/1.21 |
| `mq076` | 3 | How does Delogu characterize Marguerite Louise as a literary character? | 5/5/5 | 1.31/1.17/1.12 |
| `mq077` | 3 | What does Marguerite Louise want most as a young girl at Blois? | 5/5/5 | 1.12/1.01/1.09 |
| `mq078` | 3 | How does Delogu explain Marguerite Louise’s repeated question ‘Who is Marguerite Louise?’ | 5/5/5 | 1.25/1.26/1.24 |
| `mq079` | 3 | How does Cosimo III appear in the dissertation’s reading of Banti’s novel? | 5/5/5 | 1.20/1.21/1.25 |
| `mq080` | 3 | What role does Cosimo’s mother play in his development, according to Delogu? | 5/5/5 | 1.34/1.18/1.17 |
| `mq081` | 3 | How is Ferdinando similar to Marguerite Louise in Banti’s novel? | 5/5/5 | 1.37/1.10/1.09 |
| `mq082` | 3 | How does Delogu characterize Gian Gastone? | 5/5/5 | 1.18/1.20/1.18 |
| `mq083` | 3 | What kind of relationship develops between Violante and Gian Gastone? | 5/5/5 | 0.99/1.08/1.14 |
| `mq084` | 3 | How does Anna Ludovica differ from Marguerite Louise? | 5/5/5 | 1.08/1.10/1.02 |
| `mq085` | 3 | How does Banti portray Violante in contrast to Marguerite Louise? | 5/5/5 | 1.11/1.04/1.14 |
| `mq086` | 3 | Why does Violante’s appointment as Governor of Siena matter in Delogu’s interpretation? | 5/5/5 | 8.25/1.08/0.95 |
| `mq087` | 3 | What does Delogu mean by saying Marguerite Louise and Violante live in a ‘golden cage’? | 5/5/5 | 1.18/1.15/1.11 |
| `mq088` | 3 | What does the chapter title ‘Voi fate la mia infelicità e io la vostra’ express? | 5/5/5 | 1.02/0.94/0.91 |
| `mq089` | 3 | Why does Delogu say Marguerite Louise’s refusal to abandon French identity undermines her marriage? | 5/5/5 | 1.09/1.66/1.07 |
| `mq090` | 3 | How do lower-class women in Florence respond to Marguerite Louise’s departure, according to Banti as read by Delogu? | 5/5/5 | 0.99/1.03/0.92 |
| `mq091` | 3 | How does Delogu interpret Marguerite Louise’s motherhood? | 5/5/5 | 1.12/1.03/0.98 |
| `mq092` | 3 | What contrast does Delogu draw between Marguerite Louise and Violante as wives? | 5/5/5 | 1.01/1.04/1.06 |
| `mq093` | 4 | What is the dissertation’s central claim about historical truth in La camicia bruciata? | 5/5/5 | 0.99/1.11/1.06 |
| `mq094` | 4 | What distinction does Delogu draw between the historian and the novelist in the conclusion to Chapter Four? | 5/5/5 | 1.14/1.00/0.98 |
| `mq095` | 4 | What fundamental historical facts about Marguerite Louise does Delogu say Banti does not alter? | 3/3/3 | 1.19/1.23/1.20 |
| `mq096` | 4 | What invented episode gives La camicia bruciata its title? | 5/4/5 | 1.08/1.05/1.14 |
| `mq097` | 4 | How does Delogu interpret the burning of the wedding nightgown? | 5/5/5 | 1.36/1.14/1.09 |
| `mq098` | 4 | What historical episode involving Anne Louise does Banti expand into a psychological scene between two models of femininity? | 1/2/1 | 1.27/1.29/1.24 |
| `mq099` | 4 | How does Delogu say Banti alters Marguerite Louise’s life in France compared with Hibbert and Acton? | 5/5/5 | 1.18/0.99/1.17 |
| `mq100` | 5 | What larger autobiographical hypothesis does Delogu propose about Banti’s use of Marguerite Louise, Violante, and other heroines? | 5/5/5 | 1.15/1.37/1.28 |

Stage timing detail is available from the stderr artifacts. Aggregate retrieval-stage averages per question were: `menotti-54-mini` 1.248s, `menotti-55-low` 1.151s, and `menotti-55-high` 1.139s.

## GPT-5.4-Mini Retrieval Results

The `20260513_gpt54mini` retrieval run completed for all three candidate datasets using `gpt-5.4-mini` as the `GRAPH_COMPLETION` retrieval / answer-synthesis model. The scoring judge stayed fixed at `gpt-5.5` extra high.

| Candidate dataset | Ingestion model setting | Retrieval / answer model for this run | Scoring judge | Raw answers | Avg score | Avg retrieval-stage time / question |
|---|---|---|---|---:|---:|---:|
| `menotti-54-mini` | `gpt-5.4-mini` | `gpt-5.4-mini` | `gpt-5.5` extra high | 100/100 | 4.49 | 1.137s |
| `menotti-55-low` | `gpt-5.5` low-effort run | `gpt-5.4-mini` | `gpt-5.5` extra high | 100/100 | 4.56 | 1.148s |
| `menotti-55-high` | `gpt-5.5` high-effort run | `gpt-5.4-mini` | `gpt-5.5` extra high | 100/100 | 4.39 | 1.145s |

Compared with the `gpt-5.5` retrieval run, answer quality dropped for all three candidate datasets: `menotti-54-mini` fell from 4.71 to 4.49, `menotti-55-low` from 4.69 to 4.56, and `menotti-55-high` from 4.71 to 4.39. The logged retrieval-stage timings stayed near the earlier run because they measure Cognee vector/graph retrieval, not answer-synthesis LLM latency. End-to-end query batch wall times were 355.2s for `menotti-54-mini`, 370.7s for `menotti-55-low`, and 366.2s for `menotti-55-high`.

The completed run artifacts are written in the timestamped `tests/model_eval_tests/runs/` folders, alongside `config.json`, `ingestion_timings.json` and `ingestion_timings.jsonl`, `answers.jsonl`, `scores.jsonl`, `scores.csv`, and `report.md`.

## Question-by-Question GPT-5.4-Mini Retrieval Scores and Timing

This table uses the completed `20260513_gpt54mini` run, where `gpt-5.4-mini` was the retrieval / answer-synthesis model for every candidate dataset. `Scores` are `menotti-54-mini` / `menotti-55-low` / `menotti-55-high` on the 1-5 judge scale. `Retrieval s` is the Cognee logged retrieval-stage total per question, also in `54` / `55L` / `55H` order. It sums vector collection retrieval, ID-filtered graph retrieval, and graph projection. It does not include answer-synthesis LLM time or process overhead.

| Q | Difficulty | Question | Scores 54/55L/55H | Retrieval s 54/55L/55H |
|---:|---:|---|---:|---:|
| `mq001` | 1 | Who wrote the dissertation 'Chi sono io? Narrazione storica e soggettività nella Camicia bruciata di Anna Banti'? | 5/5/5 | 1.21/2.09/1.34 |
| `mq002` | 1 | At which university was the dissertation submitted? | 5/5/5 | 0.98/1.48/0.98 |
| `mq003` | 1 | Who directed the dissertation? | 5/5/5 | 2.18/0.99/1.01 |
| `mq004` | 1 | In what month and year was the dissertation completed? | 5/5/5 | 0.92/0.96/1.04 |
| `mq005` | 1 | What is Anna Banti’s real name according to the dissertation abstract? | 5/5/5 | 1.19/1.23/1.40 |
| `mq006` | 1 | What years of birth and death does the dissertation give for Anna Banti? | 5/5/5 | 1.25/1.28/1.23 |
| `mq007` | 1 | Which Anna Banti novel is the main focus of Delogu’s analysis? | 5/5/5 | 1.19/1.34/1.17 |
| `mq008` | 1 | In what year was La camicia bruciata published? | 5/5/5 | 1.07/1.04/1.11 |
| `mq009` | 1 | To whom is the dissertation dedicated? | 4/5/4 | 1.13/1.10/1.08 |
| `mq010` | 1 | What is the title of Chapter One? | 1/1/1 | 0.98/1.00/1.07 |
| `mq011` | 1 | What is the title of Chapter Two? | 1/1/1 | 1.09/1.09/1.10 |
| `mq012` | 1 | What is the title of Chapter Four? | 1/1/1 | 1.00/1.03/0.95 |
| `mq013` | 1 | Which two historical studies does Delogu compare with Banti’s La camicia bruciata in Chapter Four? | 5/5/5 | 0.91/0.91/0.87 |
| `mq014` | 1 | Which Banti novel is described in the abstract as the exception still in print? | 5/5/5 | 1.20/1.22/1.23 |
| `mq015` | 1 | What was the title of Banti’s first narrative work using the pseudonym Anna Banti? | 5/5/5 | 1.18/1.19/1.25 |
| `mq016` | 1 | What was Banti’s debut novel? | 5/5/5 | 1.25/1.22/1.24 |
| `mq017` | 1 | Which Banti novel made her famous according to Chapter One? | 5/5/5 | 1.04/1.14/1.06 |
| `mq018` | 1 | Who was Anna Banti’s husband? | 5/5/5 | 1.32/1.17/1.22 |
| `mq019` | 1 | What literary journal did Roberto Longhi found in 1950, with Banti as co-director of the literary series? | 5/5/5 | 1.22/1.28/1.24 |
| `mq020` | 1 | What is the name of Banti’s 1981 final novel? | 5/5/5 | 1.21/1.22/1.16 |
| `mq021` | 1 | Which question does Delogu identify as central to much of Banti’s work? | 2/5/1 | 1.20/1.22/1.18 |
| `mq022` | 1 | Which two Banti works did Cesare Garboli call masterpieces in the quoted passage? | 2/2/2 | 1.18/1.30/1.15 |
| `mq023` | 1 | Which Banti story did Garboli call perhaps the most beautiful story of the twentieth century? | 1/1/1 | 1.32/1.34/1.24 |
| `mq024` | 1 | Where and when was Anna Banti born, according to Chapter One? | 5/5/5 | 1.33/1.24/1.33 |
| `mq025` | 1 | Which faculty did Banti enroll in at Rome? | 5/5/5 | 1.20/1.19/1.19 |
| `mq026` | 1 | What early article by Banti was praised by Croce? | 1/1/1 | 1.17/1.22/1.20 |
| `mq027` | 1 | Who first suggested that Banti tell the story of Marguerite Louise, according to the dissertation? | 1/1/1 | 1.25/1.29/1.18 |
| `mq028` | 1 | Who was Marguerite Louise d’Orléans married to? | 5/5/5 | 1.08/1.17/1.10 |
| `mq029` | 1 | What are the names of Marguerite Louise and Cosimo III’s three children in the dissertation? | 5/5/5 | 1.08/0.98/1.04 |
| `mq030` | 1 | Which princess becomes central in the last two chapters of Banti’s La camicia bruciata? | 5/5/2 | 1.27/1.24/1.27 |
| `mq031` | 1 | What public role is given to Violante after Ferdinando’s death? | 5/5/5 | 0.98/1.09/1.02 |
| `mq032` | 2 | According to Delogu, what did the Italian women’s movement fight for in 1870-90? | 5/5/5 | 0.93/1.11/0.96 |
| `mq033` | 2 | Which two women are named as the most important socialist figures in the Italian women’s movement? | 5/5/5 | 1.08/0.97/0.96 |
| `mq034` | 2 | Who founded the Unione femminile nazionale in Milan in 1899? | 5/5/5 | 1.12/0.94/1.13 |
| `mq035` | 2 | What label for women’s domestic role does Delogu repeatedly cite as central to Italian patriarchal ideology? | 3/3/3 | 0.97/1.11/1.10 |
| `mq036` | 2 | Which positivist thinkers does Delogu cite as supporting women’s intellectual inferiority through biological arguments? | 5/5/4 | 1.27/1.09/1.11 |
| `mq037` | 2 | What did Giuseppe Antonio Borgese claim about women writers such as Neera, Deledda, and Serao? | 5/5/5 | 1.04/0.98/1.00 |
| `mq038` | 2 | According to Delogu, what legal dependence did married women face in liberal Italy? | 4/5/5 | 0.94/1.00/1.64 |
| `mq039` | 2 | What was the first Italian law regulating women’s and child labor mentioned by Delogu? | 5/5/5 | 0.99/1.04/1.01 |
| `mq040` | 2 | When did Italian women obtain the right to vote, according to the dissertation? | 5/5/5 | 1.04/0.90/1.03 |
| `mq041` | 2 | Which 1906 novel does Delogu call the first Italian feminist novel? | 5/5/5 | 1.04/1.11/1.11 |
| `mq042` | 2 | How does Delogu characterize fascism’s intended role for women? | 5/5/5 | 1.03/1.12/0.97 |
| `mq043` | 2 | What contradictory messages did fascism send to women, according to Delogu’s use of De Grazia? | 5/5/5 | 1.00/1.01/1.00 |
| `mq044` | 2 | How does Delogu describe Banti’s protagonists across her narrative works? | 4/4/4 | 1.32/1.32/1.27 |
| `mq045` | 2 | According to the dissertation, did Banti define herself as a feminist? | 5/5/5 | 1.22/1.31/1.24 |
| `mq046` | 2 | What two broad contributions does Delogu claim Banti made to Italian literature? | 5/5/5 | 0.99/1.04/1.10 |
| `mq047` | 2 | What does Banti call her historical writing in the quoted interview: ‘historical novel’ or ‘historical interpretation’? | 5/5/5 | 1.17/1.17/1.13 |
| `mq048` | 2 | What are the ‘black holes’ of history in Banti’s historical poetics? | 5/4/5 | 1.44/1.23/1.20 |
| `mq049` | 2 | What phrase does Banti use when urging Marguerite Louise to accept fictional reconstruction? | 5/5/5 | 1.13/1.24/1.17 |
| `mq050` | 2 | According to Delogu, why does Banti interpret rather than simply remember the past? | 5/5/4 | 1.21/1.31/1.29 |
| `mq051` | 2 | How does Delogu describe Banti’s autobiographical strategy? | 5/5/5 | 1.33/1.28/1.29 |
| `mq052` | 2 | What does Delogu say Chapter Three of the dissertation analyzes in La camicia bruciata? | 5/5/5 | 1.11/1.02/1.10 |
| `mq053` | 2 | What is Delogu’s stated purpose in comparing Banti’s fiction with Hibbert and Acton? | 4/5/4 | 1.10/1.17/1.01 |
| `mq054` | 2 | How does Delogu describe Banti’s relationship to neorealism? | 5/5/5 | 1.08/1.16/1.18 |
| `mq055` | 2 | Which kinds of women does Banti especially listen to, according to Chapter Two? | 3/2/2 | 1.08/1.28/1.20 |
| `mq056` | 2 | What sacrifice do many Banti heroines make in order to pursue their aims? | 5/5/5 | 1.06/1.05/1.13 |
| `mq057` | 2 | How does Delogu define Banti’s view of maternity? | 5/5/5 | 1.07/0.97/0.98 |
| `mq058` | 2 | What model of motherhood does Delogu say Banti creates in Artemisia? | 4/5/4 | 1.00/1.13/1.13 |
| `mq059` | 2 | Who is Porziella in relation to Artemisia? | 5/5/5 | 1.03/1.02/1.13 |
| `mq060` | 2 | How does Porziella differ from Artemisia in Delogu’s reading? | 5/5/5 | 1.20/1.12/1.17 |
| `mq061` | 2 | What female relationship does Delogu identify as essential for empowerment in Banti’s fiction? | 5/5/5 | 1.14/1.23/1.12 |
| `mq062` | 2 | What is Lavinia’s story preserved through in Lavinia fuggita? | 5/5/5 | 0.96/1.07/1.08 |
| `mq063` | 2 | How does Delogu say Banti represents marriage in many works? | 4/5/4 | 1.23/1.20/1.42 |
| `mq064` | 2 | Which three marriages are discussed in Allarme sul lago? | 5/5/3 | 1.05/1.00/1.01 |
| `mq065` | 2 | What did Banti say about being called ‘Anna Banti, wife of Roberto Longhi’? | 5/5/5 | 1.28/1.40/1.19 |
| `mq066` | 2 | How does Delogu qualify Banti’s feminism? | 5/5/5 | 0.99/1.09/1.69 |
| `mq067` | 2 | What was Banti’s reaction to militant feminism of the 1960s-70s, according to the dissertation? | 5/5/5 | 1.04/0.92/1.01 |
| `mq068` | 2 | Which Banti essays does Delogu identify as more directly concerned with concrete equality for women? | 5/5/5 | 1.12/1.05/1.02 |
| `mq069` | 2 | How is La camicia bruciata structured? | 5/5/5 | 1.12/1.09/1.19 |
| `mq070` | 2 | What are the five chapter titles of La camicia bruciata listed by Delogu? | 5/5/5 | 1.16/0.94/1.03 |
| `mq071` | 2 | What animal image does Banti use when Marguerite Louise first appears in La camicia bruciata? | 5/5/5 | 1.46/1.29/1.40 |
| `mq072` | 2 | Why is Marguerite Louise compared to a mosquito in Delogu’s reading? | 2/2/3 | 1.27/1.21/1.11 |
| `mq073` | 3 | What role does the narrator play in relation to Marguerite Louise in La camicia bruciata? | 5/5/4 | 1.09/1.26/1.19 |
| `mq074` | 3 | How does the narrator’s relationship with Marguerite Louise differ from her relationship with Artemisia? | 5/5/5 | 1.16/1.19/1.21 |
| `mq075` | 3 | What does Delogu identify as the main reason Marguerite Louise interests Banti? | 4/4/4 | 1.29/1.25/1.30 |
| `mq076` | 3 | How does Delogu characterize Marguerite Louise as a literary character? | 5/5/4 | 1.24/1.18/1.24 |
| `mq077` | 3 | What does Marguerite Louise want most as a young girl at Blois? | 5/5/5 | 1.22/1.15/0.98 |
| `mq078` | 3 | How does Delogu explain Marguerite Louise’s repeated question ‘Who is Marguerite Louise?’ | 5/5/5 | 1.25/1.26/1.31 |
| `mq079` | 3 | How does Cosimo III appear in the dissertation’s reading of Banti’s novel? | 5/5/5 | 1.24/1.23/1.21 |
| `mq080` | 3 | What role does Cosimo’s mother play in his development, according to Delogu? | 5/5/5 | 1.17/1.16/1.20 |
| `mq081` | 3 | How is Ferdinando similar to Marguerite Louise in Banti’s novel? | 4/5/5 | 1.10/1.10/1.04 |
| `mq082` | 3 | How does Delogu characterize Gian Gastone? | 5/5/5 | 1.07/1.16/1.10 |
| `mq083` | 3 | What kind of relationship develops between Violante and Gian Gastone? | 5/5/5 | 1.00/1.11/1.11 |
| `mq084` | 3 | How does Anna Ludovica differ from Marguerite Louise? | 5/5/5 | 1.14/1.15/1.12 |
| `mq085` | 3 | How does Banti portray Violante in contrast to Marguerite Louise? | 5/5/5 | 1.10/1.08/1.24 |
| `mq086` | 3 | Why does Violante’s appointment as Governor of Siena matter in Delogu’s interpretation? | 5/5/5 | 0.91/0.95/0.96 |
| `mq087` | 3 | What does Delogu mean by saying Marguerite Louise and Violante live in a ‘golden cage’? | 4/5/4 | 1.16/1.24/1.15 |
| `mq088` | 3 | What does the chapter title ‘Voi fate la mia infelicità e io la vostra’ express? | 5/5/5 | 1.01/0.92/1.08 |
| `mq089` | 3 | Why does Delogu say Marguerite Louise’s refusal to abandon French identity undermines her marriage? | 5/5/4 | 0.94/0.99/0.96 |
| `mq090` | 3 | How do lower-class women in Florence respond to Marguerite Louise’s departure, according to Banti as read by Delogu? | 5/5/5 | 0.95/1.04/1.06 |
| `mq091` | 3 | How does Delogu interpret Marguerite Louise’s motherhood? | 5/5/5 | 1.18/1.12/1.15 |
| `mq092` | 3 | What contrast does Delogu draw between Marguerite Louise and Violante as wives? | 5/5/5 | 1.08/1.04/0.99 |
| `mq093` | 4 | What is the dissertation’s central claim about historical truth in La camicia bruciata? | 5/5/5 | 1.00/1.09/0.97 |
| `mq094` | 4 | What distinction does Delogu draw between the historian and the novelist in the conclusion to Chapter Four? | 5/5/5 | 1.12/1.15/1.06 |
| `mq095` | 4 | What fundamental historical facts about Marguerite Louise does Delogu say Banti does not alter? | 4/3/3 | 1.22/1.17/1.15 |
| `mq096` | 4 | What invented episode gives La camicia bruciata its title? | 5/5/5 | 1.04/1.05/1.02 |
| `mq097` | 4 | How does Delogu interpret the burning of the wedding nightgown? | 5/5/5 | 1.12/1.14/1.34 |
| `mq098` | 4 | What historical episode involving Anne Louise does Banti expand into a psychological scene between two models of femininity? | 1/1/1 | 1.23/1.25/1.31 |
| `mq099` | 4 | How does Delogu say Banti alters Marguerite Louise’s life in France compared with Hibbert and Acton? | 5/5/5 | 1.10/1.13/1.14 |
| `mq100` | 5 | What larger autobiographical hypothesis does Delogu propose about Banti’s use of Marguerite Louise, Violante, and other heroines? | 5/5/5 | 1.17/1.26/1.21 |

Stage timing detail is available from the stderr artifacts. Aggregate retrieval-stage averages per question were: `menotti-54-mini` 1.137s, `menotti-55-low` 1.148s, and `menotti-55-high` 1.145s.

## Model-Selection Implication

The two completed retrieval runs point in the same practical direction: high-effort ingestion is not earning its cost. With `gpt-5.5` retrieval, `menotti-54-mini` and `menotti-55-high` tied at 4.71 while `menotti-55-low` scored 4.69. With `gpt-5.4-mini` retrieval, `menotti-55-low` led at 4.56, followed by `menotti-54-mini` at 4.49 and `menotti-55-high` at 4.39.

The current evidence still favors `menotti-54-mini` as the default ingestion candidate for speed-sensitive local Cognee use. It is dramatically faster to ingest and remains competitive across both retrieval models. The `menotti-55-low` ingestion run is the only slower candidate with a small quality edge under `gpt-5.4-mini` retrieval, but that edge is 0.07 average score points against a roughly 6.5x ingestion-time cost.

The current data does not justify `menotti-55-high` as a default. Its ingestion is much slower, it does not improve the shared structural and attribution failure modes, and it was the weakest candidate when retrieval/answer synthesis used `gpt-5.4-mini`.

## Next Steps

1. If you run another retrieval comparison, keep the same 100-question set and the same judge model so low-score clusters stay comparable.
2. Compare low-score clusters across the completed `gpt-5.5` and `gpt-5.4-mini` retrieval runs.
3. Select the cheaper ingestion and retrieval combination unless the slower model clearly fixes structural and interpretive retrieval errors.

<!-- brain-doc-source-hash: 758e9a7659a728b335a2960dbae4666dd023ea8fe843702d403306389a344ae0 -->
