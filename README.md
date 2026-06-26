# QueueStorm Investigator

AI-powered support ticket investigator for digital finance — built for the SUST CSE Carnival 2026 · bKash Codex Hackathon.

Receives customer complaints + transaction history, cross-references evidence, classifies, routes, and generates safe professional responses.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env (optional — system works without it)

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t queuestorm .
docker run -p 8000:8000 --env-file .env queuestorm
```

Or with docker-compose:
```bash
docker-compose up --build
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Returns `{"status": "ok"}` — health check |
| `POST` | `/analyze-ticket` | Analyze a support ticket, return structured verdict |

## Architecture

```
Request → FastAPI → Investigator Pipeline → Response
                        │
                        ├── 1. Sanitize complaint (injection defense)
                        ├── 2. Classify case (keyword rules engine)
                        ├── 3. Match transaction (scoring algorithm)
                        ├── 4. Route: severity + department + human review
                        ├── 5. Generate text (LLM with rule fallback)
                        ├── 6. Safety validate (regex post-check)
                        └── 7. Return TicketResponse
```

### Key Design Decision: Rules-First Hybrid

All **classification, routing, transaction matching, and evidence reasoning** is handled by deterministic rules. The LLM only generates the three text fields (`agent_summary`, `recommended_next_action`, `customer_reply`). This ensures:

- **Zero LLM-induced classification errors** — the 35% evidence reasoning score is deterministic
- **Sub-second p95 latency** when LLM is fast
- **Full functionality without LLM** — works with `GROQ_API_KEY=""` using rule-based templates

## MODELS

- **Primary:** `llama-3.1-8b-instant` via Groq API
  - **Why:** Sub-3s latency on free tier, sufficient for text generation tasks
  - **Where:** groq.com cloud inference (outbound HTTPS)
  - **Cost:** Free tier, no paid API required
- **Fallback:** Rule-based text templates (no external dependency)
  - **When:** Groq API fails, times out, returns invalid JSON, or no API key set
  - **Quality:** Produces correct, safe, professional responses for all case types

## AI Approach

1. **Rules engine** handles all deterministic decisions (classification, routing, matching, severity, evidence verdict)
2. **Transaction matching algorithm** scores each transaction against complaint signals (amount=40pts, type=25pts, time=20pts, counterparty=15pts)
3. **LLM** generates natural language text fields only, with full context from the rules engine
4. **Safety validator** runs post-generation regex checks on every response

This hybrid approach ensures: fast p95 latency, zero LLM-induced classification errors, and hard safety guarantees.

## Safety Logic

Four layers of defense:

1. **LLM system prompt** contains explicit NEVER rules for credentials, refunds, third-party contact
2. **Prompt injection sanitizer** detects adversarial instructions in complaint text and replaces with safe placeholder
3. **Post-generation regex validator** checks `customer_reply` and `recommended_next_action` for forbidden patterns
4. **Hardcoded safe fallback** replaces any field that fails validation

### Safety Rules Enforced

| Rule | Enforcement |
|------|-------------|
| Never ask for PIN, OTP, password | System prompt + **allowlist-inversion** validator: any credential mention is flagged *unless* it appears in a warning context ("do not share", "never ask for"), evaluated per sentence so a request can't hide behind a warning |
| Never confirm refund/reversal | System prompt + regex validator on both customer_reply and recommended_next_action |
| Never direct to third party | System prompt + regex validator |
| Ignore injected instructions | Injection sanitizer + complaint-as-data system prompt instruction |

Input handling: unknown values for optional enum fields (`language`, `channel`, `user_type`) are coerced to `None` rather than rejected, so a slightly-off optional field never fails the whole ticket. Required fields (`ticket_id`, `complaint`) stay strict.

## Known Limitations

- **Bangla NLP:** Keyword-based, not morphologically aware. May miss inflected Bangla words.
- **Transaction matching:** Relies on amount + type + time + counterparty signals; no ML embeddings or semantic similarity.
- **Groq free tier:** Has rate limits; sustained high load may hit quota and trigger fallback to templates.
- **Time signal matching:** Uses relative keywords ("today", "yesterday") without absolute date resolution against transaction timestamps.
- **Template text quality:** Rule-based fallback text is functional but less natural than LLM-generated text.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_health.py -v
pytest tests/test_safety.py -v
pytest tests/test_sample_cases.py -v
pytest tests/test_edge_cases.py -v
```

## Project Structure

```
├── app/
│   ├── main.py           # FastAPI app, endpoints, error handlers
│   ├── models.py          # Pydantic models and enums
│   ├── investigator.py    # Core investigation pipeline
│   ├── rules.py           # Rule-based classifier and text generator
│   ├── llm.py             # Groq LLM integration
│   ├── safety.py          # Safety validator and injection defense
│   └── config.py          # Settings from .env
├── tests/                 # Comprehensive test suite
├── Dockerfile             # Production Docker image
├── docker-compose.yml     # Docker Compose config
├── railway.json           # Railway deployment config
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── sample_output.json     # Sample output for SAMPLE-01
└── RUNBOOK.md             # Copy-paste local run commands
```

## Sample Request

```bash
curl -X POST http://localhost:8000/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "complaint": "I sent 5000 taka to a wrong number around 2pm today.",
    "language": "en",
    "channel": "in_app_chat",
    "user_type": "customer",
    "transaction_history": [
      {
        "transaction_id": "TXN-9101",
        "timestamp": "2026-04-14T14:08:22Z",
        "type": "transfer",
        "amount": 5000,
        "counterparty": "+8801719876543",
        "status": "completed"
      }
    ]
  }'
```
