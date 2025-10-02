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
    metrics = {  
        "duplicate_rate": 1 - (len(set(ids)) / len(ids)) if ids else 0.0,  
        "hit": sum(1 for k in expected_keywords if k in answer.lower()) / len(expected_keywords) >= 0.5,  
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
            #metrics is the dictionary that will be returned
            metrics[metric] = bool(func(*args))  
        except Exception as e:  
            logger.warning(f"Failed {metric} evaluation: {str(e)}")  
            metrics[metric] = False  
  
  
    # Calculate overall score
    # wt anvlaue recieved sum  
    metrics["overall_score"] = sum(  
        weight * float(metrics[metric])   
        for metric, weight in DEFAULT_WEIGHTS.items()  
    )  
    return metrics  
  
def process_qa_item(item: Dict, chain) -> Dict:  
    """Process a single QA item end-to-end"""  
    start_time = perf_counter()  
    result = chain.invoke({"question": item["question"]})
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
  
    return {  #relating question answer and metrices to the data
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

    results=pd.DataFrame(results)
    avg = {
        "retrieval_relevance": round(results['retrieval_relevance'].mean(), 3),
        "retrieval_correctness": round(results['retrieval_correctness'].mean(), 3),
        "answer_grounding": round(results['answer_grounding'].mean(), 3),
        "answer_accuracy": round(results['answer_accuracy'].mean(), 3),
        "answer_clarity": round(results['answer_clarity'].mean(), 3),
        "overall_score": round(results['overall_score'].mean(), 3),
    }
    print(avg)

    return results


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
        dataset_description="Evaluation dataset for the manifesto chatgpt",
    )  
 
    #if evaluated and upliaded what is meaning of run experiment?
    # # Run experiment: use candidate CSV path to avoid 'task' requirement on v11.30.0  

    # experiment = run_experiment(  
    #     candidate=str(candidate_csv_path),  
    #     experiment_name=dataset_name,  
    #     experiment_metadata={"run_timestamp": timestamp}  
    # )  
      
    # # Set primary metric  
    # evaluate_experiment(  
    #     experiment=experiment,  
    #     primary_metric="overall_score"  
        
    # )  
      
    logger.info(f"Phoenix experiment available at: {px.active_session().url}")  

  
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
    #upload_to_phoenix(df, experiment_name, csv_path)  


    #now: 28 sep 2025 will do
#      Examples uploaded: http://127.0.0.1:6006/datasets/RGF0YXNldDoxOA==/examples
# 🗄️ Dataset version ID: RGF0YXNldFZlcnNpb246MTk=
# Traceback (most recent call last):
#   File "D:\Nepal_action_plan\menifesto_chatgpt\run_eval_v2.py", line 154, in <module>
#     upload_to_phoenix(df, experiment_name, csv_path)
#   File "D:\Nepal_action_plan\menifesto_chatgpt\run_eval_v2.py", line 126, in upload_to_phoenix
#     experiment = run_experiment(
# TypeError: run_experiment() got an unexpected keyword argument 'candidate'