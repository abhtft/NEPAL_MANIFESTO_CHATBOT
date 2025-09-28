import os  
from langchain_community.document_loaders import PyPDFLoader  
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain_community.vectorstores import Chroma  
from langchain_openai import AzureOpenAIEmbeddings  
from langchain.docstore.document import Document  
from dotenv import load_dotenv  


import shutil  
import os  

def clear_chroma_store(directory="chroma_store"):  
    if os.path.exists(directory):  
        shutil.rmtree(directory)  

  
# Load .env file  
load_dotenv()  
  
def ingest():  
    # Fixed file name  
    base_dir = os.path.dirname(os.path.abspath(__file__))  
    pdf_path = os.path.normpath(os.path.join(base_dir, "..", "data", "manifesto.pdf"))  
    loader = PyPDFLoader(pdf_path)  
    docs = loader.load()  
  
    # Chunking  
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)  
    chunks_split = splitter.split_documents(docs)  
  
    # Add IDs to metadata  
    chunks = []  
    #each element is an dictionary

    for i, chunk in enumerate(chunks_split):  
        doc_id = (i+1)
        # Add id to metadata  
        #overwritting null values
        chunk.metadata["id"] = doc_id  
       
        chunks.append(chunk)  

    print(doc_id)
  
    # Azure OpenAI Embeddings setup  
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_ENDPOINT")  
    if not azure_endpoint:  
        raise EnvironmentError("Missing AZURE_OPENAI_ENDPOINT (or AZURE_ENDPOINT) in environment or .env")  
    deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT") or "text-embedding-3-large"  
  
    embeddings = AzureOpenAIEmbeddings(  
        deployment=deployment,  
        azure_endpoint=azure_endpoint,  
    )  
  
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_store")  
    print("✅ Ingestion completed.")  
  
if __name__ == "__main__":  
    clear_chroma_store()  
    ingest()  


# Excellent question!
# Yes, all document splitters in LangChain (such as RecursiveCharacterTextSplitter, CharacterTextSplitter, TokenTextSplitter, MarkdownHeaderTextSplitter, etc.) follow the same trend:

# Input: They take a list of Document objects (or sometimes just strings, which are wrapped into Document objects).
# Output: They return a list of new Document objects.
# Each output Document has a .page_content attribute (the chunked text).
# Each output Document has a .metadata attribute (a Python dictionary).
# Metadata Handling:
# The splitters preserve and/or update the original metadata.
# For example, if your input document had {"source": "myfile.txt", "page": 5}, the resulting chunks will usually carry this metadata, perhaps with added fields (like a chunk index).


# Summary Table
# Splitter Class	Output Type	Metadata Handling
# RecursiveCharacterTextSplitter	List of Documents	Preserved/augmented
# CharacterTextSplitter	List of Documents	Preserved/augmented
# TokenTextSplitter	List of Documents	Preserved/augmented
# MarkdownHeaderTextSplitter	List of Documents	Preserved/augmented (+header info)
