##############
#Evaluation prompts and LLM judge utilities#########################

from typing import List, Dict, Any, Optional
import os

from langchain_openai import AzureChatOpenAI


# -------------------------
# Prompt templates (unified style)
# -------------------------

#########################################################
# 1. Answer clarity
CLARITY_LLM_JUDGE_PROMPT = """
You will evaluate the clarity of an assistant's answer to a user's question.
Clear answers are precise, coherent, and directly address the question without unnecessary complexity.

[BEGIN DATA]
question: {question}
answer: {answer}
[END DATA]

Provide an explanation first. Then output a single label.
EXPLANATION: step-by-step reasoning about clarity
LABEL: clear or unclear
"""


#########################################################
# 2. Retrieval relevance to the question
RETRIEVAL_RELEVANCE_LLM_JUDGE_PROMPT = """
You will evaluate whether the retrieved context snippets are relevant to the user's question.
Relevant means they are topically aligned and can help answer the question.

[BEGIN DATA]
question: {question}
retrieved_context:
{contexts}
[END DATA]

Provide an explanation first. Then output a single label.
EXPLANATION: reasoning about relevance to the question
LABEL: relevant or irrelevant
"""


#########################################################
# 3. Retrieval correctness/sufficiency for the question
RETRIEVAL_CORRECTNESS_LLM_JUDGE_PROMPT = """
You will judge whether the retrieved context snippets are sufficient and correct to answer the user's question.
Correct/sufficient means they contain the key facts needed without obvious contradictions.

[BEGIN DATA]
question: {question}
retrieved_context:
{contexts}
[END DATA]

Provide an explanation first. Then output a single label.
EXPLANATION: reasoning about sufficiency and correctness
LABEL: correct or incorrect
"""



#learning function similar to arize phoenix

#########################################################
# 4. Answer grounding in retrieved context
ANSWER_GROUNDING_LLM_JUDGE_PROMPT = """
You will judge whether the assistant's answer is grounded in and supported by the retrieved context snippets.
Grounded means claims in the answer are justified by the provided context and do not contradict it.

[BEGIN DATA]
question: {question}
retrieved_context:
{contexts}
answer: {answer}
[END DATA]

Provide an explanation first. Then output a single label.
EXPLANATION: reasoning about grounding and consistency
LABEL: grounded or not_grounded
"""


#########################################################
# 5. Answer factual accuracy w.r.t. retrieved context
ANSWER_ACCURACY_LLM_JUDGE_PROMPT = """
You will judge the factual accuracy of the assistant's answer with respect to the retrieved context snippets.
Accurate means the answer's statements are factually correct given the provided context.

[BEGIN DATA]
question: {question}
retrieved_context:
{contexts}
answer: {answer}
[END DATA]

Provide an explanation first. Then output a single label.
EXPLANATION: reasoning about factual accuracy
LABEL: accurate or inaccurate
"""


# -------------------------
# LLM helper
# -------------------------

_EVAL_LLM: Optional[AzureChatOpenAI] = None


def get_eval_llm() -> AzureChatOpenAI:
    global _EVAL_LLM
    if _EVAL_LLM is None:
        deployment = os.getenv("EVAL_AZURE_DEPLOYMENT", os.getenv("AZURE_EVAL_DEPLOYMENT", "gpt-4.1"))
        _EVAL_LLM = AzureChatOpenAI(
            azure_deployment=deployment,
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            temperature=0
        )
    return _EVAL_LLM


def _format_contexts(contexts: Optional[List[str]]) -> str:
    if not contexts:
        return "(no retrieved context)"
    # Separate snippets with a clear delimiter for the judge
    return "\n---\n".join(c.strip() for c in contexts if c and c.strip()) or "(no retrieved context)"


def _extract_label(text: str, rails: List[str]) -> str:
    # Try to parse a line starting with LABEL:
    for line in reversed([l.strip() for l in text.splitlines() if l.strip()]):
        if line.lower().startswith("label:"):
            value = line.split(":", 1)[1].strip().strip('"').strip("'")
            # Normalize and match to rails
            for r in rails:
                if value.lower() == r.lower():
                    return r
    # Fallback: find the last occurrence of any rail token in text
    lowered = text.lower()
    for r in rails:
        if r.lower() in lowered:
            return r
    # Default to the first rail if nothing matched
    return rails[0]


def llm_judge(
    question: Optional[str],
    answer: Optional[str],
    contexts: Optional[List[str]],
    template: str,
    rails: List[str],
) -> Dict[str, str]:
    llm = get_eval_llm()
    prompt = template.format(
        question=(question or ""),
        answer=(answer or ""),
        contexts=_format_contexts(contexts),
    )
    resp = llm.invoke(prompt)
    text = getattr(resp, "content", str(resp))
    label = _extract_label(text, rails)
    return {"label": label, "explanation": text}


#as per general json format data else dataframe was better method

# -------------------------
# Public evaluator functions (minimal wrappers)
# -------------------------

def evaluate_retrieval_relevance(question: str, contexts: List[str]) -> bool:
    result = llm_judge(
        question=question,
        answer=None,
        contexts=contexts,
        template=RETRIEVAL_RELEVANCE_LLM_JUDGE_PROMPT,
        rails=["relevant", "irrelevant"],
    )
    return result["label"].lower() == "relevant"


def evaluate_retrieval_correctness(question: str, contexts: List[str]) -> bool:
    result = llm_judge(
        question=question,
        answer=None,
        contexts=contexts,
        template=RETRIEVAL_CORRECTNESS_LLM_JUDGE_PROMPT,
        rails=["correct", "incorrect"],
    )
    return result["label"].lower() == "correct"


def evaluate_answer_grounding(question: str, contexts: List[str], answer: str) -> bool:
    result = llm_judge(
        question=question,
        answer=answer,
        contexts=contexts,
        template=ANSWER_GROUNDING_LLM_JUDGE_PROMPT,
        rails=["grounded", "not_grounded"],
    )
    return result["label"].lower() == "grounded"


def evaluate_answer_accuracy(question: str, contexts: List[str], answer: str) -> bool:
    result = llm_judge(
        question=question,
        answer=answer,
        contexts=contexts,
        template=ANSWER_ACCURACY_LLM_JUDGE_PROMPT,
        rails=["accurate", "inaccurate"],
    )
    return result["label"].lower() == "accurate"


# Backwards-compatible signature retained
def evaluate_clarity(output: Any, input: Any) -> bool:
    if output is None:
        return False
    question = None
    #question key is important as it is used to get the question from the input
    try:
        question = (input or {}).get("question")
    except Exception:
        question = None
    # Try multiple keys for answer to be robust
    candidate_answer = None
    for key in ("final_output", "answer", "response", "output"):
        try:
            candidate_answer = (output or {}).get(key)
        except Exception:
            candidate_answer = None
        if candidate_answer:
            break

        
    result = llm_judge(
        question=question,
        answer=(candidate_answer or ""),
        contexts=None,
        template=CLARITY_LLM_JUDGE_PROMPT,
        rails=["clear", "unclear"],
    )
    return result["label"].lower() == "clear"