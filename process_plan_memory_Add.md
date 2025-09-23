### Action plan to attach a guidance prompt at the start of each conversation

- **Assess current flow**
  - Review `bot/memory.py`, `bot/chain.py`, and `app.py` to confirm how messages are constructed and where memory is initialized/loaded.

- **Define insertion strategy**
  - Use a single top-of-thread system message that is always the first entry in memory.
  - Ensure it is added exactly once per session/thread, not per turn.

- **Author the system prompt template**
  - Sections: response style/tone, scope/context, constraints/guardrails, formatting rules, refusal criteria, citation expectations, and language policy.
  - Parameterize with variables: `{project_name}`, `{data_scope}`, `{current_date}`, `{max_tokens}`, `{response_language}`.

- **Choose storage and configurability**
  - Store prompt in a file (e.g., `bot/system_prompt.md`) for easy edits.
  - Add env/CLI config: `ENABLE_SYSTEM_PROMPT=true|false`, `PROMPT_PATH`, `RESPONSE_LANGUAGE`, `STYLE_PRESET`.

- **Wire into memory**
  - Load the system prompt at memory initialization.
  - Prepend as role=`system` to the conversation buffer.
  - Guard against duplicates across requests in the same session.

- **Chain integration**
  - Ensure `chain.py` uses memory that already includes the system prompt.
  - Support runtime override (e.g., API param to supply an alternate prompt).

- **Safety and guardrails**
  - Include explicit refusal policy (no legal/medical, no PII, no harmful content).
  - Require “unknown” fallback when sources are insufficient.
  - Enforce output format rules (headings, bullets, fenced code, no overlong prose).

- **Observability**
  - Log whether the system prompt was applied (with a short hash/version).
  - Add a feature flag to disable for quick rollback.

- **Testing**
  - Unit test: first message is system, non-duplicated.
  - Integration test: response adheres to style/format and cites sources when available.
  - Check token budget impact.

- **Docs**
  - Update `README.md` with how to edit/override the prompt, env vars, and examples.

- **Rollout**
  - Default enabled behind flag; deploy, monitor, then remove flag if stable.

- **Acceptance criteria**
  - First message is the configured system prompt across all entrypoints.
  - No duplicate system messages within a session.
  - Responses follow style/guardrails; tests pass.
  - Configurable via file and env; safe rollback path.