##############
#Evaluation prompts#########################

#########################################################
#1.clarity evaluator prompt
CLARITY_LLM_JUDGE_PROMPT = """
In this task, you will be presented with a question and an answer. Your objective is to evaluate the clarity 
of the answer in addressing the question. A clear answer is one that is precise, coherent, and directly 
addresses the question without introducing unnecessary complexity or ambiguity. An unclear answer is one 
that is vague, disorganized, or difficult to understand, even if it may be factually correct.

Your answer should be a single word: either "clear" or "unclear," and it should not include any other 
text or characters. "clear" indicates that the answer is well-structured, easy to understand, and 
appropriately addresses the question. "unclear" indicates that the answer is ambiguous, poorly organized, or 
not effectively communicated. Please carefully consider the question and answer before determining your 
answer.

After analyzing the question and the answer, you must write a detailed explanation of your reasoning to 
justify why you chose either "clear" or "unclear." Avoid stating the final label at the beginning of your 
explanation. Your reasoning should include specific points about how the answer does or does not meet the 
criteria for clarity.

[BEGIN DATA]
question: {question}
Answer: {answer}
[END DATA]
Please analyze the data carefully and provide an explanation followed by your answer.

EXPLANATION: Provide your reasoning step by step, evaluating the clarity of the answer based on the question.
LABEL: "clear" or "unclear"
"""
#------------------------------------------------
#2.entity correctness evaluator prompt
ENTITY_CORRECTNESS_LLM_JUDGE_PROMPT = """
In this task, you will be presented with a question and an answer. Your objective is to determine whether all 
the entities mentioned in the answer are correctly identified and accurately match those in the question. An 
entity refers to any specific person, place, organization, date, or other proper noun. Your evaluation 
should focus on whether the entities in the answer are correctly named and appropriately associated with 
the context in the question.

Your answer should be a single word: either "correct" or "incorrect," and it should not include any 
other text or characters. "correct" indicates that all entities mentioned in the answer match those in the 
question and are properly identified. "incorrect" indicates that the answer contains errors or mismatches in 
the entities referenced compared to the question.

After analyzing the question and the answer, you must write a detailed explanation of your reasoning to 
justify why you chose either "correct" or "incorrect." Avoid stating the final label at the beginning of 
your explanation. Your reasoning should include specific points about how the entities in the answer do or 
do not match the entities in the question.

[BEGIN DATA]
question: {question}
Answer: {answer}
[END DATA]
Please analyze the data carefully and provide an explanation followed by your answer.

EXPLANATION: Provide your reasoning step by step, evaluating whether the entities in the answer are 
correct and consistent with the question.
LABEL: "correct" or "incorrect"
"""

#------------------------------------------------
#3.relevance evaluator prompt
RELEVANCE_LLM_JUDGE_PROMPT = """
In this task, you will be presented with a question and an answer. Your objective is to determine whether the 
answer is relevant to the question. A relevant answer is one that directly addresses the question and provides 
information that is directly supported by the retrieved context. An irrelevant answer is one that does not 
directly address the question or does not provide information that is directly supported by the retrieved context."""






# evaluator for tool 2: data analysis
def evaluate_clarity(output: str, input: str) -> bool:
    if output is None:
        return False
    df = pd.DataFrame({"question": [input.get("question")],
                       "answer": [output.get("final_output")]})
    answer = llm_classify(
        data=df,
        template=CLARITY_LLM_JUDGE_PROMPT,
        rails=["clear", "unclear"],
        model=eval_model,
        provide_explanation=True
    )
    return answer['label'] == 'clear'