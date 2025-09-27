


import json
import os
from time import perf_counter
from pathlib import Path
import csv
from bot.chain import get_chain
from opentelemetry.trace import StatusCode
#from phoenix.experiments import run_experiment

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

    #gold json
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
    variant = os.getenv("EVAL_VARIANT", "default")

    # Metric weights for overall score in [0,1]
    # Adjust via env var EVAL_WEIGHTS_JSON if needed, e.g. '{"relevance":0.25,"correctness":0.25,"grounding":0.2,"accuracy":0.2,"clarity":0.1}'
    default_weights = {
        "retrieval_relevance": 0.25,
        "retrieval_correctness": 0.25,
        "answer_grounding": 0.20,
        "answer_accuracy": 0.20,
        "answer_clarity": 0.10,
    }
    try:
        weights_raw = os.getenv("EVAL_WEIGHTS_JSON")
        if weights_raw:
            parsed = json.loads(weights_raw)
            # Only override known keys to avoid schema drift
            for k in list(default_weights.keys()):
                if k in parsed:
                    default_weights[k] = float(parsed[k])
    except Exception:
        pass

    tracer = None

    try:
        if otel_trace is not None:
            tracer = otel_trace.get_tracer("evaluation")
    except Exception:
        tracer = None

    # Collect rows for experiment dataset
    dataset_rows = []

    for item in gold:
        q = item["question"]
        expected_keywords = set(k.lower() for k in item.get("expected_keywords", []))

        # Start a ROOT span per question so each item is a separate trace
        item_span_cm = tracer.start_as_current_span("evaluation_item", context=Context()) if tracer is not None and Context is not None else None
        if item_span_cm is not None:
            item_span = item_span_cm.__enter__()
            try:
                
                item_span.set_attribute("eval.expected_keywords_count", len(expected_keywords))
                item_span.set_attribute("eval.question_length", len(q))
                

                item_span.set_attribute("input", q)

                #otel.
                
            except Exception:
                pass

        #item_span.set_status(StatusCode.OK)
        #item_span.end_span()


        start = perf_counter()
        out = chain.invoke({"question": q})#q is simple question from gold_qa.json




        latency_ms = (perf_counter() - start) * 1000.0
        total_latency_ms += latency_ms

        #getting responce
        answer = out.get("answer", "") or ""
        docs = out.get("source_documents", []) or []

        #saving responce to file
        with open('responce.json', 'w', encoding='utf-8') as f:  
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)  

            #to_dict().#to_json()



        #dict is the form

        #answer=out.get('answer',"")

        # Simple retrieval duplicate rate (by page or metadata source)
        #getattr study
        #stick heavily on defensie programming

        ids = []
        for d in docs:
            meta = getattr(d, "metadata", {}) or {}
            id_str = str(meta.get("id", "")) 
            ids.append(id_str)
            #ids.append(d.metadata.get("id", ""))#


        ##duplicate rate#
        #printing responce to dict
        #print(json.dumps(responce.to_dict(),ensure_ascii=False,indent=2))
        #print(json.dumps(out.to_dict(),ensure_ascii=False,indent=2))
        #print(json.dumps(out.to_dict(),ensure_ascii=False,indent=2))



        #duplicate rate#
        #
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
        contexts_text = "\n\n".join(contexts)

        # Naive hit check: keyword overlap with answer
        present = sum(1 for k in expected_keywords if k in answer.lower())
        hit = present >= max(1, int(0.5 * len(expected_keywords))) if expected_keywords else False #safe zone
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

        # Compute overall_score as weighted average in [0,1]
        def _to_unit(v: bool) -> float:
            try:
                return 1.0 if bool(v) else 0.0
            except Exception:
                return 0.0

        weighted_numerators = (
            default_weights["retrieval_relevance"] * _to_unit(ret_rel)
            + default_weights["retrieval_correctness"] * _to_unit(ret_corr)
            + default_weights["answer_grounding"] * _to_unit(ans_ground)
            + default_weights["answer_accuracy"] * _to_unit(ans_acc)
            + default_weights["answer_clarity"] * _to_unit(ans_clear)
        )
        weights_denominator = sum(default_weights.values()) or 1.0
        overall_score = max(0.0, min(1.0, weighted_numerators / weights_denominator))

        if item_span_cm is not None:
            try:
               
                item_span.set_attribute("eval.duplicate_rate", round(dup_rate, 3))
                item_span.set_attribute("eval.hit", bool(hit))#50%above same word
                item_span.set_attribute("eval.answer_length", len(answer))#total characters in answer
                item_span.set_attribute("output", answer)
                # Add new metric attributes
                item_span.set_attribute("eval.retrieval_relevance", bool(ret_rel))
                item_span.set_attribute("eval.retrieval_correctness", bool(ret_corr))
                item_span.set_attribute("eval.answer_grounding", bool(ans_ground))
                item_span.set_attribute("eval.answer_accuracy", bool(ans_acc))
                item_span.set_attribute("eval.answer_clarity", bool(ans_clear))
                item_span.set_attribute("eval.id", ids)
                # Experiment tags
                item_span.set_attribute("experiment.name", experiment_name)
                item_span.set_attribute("experiment.run_id", run_id)
                item_span.set_attribute("experiment.variant", variant)
                item_span.set_attribute("experiment.overall_score", round(overall_score, 3))
                item_span.set_status(StatusCode.OK)
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
            "overall_score": round(overall_score, 3),
            "answer": answer,
            "ids": ids,
            "experiment_name": experiment_name,
            "run_id": run_id,
            "variant": variant,
        })

        # Add a row for the experiment dataset
        dataset_rows.append({
            "experiment_name": experiment_name,
            "run_id": run_id,
            "variant": variant,
            "question": q,
            "answer": answer,
            "contexts": contexts_text,
            "latency_ms": round(latency_ms, 2),
            "duplicate_rate": round(dup_rate, 3),
            "retrieval_relevance": 1 if ret_rel else 0,
            "retrieval_correctness": 1 if ret_corr else 0,
            "answer_grounding": 1 if ans_ground else 0,
            "answer_accuracy": 1 if ans_acc else 0,
            "answer_clarity": 1 if ans_clear else 0,
            "overall_score": round(overall_score, 3),
            "ids": "|".join(ids) if ids else "",
            "expected_keywords": "|".join(sorted(expected_keywords)) if expected_keywords else "",
        })

    # Dataset-level aggregates
    try:
        avg_overall_score = round(sum([r.get("overall_score", 0.0) for r in results]) / max(1, len(results)), 3)
    except Exception:
        avg_overall_score = 0.0

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
        "overall_score": avg_overall_score,
        "experiment_name": experiment_name,
        "run_id": run_id,
        "variant": variant,
        "results": results,
    }

    # Persist artifacts: CSV dataset and JSON summary
    dataset_path = None
    try:
        base_dir = Path("monitoring") / "eval" / "experiments" / experiment_name
        base_dir.mkdir(parents=True, exist_ok=True)

        dataset_path = base_dir / f"{run_id}.csv"

        #creating file for dataset
        if dataset_rows:
            fieldnames = [
                "experiment_name",
                "run_id",
                "variant",
                "question",
                "answer",
                "contexts",
                "latency_ms",
                "duplicate_rate",
                "retrieval_relevance",
                "retrieval_correctness",
                "answer_grounding",
                "answer_accuracy",
                "answer_clarity",
                "overall_score",
                "ids",
                "expected_keywords",
            ]
            with dataset_path.open("w", encoding="utf-8", newline="") as fcsv:
                writer = csv.DictWriter(fcsv, fieldnames=fieldnames)
                writer.writeheader()
                for row in dataset_rows:
                    writer.writerow(row)

        summary_path = base_dir / f"{run_id}_summary.json"
        with summary_path.open("w", encoding="utf-8") as fsum:
            json.dump(summary, fsum, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Upload dataset to Phoenix (preferred flow for Experiments)
    phoenix_dataset = None
    try:
        import phoenix as px  # type: ignore
        import pandas as pd  # type: ignore
        if pd is not None and dataset_rows:
            df = pd.DataFrame(dataset_rows)
            print(df)
            px_client = px.Client()  # type: ignore 
            ds_name = f"{experiment_name}-{run_id}"
            try:
                phoenix_dataset = px_client.datasets.create_dataset(  # type: ignore
                    dataframe=df,
                    dataset_name=ds_name,
                    input_keys=["question"],
                    output_keys=["answer"],
                )
            
                print(f"✅ Uploaded dataset: {ds_name}")
            except Exception:
                pass
    except Exception:
        phoenix_dataset = None

    # Attempt to register and evaluate a Phoenix Experiment if available
    try:
        from phoenix.experiments import run_experiment, evaluate_experiment  # type: ignore
        try:
            # Prefer running with uploaded dataset; fallback to CSV candidate path
            if phoenix_dataset is not None:
                try:
                    print(f"🚀 Running experiment '{experiment_name}' for run '{run_id}'...")
                except Exception:
                    pass
                exp = run_experiment(  # type: ignore
                    dataset=phoenix_dataset,
                    experiment_name=experiment_name,
                    experiment_metadata={"run_id": run_id, "variant": variant},
                )
            elif dataset_path is not None:
                exp = run_experiment(candidate=str(dataset_path))  # type: ignore
            else:
                exp = None  # type: ignore
            try:
                # Evaluate and set primary metric so it appears at the top of the UI
                if exp is not None:
                    evaluate_experiment(  # type: ignore
                        experiment=exp,
                        primary_metric="overall_score",
                    )
            except Exception:
                pass
        except Exception:
            # Fallback: API signature/version differences
            pass
    except Exception:
        # Phoenix experiments module not available; silently skip
        pass
    return summary


if __name__ == "__main__":
    s = evaluate()
    print(json.dumps(s, ensure_ascii=False, indent=2))#indent 2 means 2 spaces
    


#evluating based on (retreieval quality,answer quality,citation quality,safety and policy,cost and latency)

#retreieval quality
#answer quality
#citation quality
#safety and policy
#cost and latency

#answer relevance based on context


#leave it as more complex,focus on basics


#run for duplicacy document

#building experiment wise very good evaluation score


#
# %%
