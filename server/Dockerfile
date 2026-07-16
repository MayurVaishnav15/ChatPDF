FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install -r requirements.txt
COPY modules/ ./modules/
COPY server/ ./server/
WORKDIR /app/server
CMD uvicorn main:app --host 0.0.0.0 --port $PORT