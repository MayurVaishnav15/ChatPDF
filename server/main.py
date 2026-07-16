import os
import uuid
import shutil
import bcrypt

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vectorstore import get_vectorstore
from llm import get_llm_chain
from database import SessionLocal, User, ChatHistory

from logger import log_upload, log_chat, log_auth, log_error

app = FastAPI(title="ChatPDF API")

# stores vectorstore per session_id — key: session_id, value: chromadb vectorstore
vectorstore_store = {}
bm25_store = {}
pdf_name_store = {}
memories = {}

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# shape of request body for chat endpoints
class ChatRequest(BaseModel):
    session_id: str
    question: str

# opens a fresh db connection for each request, closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# health check
@app.get("/")
def home():
    return {"message": "ChatPDF server is running"}

# accepts pdf file, saves to disk, converts to embeddings, stores in chromadb
@app.post("/upload")    
async def upload_pdf(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())  # unique id for this upload
    pdf_path = os.path.join(UPLOAD_DIR, f"{session_id}.pdf")
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)  # save uploaded file to disk
    vectorstore_store[session_id], bm25_store[session_id] = get_vectorstore(pdf_path) # embed + store in chromadb
    pdf_name_store[session_id] = file.filename
    log_upload(file.filename, session_id)
    return {"session_id": session_id, "message": "PDF uploaded and processed successfully"}


# registers new user — hashes password before saving to postgresql
@app.post("/register")
def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()  # hash password
    db.add(User(username=username, email=email, password=hashed))
    db.commit()
    log_auth("REGISTERED", email)
    return {"message": "Registered successfully"}

# login — checks email exists and password matches stored hash
@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    log_auth("LOGIN", email)
    return {"user_id": user.id, "username": user.username}

# saves question + answer to postgresql
@app.post("/chat-save")
async def chat_save(request: ChatRequest, user_id: int, db: Session = Depends(get_db)):
    if request.session_id not in vectorstore_store:
        raise HTTPException(status_code=404, detail="Session not found.")
    vectorstore = vectorstore_store[request.session_id]
    bm25_retriever = bm25_store[request.session_id]
    memory = memories.setdefault(request.session_id, [])
    chain = get_llm_chain(vectorstore, bm25_retriever, memory[-4:]) # last 2 Q&A pairs
    result = await chain.ainvoke({"question": request.question})
    log_chat(user_id, request.question)
    memory.append({"role": "human", "content": request.question})
    memory.append({"role": "ai", "content": result})

    db.add(ChatHistory(
        user_id=user_id, 
        session_id=request.session_id, 
        question=request.question, 
        answer=result,
        pdf_name=pdf_name_store.get(request.session_id, "unknown")
        ))
    db.commit()
    return {"answer": result}
