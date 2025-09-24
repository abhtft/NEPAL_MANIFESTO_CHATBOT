### Evaluation action plan for the chatbot (no code)

- Data and baselines
  - Build a small gold dataset (50–200) of Q&A pairs from the manifesto with citations to page/section.
  - Include “hard” cases: ambiguous questions, cross-section queries, out-of-scope prompts, and adversarial phrasing.
  - Freeze a baseline run (current MMR retriever) for comparison.

- Retrieval quality
  - Metrics: top-k hit rate (does any retrieved chunk contain the gold answer), MRR@k, context precision/recall, and retrieval diversity.
  - Diagnostics: duplicate chunk rate, average chunk overlap, per-query doc score distribution.
  - Sensitivity tests: vary k, fetch_k, and lambda to map quality vs cost.

- Answer quality
  - LLM-as-judge with a strict rubric: relevance, groundedness (faithfulness to retrieved context), completeness, and helpfulness (1–5 or pass/fail).
  - Hallucination check: judge must fail responses that include info absent from retrieved context.
  - Include refusal correctness for out-of-scope and harmful prompts.

- Citation/grounding checks
  - Require each answer to cite snippet IDs or sections; verify cited chunks actually support claims via string-match or semantic overlap.
  - Penalize answers without citations when evidence exists.

- Safety and policy
  - Evaluate refusal on restricted topics (medical/legal/PII) and tone/format adherence.
  - Add toxicity and PII detectors on inputs/outputs (lightweight thresholding).

- Cost and latency
  - Track end-to-end and component latencies (retriever, LLM), output token counts, and cost per query.
  - Define budgets and alert thresholds for p95 latency and average tokens.

- Observability in Phoenix
  - Ensure traces log: session/request IDs, model name/params, retrieval scores, token counts, latencies, judge scores.
  - Create Phoenix dashboards for: retrieval hit rate, hallucination rate, latency, and cost trends; slice by question type.

- Automation & CI
  - Add a nightly eval job on the gold dataset; store run IDs and compare against baseline.
  - Set regression gates (e.g., groundedness ≥ 0.9, hallucination ≤ 5%, p95 latency ≤ target).

- Human-in-the-loop
  - Weekly sample review (e.g., 20 queries) for rubric calibration and drift detection.
  - Feed misfires back into the dataset; expand “hard cases” over time.

- Experimentation loop
  - Test chunking params (size/overlap), re-embed strategy, retriever variants (hybrid BM25+vector), and prompt tweaks.
  - Use A/B runs and Phoenix slices per variant; adopt changes only if metrics improve without cost/latency regressions.

- Governance and versioning
  - Version datasets, prompts, and retriever configs; tie runs to git commits.
  - Document metric definitions and acceptance thresholds in the repo.

- Acceptance criteria
  - Automated eval pipeline produces scores per run with Phoenix dashboards.
  - Retrieval hit rate and groundedness meet thresholds; hallucination and duplicates stay low.
  - Latency/cost within budget; alerts configured; changes tracked and reproducible.

- Near-term quick wins
  - Add judge scoring for groundedness and relevance on your current gold set.
  - Add token and latency logging to traces; create a Phoenix dashboard.
  - Tune `k/fetch_k/lambda_mult` with a small grid search and lock in best params.

- Medium-term enhancements
  - Hybrid search (BM25 + vector) and reranking for tougher queries.
  - Fine-tune the prompt for style/citation consistency; test structured output constraints.

- Long-term
  - Drift monitoring for embeddings (periodic re-embed) and data updates.
  - Expand eval set to cover new manifesto revisions and user feedback.


  -----------------------------------------------------------
  ### P0 — Do now
- Build small gold Q&A set (50–200) with section/page citations.
- Enable Phoenix trace attributes: session/request IDs, model name, k/fetch_k/lambda, scores, token counts, latencies.
- Add LLM-as-judge for groundedness and relevance; fail if unsupported by context.
- Track retrieval hit rate@k and duplicate rate; keep k=4 with MMR.

### P1 — Next
- Auto citation check: ensure cited chunks support claims (string/semantic overlap).
- Add per-query cost/latency dashboards in Phoenix; alert on p95 latency and token spikes.
- Nightly batch eval on gold set; compare to baseline and block regressions.

### P2 — Later
- Try hybrid retrieval (BM25 + vector) or reranking; adopt only if groundedness improves without cost blowup.
- Safety checks: refusal correctness for out-of-scope and PII/toxicity screens.
- Human review: weekly 20-sample audit; feed misses back into gold set.

-------------------------------------------------

sure,please update the code as per do now part.keep updates clear ,consize and not add unneceesary complexity.add those things that bring meaningfull variation in chatbot. You are allowed to read manifesto.pdf in data section to generate gold questions .keep 15 eval diverse question.PLease start


--------------------------------------------------

I'll quickly scan the repository for any Phoenix/Arize integration to understand why run_eval.py isn't updating a Phoenix experiment and then explain the best approach.

[6 tools called]

I checked your repo: Phoenix tracing is only initialized in `app.py` via `init_arize_tracing()`. `run_eval.py` doesn’t initialize Phoenix/OpenTelemetry at all, so those eval runs won’t show up in Phoenix “experiments” (or any Phoenix project) right now.

### Should `run_eval.py` update a Phoenix experiment?
Yes—if you want your evaluation runs to appear in Phoenix, you should instrument `run_eval.py` the same way as the app:

- Initialize Phoenix OTEL before calling the chain (same as `init_arize_tracing()` in `app.py`).
- Ensure a Phoenix collector is running and reachable (local Phoenix server or configured OTLP endpoint).
- Tag each evaluation with clear metadata so you can slice/filter in Phoenix:
  - experiment_name/run_id/dataset_name/commit_sha
  - per-item attributes: latency_ms, duplicate_rate, hit, expected_keywords_count
- Optionally keep evals separate by using a different `project_name` from the app, or add a span/resource attribute like `context=evaluation`.

This approach lets Phoenix capture:
- All LLM/RAG spans from `chain.invoke(...)`
- Your eval metrics as span attributes
- Easy comparison across runs by filtering on `experiment_name` or `run_id`

### When sticking to JSON is enough
If you only need a quick local summary (hit rate, avg latency, duplicate rate), your current `run_eval.py` output is fine. But for longitudinal tracking, debugging misretrievals, and comparing runs, emitting traces to Phoenix is the better method.

### Minimal checklist (no code)
- Run a Phoenix server/collector and confirm the OTLP endpoint is reachable.
- Initialize Phoenix OTEL in `run_eval.py` (same pattern used in `app.py`) with a project name.
- Add experiment/run metadata and eval metrics as span attributes around each `chain.invoke`.
- Use Phoenix UI to filter by experiment/run.

Status: I reviewed `monitoring/arize_integration.py`, `app.py`, `bot/chain.py`, and confirmed `run_eval.py` lacks tracing init—hence no Phoenix updates. If you want, I can wire this up next.