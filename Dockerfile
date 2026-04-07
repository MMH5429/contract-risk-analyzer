FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY . .

ENV CONTRACT_DATA_PATH="/app/data"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
