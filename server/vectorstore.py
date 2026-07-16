import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever

def get_vectorstore(pdf_path: str):
    # step 1: load pdf — each page becomes a document object with text + page number metadata
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # step 2: split pages into smaller chunks so LLM doesn't get overwhelmed
    # chunk_size=500 = max 500 characters per chunk
    # chunk_overlap=50 = last 50 chars of chunk 1 repeat in chunk 2 so meaning doesn't cut off
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # step 3: load embedding model — converts text chunks into numbers (vectors)
    # downloads once ~90MB, cached forever after
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # step 4: store chunks + their vectors in ChromaDB (in memory, no disk)
    # from_documents = takes chunks, embeds them, stores all in one call
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    bm25_retriever = BM25Retriever.from_documents(
        documents=chunks,
        k=3)


    # step 5: return vectorstore,BM25 so llm.py can search it later
    return vectorstore,bm25_retriever