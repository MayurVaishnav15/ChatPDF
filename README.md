# 🤖 ChatPDF — AI-Powered PDF Chat Application

> Chat with any PDF using hybrid semantic search, cross-encoder reranking, and LLaMA 3.3 70B — with persistent memory and user authentication.

---

## ✨ Features

- 🔐 **User Authentication** — Register & login with bcrypt-hashed passwords
- 📄 **PDF Upload & Processing** — Automatic chunking and embedding on upload
- 🔍 **Hybrid Search** — BM25 keyword search + ChromaDB semantic search combined
- 🎯 **CrossEncoder Reranking** — Top results reranked for maximum relevance
- 🧠 **Sliding Window Memory** — LLM remembers last 2 Q&A pairs per session
- 📌 **Inline Citations** — Answers cite exact page numbers from your PDF
- 💾 **PostgreSQL Persistence** — Full chat history saved per user per session
- 📋 **Structured Logging** — Every request logged to terminal and file

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    streamlit_app.py                      │
│              (Frontend — Port 8501)                      │
└─────────────────┬───────────────────────────────────────┘
                  │  HTTP requests (requests.post)
                  ▼
┌─────────────────────────────────────────────────────────┐
│                      main.py                             │
│              (FastAPI Backend — Port 8000)               │
│   /register  /login  /upload  /chat-save                 │
└────┬──────────────┬──────────────┬───────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐  ┌──────────────┐  ┌──────────────────────────┐
│database │  │ vectorstore  │  │         llm.py            │
│   .py   │  │    .py       │  │                          │
│         │  │              │  │  EnsembleRetriever        │
│PostgreSQL│  │ PyPDFLoader  │  │  BM25 + ChromaDB         │
│ users   │  │ Chunking     │  │  CrossEncoder Reranker    │
│ history │  │ ChromaDB     │  │  ChatGroq (LLaMA 70B)     │
└─────────┘  │ BM25         │  │  Sliding Window Memory   │
             └──────────────┘  └──────────────────────────┘
```

### RAG Pipeline Flow

```
User Question
     │
     ▼
EnsembleRetriever (BM25 + ChromaDB)
     │
     ├── BM25 → Top 3 keyword matches
     └── ChromaDB → Top 3 semantic matches
                         │
                         ▼
              CrossEncoder Reranker
              (scores all 6, returns top 3)
                         │
                         ▼
              format_docs_with_sources
              (chunks + page citations)
                         │
                         ▼
              ChatPromptTemplate
              (system + memory + context + question)
                         │
                         ▼
              Groq API → LLaMA 3.3 70B
                         │
                         ▼
              Answer with inline page citations
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| LLM | LLaMA 3.3 70B via Groq API |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB (in-memory) |
| Keyword Search | BM25 (rank_bm25) |
| Reranker | CrossEncoder `ms-marco-MiniLM-L-6-v2` |
| Database | PostgreSQL (Railway) |
| ORM | SQLAlchemy |
| Auth | bcrypt |
| PDF Processing | PyPDF |

---

## 📁 Project Structure

```
ChatbotPdf/
├── modules/
│   ├── llm.py              # LLM chain, hybrid retrieval, reranking
│   └── vectorstore.py      # PDF loading, chunking, ChromaDB, BM25
├── server/
│   ├── main.py             # FastAPI routes
│   ├── database.py         # PostgreSQL models & connection
│   ├── logger.py           # Structured logging
│   ├── .env                # Environment variables (never pushed)
│   └── requirements.txt    # Dependencies
├── streamlit_app.py        # Streamlit frontend
├── .gitignore
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/chatpdf.git
cd chatpdf
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
cd server
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file inside `server/` — see `.env.example` for reference:
```
DATABASE_PUBLIC_URL=your_postgresql_connection_url
GROQ_API_KEYS=your_groq_api_key
```

### 5. Run FastAPI backend
```bash
cd server
uvicorn main:app
```

### 6. Run Streamlit frontend
```bash
# new terminal, from root folder
streamlit run streamlit_app.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/register` | Register new user |
| POST | `/login` | Login and get user info |
| POST | `/upload` | Upload PDF and process embeddings |
| POST | `/chat-save` | Ask question, get answer, save to DB |

Full API docs available at `http://127.0.0.1:8000/docs` (Swagger UI)

---

## 🔑 Environment Variables

See `.env.example`:
```
DATABASE_PUBLIC_URL=your_postgresql_connection_url_here
GROQ_API_KEYS=your_groq_api_key_here
API_URL=your_fastapi_deployed_url_here
```

---

## 🚀 Deployment

- **Backend + DB** — Railway
- **Frontend** — Railway

---

## 👨‍💻 Author

**Mayur** — B.Tech CSE (AI & Data Science), 2026
- GitHub: [@yourusername](https://github.com/MayurVaishnav15)
- LinkedIn: [your-linkedin](https://linkedin//)