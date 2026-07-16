from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# grab database connection url from .env file
DATABASE_URL = os.environ.get("DATABASE_PUBLIC_URL")

# create_engine = connects python to postgresql using the url
engine = create_engine(DATABASE_URL)

# sessionmaker = factory that creates db sessions (one session = one request's db work)
SessionLocal = sessionmaker(bind=engine)

# Base = parent class all models inherit from — tells sqlalchemy these are db tables
Base = declarative_base()

# users table — one row per registered user
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)   # auto incrementing unique id
    username = Column(String, unique=True)    # no two users same username
    email = Column(String, unique=True)       # no two users same email
    password = Column(String)                 # bcrypt hashed password stored here

# chat_history table — one row per question asked
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)      # which user asked this — links to users.id
    session_id = Column(String)    # which pdf session this belongs to
    question = Column(Text)        # the question user asked
    answer = Column(Text)          # the answer llm gave
    pdf_name = Column(String)      # which pdf was uploaded
    timestamp = Column(DateTime, default=datetime.now) # when it was asked

# create_all = creates these tables in postgresql if they don't exist yet
Base.metadata.create_all(engine)