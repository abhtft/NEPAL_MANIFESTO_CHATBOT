import os  
import json  
import logging  
from time import perf_counter  
from pathlib import Path  
from datetime import datetime  
from typing import Dict, List  
import pandas as pd  
import phoenix as px  
from phoenix.experiments import run_experiment, evaluate_experiment  
from bot.chain import get_chain
 
#list of function call and each folder have . use 
from monitoring.eval.eval_func import (  
    evaluate_retrieval_relevance,  
    evaluate_retrieval_correctness,  
    evaluate_answer_grounding,  
    evaluate_answer_accuracy,  
    evaluate_clarity,  
)  
  
# Configure logging
# LOG LEVEL can be overridden with env var EVAL_LOG_LEVEL (e.g., DEBUG, INFO)
_LOG_LEVEL_NAME = os.getenv("EVAL_LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(level=_LOG_LEVEL)
logger = logging.getLogger(__name__)
  
"""Offline evaluation runner and Phoenix experiment logger.

This module computes per-row metrics using LLM judge functions, writes results to CSV,
and logs a Phoenix dataset and experiment so metrics are visible in the UI.

Key env vars:
- EVAL_EXPERIMENT: name prefix for saved CSV/experiment folder
- PHOENIX_ENDPOINT: Phoenix server endpoint (default http://127.0.0.1:6006)
- EVAL_LOG_LEVEL: logging level (DEBUG, INFO, WARNING, ERROR)
- EVAL_LOG_MAX_CHARS: truncate long fields in logs (default 500)
"""

# Constants
DEFAULT_WEIGHTS = {
    "retrieval_relevance": 0.25,  
    "retrieval_correctness": 0.25,  
    "answer_grounding": 0.20,  
    "answer_accuracy": 0.20,  
    "answer_clarity": 0.10,  
}

_LOG_MAX_CHARS = int(os.getenv("EVAL_LOG_MAX_CHARS", "500"))


def _truncate_for_log(text: str, max_chars: int = _LOG_MAX_CHARS) -> str:
    """Truncate long strings for concise logs."""
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}…(truncated {len(text) - max_chars} chars)"
  
def calculate_metrics(question: str, answer: str, contexts: List[str], expected_keywords: List[str], ids: List[str]) -> Dict:
    """Calculate all evaluation metrics in a single pass.

    Metrics computed:
    - duplicate_rate: fraction of non-unique document IDs (0.0 if none present)
    - hit: at least 50% of expected keywords appear in the answer (case-insensitive)
    - retrieval_relevance: LLM judge, contexts relevant to question
    - retrieval_correctness: LLM judge, contexts sufficient/correct
    - answer_grounding: LLM judge, answer grounded in contexts
    - answer_accuracy: LLM judge, answer accurate wrt contexts
    - answer_clarity: LLM judge, answer clarity
    - overall_score: weighted sum of the five LLM-based booleans
    """
    # Basic metrics
    filtered_ids = [i for i in ids if i]  
    if expected_keywords:  
        answer_lc = (answer or "").lower()  
        matches = sum(1 for k in expected_keywords if k and k.lower() in answer_lc)  
        hit_value = (matches / len(expected_keywords)) >= 0.5  
    else:  
        hit_value = False  
    metrics = {  
        "duplicate_rate": 1 - (len(set(filtered_ids)) / len(filtered_ids)) if filtered_ids else 0.0,  
        "hit": hit_value,  
    }  
  
    # LLM-based evaluations  
    # Best practice: map metric names to (callable, args) for a single-pass loop
    evaluation_functions = {  
        "retrieval_relevance": (evaluate_retrieval_relevance, [question, contexts]),  
        "retrieval_correctness": (evaluate_retrieval_correctness, [question, contexts]),  
        "answer_grounding": (evaluate_answer_grounding, [question, contexts, answer]),  
        "answer_accuracy": (evaluate_answer_accuracy, [question, contexts, answer]),  
        "answer_clarity": (evaluate_clarity, [{"answer": answer}, {"question": question}]),  
    }  
  
    for metric, (func, args) in evaluation_functions.items():  
        try:  
            metrics[metric] = bool(func(*args))  
        except Exception as e:  
            logger.warning(f"Failed {metric} evaluation: {str(e)}")  
            metrics[metric] = False  
  
    # Calculate overall score  
    metrics["overall_score"] = sum(  
        weight * float(metrics[metric])   
        for metric, weight in DEFAULT_WEIGHTS.items()  
    )  

    logger.debug(
        "metrics_computed question='%s' hit=%s duplicate_rate=%.3f overall=%.3f",
        _truncate_for_log(question or ""),
        metrics.get("hit"),
        metrics.get("duplicate_rate", 0.0),
        metrics.get("overall_score", 0.0),
    )
  
    return metrics  
  
def process_qa_item(item: Dict, chain) -> Dict:
    """Process a single QA item end-to-end.

    1) Invoke the retrieval+LLM chain
    2) Extract contexts and IDs
    3) Compute metrics
    4) Return a flat, CSV-friendly dict
    """
    start_time = perf_counter()  
    try:  
        result = chain.invoke({"question": item["question"]})  
    except Exception as e:  
        logger.exception(f"Chain invocation failed for question: {item.get('question')}. Error: {e}")  
        result = {}  
    #dict form with source there  
    latency_ms = (perf_counter() - start_time) * 1000  
  
    answer = result.get("answer", "")  
    docs = result.get("source_documents", [])  
      
    # Extract document info  
    ids = [str(d.metadata.get("id", "")) for d in docs]  
    contexts = [d.page_content for d in docs if getattr(d, "page_content", "")]  
    logger.debug(
        "qa_item_extracted question='%s' latency_ms=%.2f contexts=%d ids=%d",
        _truncate_for_log(item.get("question", "")),
        latency_ms,
        len(contexts),
        len([i for i in ids if i]),
    )
      
    # Calculate all metrics  
    metrics = calculate_metrics(  
        question=item["question"],  
        answer=answer,  
        contexts=contexts,  
        expected_keywords=item.get("expected_keywords", []),  
        ids=ids  
    )  
  
    record = {  
        "question": item["question"],  
        "answer": answer,  
        "latency_ms": round(latency_ms, 2),  
        "contexts": "\n\n".join(contexts),  
        "ids": "|".join(ids),  
        "expected_keywords": "|".join(item.get("expected_keywords", [])),  
        **metrics  
    }
    logger.debug(
        "qa_item_result question='%s' overall=%.3f",
        _truncate_for_log(item.get("question", "")),
        record.get("overall_score", 0.0),
    )
    return record  
  
def run_evaluation() -> pd.DataFrame:
    """Main evaluation workflow.

    Loads gold questions, runs the chain per item, computes metrics, and
    returns a DataFrame ready for CSV and Phoenix upload.
    """
    # Load gold data
    with open(Path("monitoring/eval/gold_qa.json")) as f:  
        gold_data = json.load(f)["items"]  
    logger.info("gold_loaded count=%d", len(gold_data))

    # Process all items
    chain = get_chain()  
    logger.info("evaluation_started items=%d", len(gold_data))
    results = [process_qa_item(item, chain) for item in gold_data]
    logger.info("evaluation_completed items=%d", len(results))

    return pd.DataFrame(results)  
  
def upload_to_phoenix(df: pd.DataFrame, experiment_name: str, candidate_csv_path: Path) -> None:
    """Upload results as a Phoenix dataset and run an experiment.

    - Creates a unique dataset name using experiment_name + timestamp
    - Uploads the DataFrame (inputs: question, outputs: answer)
    - Runs a Phoenix experiment that recomputes the five metrics plus overall_score
    - Marks overall_score as the primary metric
    """
    endpoint = os.getenv("PHOENIX_ENDPOINT", "http://127.0.0.1:6006")  
    px_client = px.Client(endpoint=endpoint)  
      
    # Create unique dataset name  
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")  
    dataset_name = f"{experiment_name}-{timestamp}"  
      
    # Upload dataset  
    # Include precomputed metric columns as inputs so experiment evaluators can read them
    metric_input_keys = [
        "retrieval_relevance",
        "retrieval_correctness",
        "answer_grounding",
        "answer_accuracy",
        "answer_clarity",
        "overall_score",
        "hit",
        "duplicate_rate",
    ]
    present_metric_keys = [k for k in metric_input_keys if k in df.columns]
    input_keys = ["question", "contexts", *present_metric_keys]

    dataset = px_client.upload_dataset(
        dataframe=df,
        dataset_name=dataset_name,
        input_keys=input_keys,
        output_keys=["answer"],
    )
    logger.info("phoenix_dataset_uploaded name='%s' rows=%d endpoint=%s", dataset_name, len(df), endpoint)

    # Run a Phoenix experiment so metrics are visible in the Experiments UI.
    def _get_input(example, key: str):
        inputs = getattr(example, "inputs", {}) or {}
        return inputs.get(key, "")

    def _get_output(output: Dict, example, key: str):
        # Prefer task output; fallback to dataset outputs
        if isinstance(output, dict) and key in output:
            return output.get(key) or ""
        outputs = getattr(example, "outputs", {}) or {}
        return outputs.get(key, "")

    def _parse_contexts_from_inputs(example) -> List[str]:
        raw = str(_get_input(example, "contexts") or "")
        parts = [p for p in raw.split("\n\n") if p and p.strip()]
        return parts

    # Evaluators that read precomputed metrics from dataset inputs
    def _as_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in ("1", "true", "yes", "y"): return True
        if s in ("0", "false", "no", "n", "none", ""): return False
        try:
            return float(s) != 0.0
        except Exception:
            return False

    def _as_float(value) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    def _eval_retrieval_relevance(example=None, output=None, **_):
        return _as_bool(_get_input(example, "retrieval_relevance"))

    def _eval_retrieval_correctness(example=None, output=None, **_):
        return _as_bool(_get_input(example, "retrieval_correctness"))

    def _eval_answer_grounding(example=None, output=None, **_):
        return _as_bool(_get_input(example, "answer_grounding"))

    def _eval_answer_accuracy(example=None, output=None, **_):
        return _as_bool(_get_input(example, "answer_accuracy"))

    def _eval_answer_clarity(example=None, output=None, **_):
        return _as_bool(_get_input(example, "answer_clarity"))

    def _eval_overall_score(example=None, output=None, **_):
        val = _get_input(example, "overall_score")
        return _as_float(val)

    def _task_identity(example) -> Dict:
        # Identity task so evaluators can read already-computed outputs
        return {"answer": _get_output({}, example, "answer")}

    _evaluators = {
        "retrieval_relevance": _eval_retrieval_relevance,
        "retrieval_correctness": _eval_retrieval_correctness,
        "answer_grounding": _eval_answer_grounding,
        "answer_accuracy": _eval_answer_accuracy,
        "answer_clarity": _eval_answer_clarity,
        "overall_score": _eval_overall_score,
    }
    logger.info("phoenix_experiment_running name='%s'", dataset_name)
    experiment = run_experiment(
        dataset=dataset,
        task=_task_identity,
        evaluators=_evaluators,
        experiment_name=dataset_name,
        experiment_description="Offline LLM-judge metrics computed in Phoenix",
    )
    evaluate_experiment(experiment, _evaluators)
    logger.info("phoenix_experiment_completed name='%s' primary_metric=overall_score", dataset_name)

  
if __name__ == "__main__":  
    # 1. Run evaluations once
    df = run_evaluation()  
      
    # 2. Save results locally
    experiment_name = os.getenv("EVAL_EXPERIMENT", "offline-eval")  
    output_dir = Path(f"monitoring/eval/experiments/{experiment_name}")  
    output_dir.mkdir(parents=True, exist_ok=True)  
      
    csv_path = output_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"  
    df.to_csv(csv_path, index=False)  
    logger.info("results_saved path='%s' rows=%d", str(csv_path), len(df))
      
    # 3. Upload to Phoenix
    upload_to_phoenix(df, experiment_name, csv_path)  
