import json
import os
from time import perf_counter
from bot.chain import get_chain
from monitoring.arize_integration import init_arize_tracing
from monitoring.eval.eval_func import (
    evaluate_retrieval_relevance,
    evaluate_retrieval_correctness,
    evaluate_answer_grounding,
    evaluate_answer_accuracy,
    evaluate_clarity,
)
try:
    from opentelemetry import trace as otel_trace  # type: ignore
    from opentelemetry.context import Context  # type: ignore
except Exception:
    otel_trace = None  # optional
    Context = None  # type: ignore


def evaluate() -> dict:
    with open(os.path.join("monitoring", "eval", "gold_qa.json"), "r", encoding="utf-8") as f:
        gold = json.load(f)["items"]

    # Enable Phoenix/OTEL tracing (non-blocking)
    try:
        init_arize_tracing()
    except Exception:
        pass

    chain = get_chain()

    results = []
    hit_count = 0
    total_latency_ms = 0.0
    duplicate_rates = []

    # New metric counters
    retrieval_relevance_true = 0
    retrieval_correctness_true = 0
    answer_grounding_true = 0
    answer_accuracy_true = 0
    answer_clarity_true = 0

    # Identify this evaluation run
    run_id = os.getenv("EVAL_RUN_ID", os.getenv("GIT_COMMIT", "local-run"))
    experiment_name = os.getenv("EVAL_EXPERIMENT", "offline-eval")

    tracer = None
    try:
        if otel_trace is not None:
            tracer = otel_trace.get_tracer("evaluation")
    except Exception:
        tracer = None

    for item in gold:
        q = item["question"]
        expected_keywords = set(k.lower() for k in item.get("expected_keywords", []))

        # Start a ROOT span per question so each item is a separate trace
        item_span_cm = tracer.start_as_current_span("evaluation_item", context=Context()) if tracer is not None and Context is not None else None
        if item_span_cm is not None:
            item_span = item_span_cm.__enter__()
            try:
                item_span.set_attribute("eval.context", "evaluation")
                item_span.set_attribute("eval.experiment", experiment_name)
                item_span.set_attribute("eval.run_id", run_id)
                item_span.set_attribute("eval.expected_keywords_count", len(expected_keywords))
                item_span.set_attribute("eval.question_length", len(q))
                item_span.set_attribute("input", q)
            except Exception:
                pass

        start = perf_counter()
        out = chain.invoke({"question": q})#q is simple question from gold_qa.json
        latency_ms = (perf_counter() - start) * 1000.0
        total_latency_ms += latency_ms

        #getting responce
        answer = out.get("answer", "") or ""
        docs = out.get("source_documents", []) or []

        # Simple retrieval duplicate rate (by page or metadata source)
        #getattr study
        ids = []
        for d in docs:
            meta = getattr(d, "metadata", {}) or {}
            id_str = str(meta.get("source", "")) + ":" + str(meta.get("page", meta.get("page_number", "")))
            ids.append(id_str)

        unique = len(set(ids)) if ids else 0
        dup_rate = 1.0 - (unique / len(ids)) if ids else 0.0
        duplicate_rates.append(dup_rate)

        # Prepare plain text contexts from retrieved documents
        contexts = []
        for d in docs:
            try:
                content = getattr(d, "page_content", "") or ""
            except Exception:
                content = ""
            if content:
                contexts.append(content)

        # Naive hit check: keyword overlap with answer
        present = sum(1 for k in expected_keywords if k in answer.lower())
        hit = present >= max(1, int(0.5 * len(expected_keywords))) if expected_keywords else False
        if hit:
            hit_count += 1

        # Run LLM-based evaluations (best-effort)
        try:
            ret_rel = bool(evaluate_retrieval_relevance(q, contexts))
        except Exception:
            ret_rel = False
        try:
            ret_corr = bool(evaluate_retrieval_correctness(q, contexts))
        except Exception:
            ret_corr = False
        try:
            ans_ground = bool(evaluate_answer_grounding(q, contexts, answer))
        except Exception:
            ans_ground = False
        try:
            ans_acc = bool(evaluate_answer_accuracy(q, contexts, answer))
        except Exception:
            ans_acc = False
        try:
            ans_clear = bool(evaluate_clarity({"answer": answer}, {"question": q}))
        except Exception:
            ans_clear = False

        retrieval_relevance_true += 1 if ret_rel else 0
        retrieval_correctness_true += 1 if ret_corr else 0
        answer_grounding_true += 1 if ans_ground else 0
        answer_accuracy_true += 1 if ans_acc else 0
        answer_clarity_true += 1 if ans_clear else 0

        if item_span_cm is not None:
            try:
                item_span.set_attribute("eval.latency_ms", round(latency_ms, 2))
                item_span.set_attribute("eval.duplicate_rate", round(dup_rate, 3))
                item_span.set_attribute("eval.hit", bool(hit))
                item_span.set_attribute("eval.answer_length", len(answer))
                item_span.set_attribute("output", answer)
                # Add new metric attributes
                item_span.set_attribute("eval.retrieval_relevance", bool(ret_rel))
                item_span.set_attribute("eval.retrieval_correctness", bool(ret_corr))
                item_span.set_attribute("eval.answer_grounding", bool(ans_ground))
                item_span.set_attribute("eval.answer_accuracy", bool(ans_acc))
                item_span.set_attribute("eval.answer_clarity", bool(ans_clear))
            except Exception:
                pass
            try:
                item_span_cm.__exit__(None, None, None)
            except Exception:
                pass

        results.append({
            "question": q,
            "latency_ms": round(latency_ms, 2),
            "duplicate_rate": round(dup_rate, 3),
            "hit": hit,
            "retrieval_relevance": ret_rel,
            "retrieval_correctness": ret_corr,
            "answer_grounding": ans_ground,
            "answer_accuracy": ans_acc,
            "answer_clarity": ans_clear,
        })

    summary = {
        "n": len(gold),
        "hit_rate": round(hit_count / max(1, len(gold)), 3),
        "avg_latency_ms": round(total_latency_ms / max(1, len(gold)), 2),
        "avg_duplicate_rate": round(sum(duplicate_rates) / max(1, len(duplicate_rates)), 3),
        "retrieval_relevance_rate": round(retrieval_relevance_true / max(1, len(gold)), 3),
        "retrieval_correctness_rate": round(retrieval_correctness_true / max(1, len(gold)), 3),
        "answer_grounding_rate": round(answer_grounding_true / max(1, len(gold)), 3),
        "answer_accuracy_rate": round(answer_accuracy_true / max(1, len(gold)), 3),
        "answer_clarity_rate": round(answer_clarity_true / max(1, len(gold)), 3),
        "results": results,
    }
    return summary


if __name__ == "__main__":
    s = evaluate()
    print(json.dumps(s, ensure_ascii=False, indent=2))


#evluating based on (retreieval quality,answer quality,citation quality,safety and policy,cost and latency)

#retreieval quality
#answer quality
#citation quality
#safety and policy
#cost and latency

#answer relevance based on context


