# Embedding Model Ratings

Ratings are for Brain's memory/retrieval use case, not a universal embedding leaderboard. They weight public quality evidence, cost, current Brain wiring, operational risk, and whether the model is practical to run locally or in production.

Brain's current embedding eval is still only a smoke/vector-shape check. It does not yet measure retrieval quality, so these ratings should be treated as candidate prioritization until a real Brain retrieval eval is added.

| Model | Price / 1M Input | Rating | Notes |
|---|---:|---:|---|
| `local:qwen3-embedding-8b` | local compute | 4.7/5 quality, 2.8/5 Brain fit | Public multilingual benchmark is top-tier, but too heavy for the current 16 GB Mac unless quantized and served through a local endpoint. Not wired yet. |
| `local:qwen3-embedding-4b` | local compute | 4.5/5 quality, 3.2/5 Brain fit | Best realistic top-tier local challenger. Still needs local serving integration. |
| `google:gemini-embedding-001` | $0.15 | 4.5/5 | Strong Google multilingual/text candidate; already close to wired. |
| `voyage:voyage-4-large` | $0.12 | 4.4/5 | Strong retrieval candidate; wired cloud path. |
| `voyage:voyage-4` | $0.06 | 4.1/5 | Good cost/quality middle option. |
| `voyage:voyage-4-lite` | $0.02 | 4.0/5 | Best cheap cloud candidate. |
| `fastembed:intfloat/multilingual-e5-large` | local compute | 3.8/5 | Best easy local multilingual candidate. Registered as the local default; requires reindex before use with existing vectors. |
| `openai:text-embedding-3-large` | $0.13 | 3.7/5 | Solid baseline, but not top multilingual and prod lacks an OpenAI embedding key. |
| `google:gemini-embedding-2` | $0.20 | 3.5/5 | Interesting multimodal option, less compelling for text-only memory. |
| `google-vertex:multilingual-e5-large` | $0.025 cloud | 3.3/5 | Same underlying E5 family as local option, but Vertex requires Model Garden/endpoint wiring. |
| `fastembed:jinaai/jina-embeddings-v3` | local compute | 3.2/5 | Good multilingual local model, but license is `cc-by-nc-4.0`, so risky for production/commercial use. |
| `openai:text-embedding-3-small` | $0.02 | 3.2/5 | Cheap baseline, not top multilingual. |
| `google-vertex:text-multilingual-embedding-002` | ~$0.10 | 3.0/5 | Older Vertex multilingual model; likely superseded by Gemini 001. |
| `fastembed:sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | local compute | 2.9/5 | Easy local multilingual fallback, older and weaker. |
| `google-vertex:multilingual-e5-small` | $0.015 cloud | 2.7/5 | Cheap but lower quality ceiling. |
| `fastembed:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | local compute | 2.5/5 | Very easy/cheap local fallback, not a serious quality contender. |
| `google-vertex:text-embedding-005` | ~$0.10 | 2.4/5 | English/code oriented, not the multilingual target. |
| `google-vertex:multimodalembedding` | ~$0.80 | 1.8/5 | Expensive legacy multimodal reference. |

## Recommended Shortlist

1. `google:gemini-embedding-001` for best Google-backed multilingual quality.
2. `voyage:voyage-4-lite` for a cheap production candidate using credentials already available in prod.
3. `voyage:voyage-4-large` for a high-quality retrieval candidate.
4. `fastembed:intfloat/multilingual-e5-large` for the easiest local multilingual fallback.
5. `local:qwen3-embedding-4b` for a serious local top-tier challenger once local serving is wired.

## Highest-Confidence Issues

| Issue | Confidence | Impact | Next Action |
|---|---:|---|---|
| Brain's current embedding eval is not a retrieval-quality eval. | High | The existing `1.000` scores only prove vector generation, not better recall. | Add a real retrieval eval with fixed corpus, gold queries, recall@k, MRR, nDCG, and answer correctness. |
| Current prod embedding default is `openai:text-embedding-3-small`, but prod OpenAI API key has been intentionally blanked. | High | OpenAI text can use OAuth, but OpenAI embeddings still require `OPENAI_API_KEY`; active prod smoke currently cannot validate OpenAI embeddings without a key. | Either restore a scoped OpenAI embedding key or move prod embeddings to a provider with configured credentials, such as Voyage or Google. |
| Profile validation currently couples `PROFILE=openai` to `EMBEDDING_PROVIDER=openai`. | High | This blocks practical mixes like OpenAI LLM plus Gemini/Voyage embeddings even though LLM and embeddings do not need the same provider. | Decouple LLM profile validation from embedding provider validation, while keeping no-cloud-key protections for `PROFILE=local`. |
| Vertex and local E5 should be represented as different provider paths. | High | `google-vertex:multilingual-e5-large` means managed Vertex/Model Garden; local E5 should be `fastembed:intfloat/multilingual-e5-large` or another local provider ref. | Add local E5 as its own registry candidate and keep Vertex E5 marked as managed endpoint work. |
| Any embedding dimension change requires a vector-store rebuild. | High | Switching between OpenAI small, Gemini 001, E5, or Qwen changes vector dimensions unless explicitly projected. Mixed old/new dimensions will break retrieval. | Require explicit reindex/rebuild plan before changing prod embedding model. |
| `google-vertex:*` embeddings are registry inventory, not runnable Brain candidates yet. | High | Smoke/eval clients do not currently call Vertex embedding endpoints, and Vertex auth/project/location are not exported or validated. | Add Vertex settings, auth validation, live smoke, eval client support, and endpoint-specific handling. |
| `fastembed:intfloat/multilingual-e5-large` is the lowest-effort local multilingual candidate. | High | It is supported by installed `fastembed` and is now represented as the local default candidate. | Reindex before using it with existing memory vectors, and use the local smoke/eval path to validate vector generation. |
| Qwen3 local embeddings are high-quality candidates but not a config-only change. | Medium-high | They need a serving layer and probably query/document instruction handling before they can be fairly evaluated in Brain. | Treat Qwen3 as a separate local-serving integration after the simpler FastEmbed path is evaluated. |

## Next Eval Work

A useful Brain retrieval eval should re-embed the same fixed memory corpus per model, run gold queries, and score recall@k, MRR, nDCG, and final answer correctness. The existing embedding smoke fixtures are not enough to distinguish model quality.
