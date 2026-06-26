# QueueStorm Investigator - Full Stack Application

<div align="center">

## 🎫 AI-Powered Support Ticket Investigator

**FastAPI Backend + React Frontend**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

</div>

---

## 🌟 Overview

QueueStorm Investigator is a complete full-stack application for analyzing digital finance support tickets. It uses AI-powered investigation with rule-based classification to provide instant ticket analysis, evidence verification, and customer response generation.

### Key Features

- 🤖 **AI-Powered Analysis** - LLM + rule-based hybrid system
- 📊 **Evidence Matching** - Automatic transaction correlation
- 🎯 **Smart Routing** - Department and severity classification
- 🔒 **Safety First** - Multi-layer safety validation
- 📱 **Modern UI** - React-based responsive interface
- ⚡ **Fast Performance** - Sub-second p95 latency
- 🐳 **Docker Ready** - One-command deployment

## 🚀 Quick Start

### Option 1: One-Command Start (Easiest)

**Mac/Linux:**
```bash
./start-dev.sh
```

**Windows:**
```batch
start-dev.bat
```

### Option 2: Docker
```bash
docker-compose -f docker-compose.fullstack.yml up --build
```

### Access the Application
- **Frontend**: http://localhost:3000 ← **Start here!**
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📸 Screenshots

### Ticket Submission Form
Modern, intuitive form with transaction history management and sample data loading.

### Analysis Results
Comprehensive visualization with confidence scores, evidence verdicts, and actionable recommendations.

### Health Monitoring
Real-time backend status monitoring with automatic health checks.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│          React Frontend (Port 3000)             │
│  • HealthStatus - Backend monitoring            │
│  • TicketForm - Ticket submission               │
│  • ResultDisplay - Analysis visualization       │
└──────────────────────┬──────────────────────────┘
                       │ HTTP/REST API
                       │ Vite Proxy (dev)
┌──────────────────────▼──────────────────────────┐
│         FastAPI Backend (Port 8000)             │
│  • GET  /health - Health check                  │
│  • POST /analyze-ticket - Ticket analysis       │
│                                                  │
│  Investigation Pipeline:                        │
│  1. Sanitize complaint                          │
│  2. Classify case type                          │
│  3. Match transactions                          │
│  4. Route to department                         │
│  5. Generate responses (LLM/rules)              │
│  6. Safety validation                           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│         Groq API (Optional)                     │
│    LLM: llama-3.1-8b-instant                    │
└─────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
QueueStorm_Investigator/
├── app/                          # Backend (Python/FastAPI)
│   ├── main.py                   # API endpoints
│   ├── models.py                 # Pydantic models
│   ├── investigator.py           # Investigation pipeline
│   ├── rules.py                  # Classification engine
│   ├── llm.py                    # LLM integration
│   ├── safety.py                 # Safety validation
│   └── config.py                 # Configuration
│
├── frontend/                     # Frontend (React/Vite)
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── HealthStatus.*    # Backend health
│   │   │   ├── TicketForm.*      # Ticket form
│   │   │   └── ResultDisplay.*   # Results view
│   │   ├── App.*                 # Main app
│   │   └── main.jsx              # Entry point
│   ├── vite.config.js            # Vite + proxy config
│   ├── Dockerfile                # Frontend Docker
│   └── nginx.conf                # Nginx config
│
├── tests/                        # Backend tests
├── Dockerfile                    # Backend Docker
├── docker-compose.fullstack.yml  # Full stack
├── start-dev.sh                  # Dev startup (Unix)
├── start-dev.bat                 # Dev startup (Windows)
├── requirements.txt              # Python deps
├── .env                          # Environment vars
│
└── Documentation/
    ├── README.md                 # Backend docs
    ├── frontend/README.md        # Frontend docs
    ├── QUICK_START.md            # Quick reference
    ├── FRONTEND_SETUP.md         # Frontend setup
    ├── FULLSTACK_GUIDE.md        # Complete guide
    └── FRONTEND_INTEGRATION_SUMMARY.md
```

## 🎯 Core Capabilities

### Backend API

#### POST /analyze-ticket
Analyzes support tickets with:
- **Classification**: 8 case types (wrong transfer, payment failed, etc.)
- **Evidence Matching**: Automatic transaction correlation with scoring
- **Routing**: Department assignment and severity classification
- **Response Generation**: Agent summaries and customer replies
- **Safety**: Multi-layer validation against credential leaks

#### GET /health
Health check endpoint for monitoring.

### Frontend Interface

#### Ticket Form
- All ticket fields with validation
- Transaction history management
- Sample data loader for testing
- Responsive mobile-friendly design

#### Results Display
- Key metrics (case type, severity, department)
- Confidence score visualization
- Evidence verdict
- Agent summary
- Recommended actions
- Customer reply draft with copy button
- Reason codes

#### Health Monitoring
- Real-time backend status
- Auto-refresh every 30 seconds
- Visual indicators

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.100+
- **Language**: Python 3.9+
- **LLM**: Groq API (llama-3.1-8b-instant)
- **Server**: Uvicorn (dev) / Gunicorn (prod)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: CSS Modules
- **HTTP**: Fetch API

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Web Server**: Nginx (production)
- **Proxy**: Vite proxy (development)

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START.md](QUICK_START.md) | Get running in 30 seconds |
| [FULLSTACK_GUIDE.md](FULLSTACK_GUIDE.md) | Complete setup and deployment guide |
| [FRONTEND_SETUP.md](FRONTEND_SETUP.md) | Frontend-specific setup |
| [FRONTEND_INTEGRATION_SUMMARY.md](FRONTEND_INTEGRATION_SUMMARY.md) | Integration overview |
| [README.md](README.md) | Backend API documentation |
| [frontend/README.md](frontend/README.md) | Frontend details |

## ⚙️ Configuration

### Environment Variables (.env)

```env
# LLM Configuration (optional)
GROQ_API_KEY=your_api_key_here
MODEL_NAME=llama-3.1-8b-instant

# Server Configuration
PORT=8000
LOG_LEVEL=INFO
LLM_TIMEOUT=8.0
```

### Proxy Configuration (Development)

Frontend automatically proxies `/api/*` to `http://localhost:8000/*` via Vite.

## 🧪 Testing

### Quick Test
1. Open http://localhost:3000
2. Click "Load Sample Data"
3. Click "Analyze Ticket"
4. View results

### Backend Tests
```bash
pytest tests/ -v
```

### Manual API Test
```bash
curl -X POST http://localhost:8000/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "complaint": "I sent 5000 taka to wrong number",
    "transaction_history": [...]
  }'
```

## 🐳 Docker Deployment

### Full Stack
```bash
# Build and start
docker-compose -f docker-compose.fullstack.yml up --build

# Background mode
docker-compose -f docker-compose.fullstack.yml up -d

# View logs
docker-compose -f docker-compose.fullstack.yml logs -f

# Stop
docker-compose -f docker-compose.fullstack.yml down
```

### Individual Services

**Backend only:**
```bash
docker-compose up --build
```

**Frontend only:**
```bash
cd frontend
docker build -t queuestorm-frontend .
docker run -p 3000:80 queuestorm-frontend
```

## 🔧 Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Setup

**Backend:**
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🚢 Production Deployment

### Build

**Backend:**
```bash
docker build -t queuestorm-backend .
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve dist/ folder with nginx or static server
```

### Run
```bash
docker-compose -f docker-compose.fullstack.yml up -d
```

### Environment
- Set production `GROQ_API_KEY`
- Configure HTTPS/SSL
- Set up reverse proxy (nginx)
- Enable monitoring and logging

## 🔒 Security

- ✅ Input sanitization
- ✅ Prompt injection defense
- ✅ Safety validation
- ✅ No credential exposure
- ✅ CORS handling
- ⚠️ Add authentication for production
- ⚠️ Use HTTPS in production

## 📊 Performance

- **P95 Latency**: <5 seconds
- **LLM Timeout**: 8 seconds
- **Backend**: Sub-second (without LLM)
- **Frontend**: Optimized React build

## 🐛 Troubleshooting

### Backend Offline
```bash
# Check backend
curl http://localhost:8000/health

# Restart backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### Frontend Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

See [FULLSTACK_GUIDE.md](FULLSTACK_GUIDE.md) for more troubleshooting.

## 🤝 Contributing

1. Backend changes: Update `app/` directory
2. Frontend changes: Update `frontend/src/` directory
3. Run tests before committing
4. Update relevant documentation

## 📄 License

See LICENSE file for details.

## 🎓 Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Docker Documentation](https://docs.docker.com/)

## 🙏 Acknowledgments

Built for SUST CSE Carnival 2026 · bKash Codex Hackathon

## 📞 Support

For issues and questions:
1. Check documentation in this repository
2. Review troubleshooting guides
3. Check backend logs: `logs/backend.log`
4. Check frontend console (F12 in browser)

---

<div align="center">

**Made with ❤️ for Digital Finance**

[Get Started](QUICK_START.md) · [Full Guide](FULLSTACK_GUIDE.md) · [API Docs](http://localhost:8000/docs)

</div>
