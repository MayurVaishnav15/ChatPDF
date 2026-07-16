import streamlit as st
import requests
import os

# fastapi backend url
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="ChatPDF", page_icon="📂", layout="wide")

# session state = variables that stay alive across reruns
# streamlit reruns the whole script on every interaction, so we store data here
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── LOGIN / REGISTER PAGE ───────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.title("🤖 PDF AI Chat")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            # calls FastAPI POST /login
            res = requests.post(f"{API_URL}/login", params={"email": email, "password": password})
            if res.status_code == 200:
                st.session_state.logged_in = True
                st.session_state.user_id = res.json()["user_id"]
                st.session_state.username = res.json()["username"]
                st.rerun()  # reload page to show chat UI
            else:
                st.error("Invalid email or password")

    with tab2:
        username = st.text_input("Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            # calls FastAPI POST /register
            res = requests.post(f"{API_URL}/register", params={"username": username, "email": email, "password": password})
            if res.status_code == 200:
                st.success(res.json().get("message", "Registered! Please login."))
            else:
                st.error(res.json().get("detail", "Registration failed"))

# ─── MAIN CHAT PAGE ──────────────────────────────────────────────────────────
else:
    with st.sidebar:
        st.markdown(f"👋Welcome **{st.session_state.username.title()}**")
        st.markdown("---")

        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_file and st.session_state.session_id is None:
            with st.spinner("Processing PDF..."):
                # calls FastAPI POST /upload — returns session_id
                res = requests.post(f"{API_URL}/upload", files={"file": (uploaded_file.name, uploaded_file, "application/pdf")})
                if res.status_code == 200:
                    st.session_state.session_id = res.json()["session_id"]
                    st.session_state.messages = []
                    st.success("PDF ready!")

        if st.button("➕ New Chat"):
            st.session_state.session_id = None
            st.session_state.messages = [] 
            st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

    st.title("Chat with your PDF")

    if not st.session_state.session_id:
        st.info("👈 Upload a PDF from the sidebar to start chatting.")
    else:
        # show chat messages
        for msg in st.session_state.messages:
            role = "👤" if msg["role"] == "user" else "🤖"
            st.chat_message(role).write(msg["content"])

        question = st.chat_input("Ask something about your PDF...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Thinking..."):
                # calls FastAPI POST /chat-save — saves to postgresql + returns answer
                res = requests.post(
                    f"{API_URL}/chat-save",
                    params={"user_id": st.session_state.user_id},
                    json={"session_id": st.session_state.session_id, "question": question}
                )
                if res.status_code == 200:
                    answer = res.json()["answer"]
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.rerun()
                else:
                   st.error(res.json())