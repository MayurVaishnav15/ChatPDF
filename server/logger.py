import logging
from datetime import datetime

# create logger
logger = logging.getLogger("ChatPDF")
logger.setLevel(logging.DEBUG)

# format: [2026-06-17 15:30:00] INFO — PDF uploaded successfully
formatter = logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# log to terminal
terminal = logging.StreamHandler()
terminal.setFormatter(formatter)

# log to file — creates chatpdf.log in same folder
file = logging.FileHandler("chatpdf.log")
file.setFormatter(formatter)

logger.addHandler(terminal)
logger.addHandler(file)


def log_request(endpoint: str, data: dict):
    logger.info(f"REQUEST  -> {endpoint} | {data}")

def log_response(endpoint: str, status: str):
    logger.info(f"RESPONSE <- {endpoint} | {status}")

def log_error(endpoint: str, error: str):
    logger.error(f"ERROR    x {endpoint} | {error}")

def log_upload(filename: str, session_id: str):
    logger.info(f"UPLOAD   ^ {filename} | session: {session_id}")

def log_chat(user_id: int, question: str):
    logger.info(f"CHAT     > user:{user_id} | question: {question[:60]}...")

def log_auth(action: str, email: str):
    logger.info(f"AUTH     * {action} | {email}")