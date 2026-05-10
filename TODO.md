# TODO

- Keep eval role prompts aligned with agent markdown docs, especially shared docs in `src/memory_stack/agents/shared/` and per-role definitions in `src/memory_stack/agents/roles/`. The prompt contract reads bounded shared sections plus the selected role markdown; when headings or role docs move, update the section mapping and related prompt-contract tests.
