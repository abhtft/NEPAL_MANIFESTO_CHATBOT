from langchain.chains import ConversationalRetrievalChain
from langchain_openai import AzureChatOpenAI
from retriever.retriever import get_retriever
from bot.memory import get_memory
from dotenv import load_dotenv

import os

# Load .env file
load_dotenv()

def get_chain():
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        temperature=0
    )
    retriever = get_retriever()
    memory = get_memory()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer",
        #return_only_outputs=False  # Changed from "answer" to "response" to match expected output
    )
    return chain
