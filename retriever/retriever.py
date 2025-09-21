from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings


import os

def get_retriever():
    embeddings = AzureOpenAIEmbeddings(
        deployment="text-embedding-3-large",
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    )

    vectordb = Chroma(
        persist_directory="chroma_store",
        embedding_function=embeddings
    )

    return vectordb.as_retriever(search_kwargs={"k": 4})
