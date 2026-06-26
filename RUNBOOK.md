# RUNBOOK — QueueStorm Investigator

Copy-paste commands to bring up the service locally.

## Prerequisites

- Python 3.11+
- pip

## Option A: Run Directly

```bash
# Clone the repository
git clone <repo-url>
cd queuestorm

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add GROQ_API_KEY (optional — works without it)

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Option B: Docker

```bash
# Build the image
docker build -t queuestorm .

# Run with environment file
docker run -p 8000:8000 --env-file .env queuestorm
```

## Option C: Docker Compose

```bash
docker-compose up --build
```

## Verify

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Sample ticket
curl -X POST http://localhost:8000/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "complaint": "I sent 5000 taka to a wrong number around 2pm today.",
    "language": "en",
    "channel": "in_app_chat",
    "user_type": "customer",
    "transaction_history": [{
      "transaction_id": "TXN-9101",
      "timestamp": "2026-04-14T14:08:22Z",
      "type": "transfer",
      "amount": 5000,
      "counterparty": "+8801719876543",
      "status": "completed"
    }]
  }'
```

## Run Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | No | `""` | Groq API key for LLM. System works without it. |
| `MODEL_NAME` | No | `llama-3.1-8b-instant` | Groq model name |
| `PORT` | No | `8000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level |
