import os  
import json  
import logging  
from time import perf_counter  
from pathlib import Path  
from datetime import datetime  
from typing import Dict, List  
import pandas as pd  
import phoenix as px  
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
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  
  
# Constants  
DEFAULT_WEIGHTS = {  
    "retrieval_relevance": 0.25,  
    "retrieval_correctness": 0.25,  
    "answer_grounding": 0.20,  
    "answer_accuracy": 0.20,  
    "answer_clarity": 0.10,  
}  
  
def calculate_metrics(question: str, answer: str, contexts: List[str], expected_keywords: List[str], ids: List[str]) -> Dict:  
    """Calculate all evaluation metrics in a single pass"""  
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
    #best prctises to handle multiple fucntions
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
  
    return metrics  
  
def process_qa_item(item: Dict, chain) -> Dict:  
    """Process a single QA item end-to-end"""  
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
      
    # Calculate all metrics  
    metrics = calculate_metrics(  
        question=item["question"],  
        answer=answer,  
        contexts=contexts,  
        expected_keywords=item.get("expected_keywords", []),  
        ids=ids  
    )  
  
    return {  
        "question": item["question"],  
        "answer": answer,  
        "latency_ms": round(latency_ms, 2),  
        "contexts": "\n\n".join(contexts),  
        "ids": "|".join(ids),  
        "expected_keywords": "|".join(item.get("expected_keywords", [])),  
        **metrics  
    }  
  
def run_evaluation() -> pd.DataFrame:  
    """Main evaluation workflow"""  
    # Load gold data  
    with open(Path("monitoring/eval/gold_qa.json")) as f:  
        gold_data = json.load(f)["items"]  
      
    # Process all items  
    chain = get_chain()  
    results = [process_qa_item(item, chain) for item in gold_data]  
      
    return pd.DataFrame(results)  
  
def upload_to_phoenix(df: pd.DataFrame, experiment_name: str, candidate_csv_path: Path) -> None:  
    """Handle Phoenix dataset and experiment creation"""  
    px_client = px.Client()  
      
    # Create unique dataset name  
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")  
    dataset_name = f"{experiment_name}-{timestamp}"  
      
    # Upload dataset  
    dataset = px_client.upload_dataset(  
        dataframe=df,  
        dataset_name=dataset_name,  
        input_keys=["question"],  
        output_keys=["answer"],  
    )  
    logger.info(f"Uploaded dataset '{dataset_name}'. Phoenix UI: {px.active_session().url}")  

  
if __name__ == "__main__":  
    # 1. Run evaluations once  
    df = run_evaluation()  
      
    # 2. Save results locally  
    experiment_name = os.getenv("EVAL_EXPERIMENT", "offline-eval")  
    output_dir = Path(f"monitoring/eval/experiments/{experiment_name}")  
    output_dir.mkdir(parents=True, exist_ok=True)  
      
    csv_path = output_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"  
    df.to_csv(csv_path, index=False)  
    logger.info(f"Saved results to {csv_path}")  
      
    # 3. Upload to Phoenix  
    upload_to_phoenix(df, experiment_name, csv_path)  
