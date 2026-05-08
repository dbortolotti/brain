# Prompt: Update Brain Model Registry

You are updating Brain’s model registry for the personal memory system.

Your task is to refresh `brain_model_registry.yaml` so it reflects the current best model choices, current model IDs, current pricing, provider availability, data/privacy posture, and suitability for Brain’s model-eval harness.

## Context

Brain is a personal memory application with these LLM roles:

- `router`
- `slack_intake`
- `memory_compiler`
- `validator_critic`
- `entity_resolution`
- `conflict_classifier`
- `recall_synthesizer`
- `debug_explainer`
- `eval_judge`
- `embeddings`

Brain’s philosophy:

```text
Strict on committing.
Helpful on repairing.
Explicit on success.
```

The registry should support evals that determine the cheapest model that saturates quality without corrupting long-term memory.

Zero-tolerance Brain failures:

```text
- silent overwrite of high-confidence facts
- entity over-merge
- unresolved pronoun committed as durable fact
- long source stored as one giant memory card
- large table atomized into memory cards by default
- malformed JSON that cannot be repaired
- deleted/superseded memory returned as current
```

## Hard constraints

1. Use only reputable model providers and model brands with servers/control plane outside China.

2. Do not include Chinese-linked model brands unless explicitly requested. Exclude or keep excluded:
   - DeepSeek
   - Qwen / Alibaba
   - Moonshot / Kimi
   - Zhipu / GLM / Z.ai
   - MiniMax

3. Use official provider sources only:
   - OpenAI official docs/pricing/model pages
   - Google Gemini official docs/pricing/model pages
   - Anthropic official docs/pricing/model pages
   - AWS Bedrock official model/pricing pages
   - Groq official model/pricing pages
   - Mistral official docs/pricing, or Mistral via Bedrock
   - Voyage official pricing/docs for embeddings
   - Cohere official docs/pricing if adding Cohere models

4. Do not rely on blog posts, Reddit, model leaderboards, or third-party price aggregators unless official sources are unavailable. If using non-official sources, mark them clearly as secondary.

5. Prefer stable production models. Preview/beta models may be included only with:
   - `preview: true`
   - `enabled_by_default: false`
   - a short reason why they are worth testing

6. Do not remove deprecated models silently. Move them to a `deprecated` or `excluded_for_now` section with:
   - date checked
   - reason
   - replacement recommendation

7. Keep model IDs exact and API-usable for the relevant provider.

8. Update pricing in USD per 1M tokens where available.

9. Include cached-input pricing, batch pricing, regional pricing, or long-context pricing when materially relevant.

10. Add a `last_checked` date and source URLs for every provider/model family.

## Current target providers

Review and update these providers:

```text
OpenAI
Google Gemini
Anthropic Claude
AWS Bedrock: Mistral
AWS Bedrock: NVIDIA Nemotron
Groq: Meta Llama / OpenAI open-weight models
Voyage embeddings
OpenAI embeddings
Optional: Cohere rerank/embedding/tool-use models
Optional: Mistral direct API
Optional: Azure OpenAI, if data residency or enterprise deployment is relevant
```

## Registry update tasks

### 1. Audit current model availability

For each provider:

- Check current model families.
- Check whether the model IDs in the registry still exist.
- Check whether newer replacements exist.
- Check whether any models are deprecated, renamed, region-limited, or preview-only.
- Check whether pricing changed.

For each model, record:

```yaml
id:
provider:
provider_brand:
roles:
enabled_by_default:
preview:
judge_only:
price_per_1m:
  input:
  cached_input:
  output:
  batch_input:
  batch_output:
context_window:
supports_structured_output:
supports_tool_calling:
supports_json_mode:
supports_batch:
supports_prompt_caching:
regions:
data_training_policy_summary:
last_checked:
source_urls:
expected_use:
notes:
```

Use `null` when a field is unavailable, but add a note explaining why.

### 2. Update role assignments

Assign models to Brain roles based on expected suitability.

Roles:

```yaml
router:
  Needs cheap classification and simple intent routing.

slack_intake:
  Needs reliable JSON, conservative decisions, repair options, and strong instruction following.

memory_compiler:
  Needs extraction of atomic durable memory cards from messy text, articles, summaries, transcripts.

validator_critic:
  Optional cheap LLM critic. Deterministic validator remains authoritative.

entity_resolution:
  Needs conservative entity matching. Prefer asking user over unsafe merge.

conflict_classifier:
  Needs duplicate/additive/supersedes/contradicts/correction classification.

recall_synthesizer:
  Needs grounded synthesis over retrieved Brain records.

debug_explainer:
  Needs explainability and good structured debugging output.

eval_judge:
  Offline judge only. Can be more expensive.

embeddings:
  Retrieval embedding candidates.
```

Do not assign expensive models as defaults unless there is a strong reason.

### 3. Update the core eval matrix

Maintain a concise `core_eval_matrix`.

The first-pass eval matrix should include:

```yaml
router:
  - cheapest viable router models

slack_intake:
  - strongest cheap default candidate
  - cheapest serious challenger
  - one controlled-infra challenger
  - one fast/cheap open-weight challenger

memory_compiler:
  - same structure as slack_intake

conflict_classifier:
  - stronger models only
  - include judge/escalation candidates

recall_synthesizer:
  - cheap/default candidates
  - one stronger challenger

eval_judge:
  - high-quality judge models only

embeddings:
  - cheap default
  - quality challenger
```

### 4. Update costs

For every model with pricing:

- Store `price_per_1m`.
- Also compute optional helper fields:

```yaml
price_per_token:
  input:
  cached_input:
  output:
```

Formula:

```text
price_per_token = price_per_1m / 1_000_000
```

For Brain eval cost estimates, also compute a sample cost for:

```text
short_ingestion:
  2,000 input tokens
  600 output tokens

long_source:
  20,000 input tokens
  2,000 output tokens

recall:
  4,000 input tokens
  800 output tokens
```

Add this under:

```yaml
estimated_brain_costs:
  short_ingestion:
  long_source:
  recall:
```

### 5. Data/privacy posture

For each provider, summarize official data handling:

```yaml
data_policy:
  api_data_used_for_training_by_default: true | false | unknown
  paid_tier_training_policy:
  free_tier_training_policy:
  regional_processing_available:
  notes:
  source_urls:
```

Important:

- Gemini free tier and paid tier may differ. Mark this clearly.
- AWS Bedrock has different data-control properties from direct provider APIs. Mark this clearly.
- OpenAI regional/data-residency endpoints may have pricing differences. Mark this clearly if relevant.
- Anthropic commercial/API training policy should be checked from official Anthropic sources.

### 6. Keep exclusions explicit

Maintain:

```yaml
excluded_for_now:
  chinese_linked_model_brands:
    reason:
    skip:
      - ...
  local_models:
    reason:
    skip:
      - ...
  other:
    - provider:
      reason:
```

Do not delete exclusions unless the user explicitly changes the selection policy.

### 7. Produce a changelog

At the top or bottom of the registry, add/update:

```yaml
changelog:
  - date:
    summary:
    added:
    removed:
    deprecated:
    price_changes:
    role_changes:
    notes:
```

### 8. Produce an implementation summary

After editing the registry, return a markdown summary with:

```text
1. Models added
2. Models removed/deprecated
3. Price changes
4. New recommended eval matrix
5. New recommended production defaults
6. Any uncertainty or source gaps
7. Follow-up actions
```

### 9. Recommended production defaults

After updating, recommend defaults for:

```yaml
production_defaults:
  router:
  slack_intake:
  memory_compiler:
  validator_critic:
  entity_resolution:
  conflict_classifier:
  recall_synthesizer:
  debug_explainer:
  eval_judge:
  embeddings:
```

Use this decision rule:

```text
Choose the cheapest model with zero zero-tolerance failures and no meaningful quality gap versus the next stronger model on Brain evals.
```

If eval results are unavailable, mark recommendation as provisional.

## Output requirements

Return:

1. The updated `brain_model_registry.yaml`.
2. A concise markdown summary of changes.
3. A list of official sources checked.
4. A list of uncertainties.
5. Suggested next eval command.

## Suggested eval command

Include an eval command like:

```bash
brain eval models \
  --registry brain_model_registry.yaml \
  --fixtures all \
  --roles router,slack_intake,memory_compiler,conflict_classifier,recall_synthesizer \
  --output eval_runs/$(date +%Y%m%d_%H%M%S).jsonl
```

## Important

Do not invent prices, model IDs, context windows, or data policies.

When uncertain, write:

```yaml
unknown
```

and explain what source was insufficient.
