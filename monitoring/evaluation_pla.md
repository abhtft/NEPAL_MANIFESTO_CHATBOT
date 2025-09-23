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
