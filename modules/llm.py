import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.retrievers import EnsembleRetriever
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEYS")

def format_docs_with_sources(docs):
    # docs = list of chunks retrieved from chromadb
    # we format each chunk with its page number and join them into one string
    formatted = []
    sources = []
    for doc in docs:
        formatted.append(doc.page_content)
        page = doc.metadata.get("page", "unknown")
        sources.append(f"Page {page}")
    return "\n\n".join(formatted) + f"\n\n[Sources: {', '.join(sources)}]"

def rerank_docs(question, docs, top_n=3):
    pairs = [(question, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(scores, docs), reverse=True)
    return [doc for _, doc in ranked[:top_n]]

def get_llm_chain(vectorstore, bm25_retriever, chat_history: list = []):
    
    
    # step 1: create the LLM
    llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile", streaming=True)
    
    # step 2: create retriever — searches chromadb and returns top 3 relevant chunks
    chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.5, 0.5]
    )

    # step 3: build the prompt
    # *[(msg.type, msg.content) for msg in chat_history] = unpack past messages into prompt
    # msg.type = "human" or "ai", msg.content = the actual message text
    # this is how memory gets injected — LLM sees full past conversation before answering
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Answer based on the context below. Cite page numbers inline like: 'The policy states X (Page 4)'. At the end, also write 'Sources: Page X, Page Y' listing all pages used.\n\nContext:\n{context}"),
       *[(msg["role"], msg["content"]) for msg in chat_history],  # past messages go here
        ("human", "{question}"),  # current question goes here
    ])

    # step 4: build the chain using | (pipe operator — data flows left to right)
    # RunnableLambda(lambda x: x["question"]) = extract just the question string from input dict
    # because input comes as {"question": "..."} but retriever needs plain string
    chain = (
        {
            "context": RunnableLambda(lambda x: rerank_docs(x["question"], ensemble_retriever.invoke(x["question"]))) | format_docs_with_sources,
            "question": RunnableLambda(lambda x: x["question"])
        }
        | prompt      # inject context + history + question into prompt template
        | llm         # send filled prompt to Groq LLM
        | StrOutputParser()  # convert LLM response object to plain string
    )

    return chain