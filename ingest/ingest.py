import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def ingest():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(base_dir, "..", "data", "manifesto.pdf"))
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # Initialize Azure embeddings using deployment + azure_endpoint (no base URL)
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_ENDPOINT")
    if not azure_endpoint:
        raise EnvironmentError("Missing AZURE_OPENAI_ENDPOINT (or AZURE_ENDPOINT) in environment or .env")

    deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT") or "text-embedding-3-large"
    embeddings = AzureOpenAIEmbeddings(
        deployment=deployment,
        azure_endpoint=azure_endpoint,
    )
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_store")
    #vectordb.persist()
    print("✅ Ingestion completed.")

if __name__ == "__main__":
    ingest()
