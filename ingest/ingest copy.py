import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
#many lib benifit is small size
from langchain.docstore.document import Document 

from dotenv import load_dotenv
#this is used to load the environment variables
# Load .env file
load_dotenv()

def ingest():
    #curren tfixed file name
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(base_dir, "..", "data", "manifesto.pdf"))
    loader = PyPDFLoader(pdf_path)#pdf file loading to text form
    docs = loader.load()

    #chunking approach
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    #first token ways ,if not available then char based splitting

    #It tries to split the text recursively using a list of separators in order. By default, this list is: ['\n\n', '\n', ' ', ''].
    #only paragraph splitting :after sepe ,split by token limit>par>line>word>char

    #     Parameters
    # chunk_size: Maximum size of each chunk (in characters or tokens).

    # chunk_overlap: Number of characters or tokens to overlap between chunks for context.

    # length_function: Function to measure size, commonly len for characters.

    # separators: List of separators to recursively split on.

    # keep_separator: Whether to keep the separator character in the chunks.

    # # is_separator_regex: Whether separators are regex patterns.

    #by default it is in char but also respect token limit

    chunks_split = splitter.split_documents(docs)


   
  
    chunks = []  
    for i, chunk_text in enumerate(chunks_split):  
        doc_id = (i+1)
        # Add id to metadata as well  
        chunks.append(  
            Document(  
                page_content=chunk_text,  
                metadata={"id": doc_id, "source": "manifesto.pdf"}  
            )  
        )  



    # Initialize Azure embeddings using deployment + azure_endpoint (no base URL)
#not
    #embedding model

    ###############################33

# Yes, concluding correctly:

# The RecursiveCharacterTextSplitter splits text by characters by default, measuring chunks by the number of characters corresponding to the provided chunk_size.

# However, if you want it to split by tokens instead of characters, you need to explicitly provide the length_function argument that counts tokens (using a tokenizer like from HuggingFace or tiktoken). Only then will the splitter manage chunk sizes based on the number of tokens.





    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_ENDPOINT")
    if not azure_endpoint:
        raise EnvironmentError("Missing AZURE_OPENAI_ENDPOINT (or AZURE_ENDPOINT) in environment or .env")

    deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT") or "text-embedding-3-large"

    #chunks are embedded to vector form
    embeddings = AzureOpenAIEmbeddings(
        deployment=deployment,
        azure_endpoint=azure_endpoint,
    )
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_store")
    #vectordb.persist()
    print("✅ Ingestion completed.")






if __name__ == "__main__":
    ingest()

# LangChain offers integrations with many vector stores—these are databases optimized for storing and searching vector embeddings. Some key vector stores LangChain supports include:

# Chroma (Open-source, local and cloud options)

# FAISS (Open-source, local vector similarity search)

# Pinecone (Cloud-based, free tier available, paid plans for larger scale)

# Weaviate (Open-source with cloud and free tier options)

# Milvus (Open-source, highly scalable vector database)

# Qdrant (Open-source vector search engine)

# Redis (Supports vector search as of recent versions)

# Elasticsearch (With vector search capabilities)

# MongoDB Atlas Search (Cloud managed, free tier available)

# PGVector (PostgreSQL extension, open-source)