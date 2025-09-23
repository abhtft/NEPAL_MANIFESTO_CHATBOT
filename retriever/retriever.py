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



    #general working
    # return vectordb.as_retriever(search_kwargs={"k": 4})

    # Use MMR (Maximal Marginal Relevance) to reduce duplicate/near-duplicate chunks
    return vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 4,          # maximum results
            "fetch_k": 20,   # candidate pool size for diversification
            "lambda_mult": 0.5,  # balance relevance vs. diversity
        },
    )

