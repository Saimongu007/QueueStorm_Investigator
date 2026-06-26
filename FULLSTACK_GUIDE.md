# QueueStorm Investigator - Full Stack Guide

Complete guide to running both backend and frontend together.

## 🚀 Quick Start (Recommended)

### Option 1: Docker Compose (Easiest)

Run both backend and frontend with a single command:

```bash
# Build and start both services
docker-compose -f docker-compose.fullstack.yml up --build

# Or run in detached mode (background)
docker-compose -f docker-compose.fullstack.yml up -d --build
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Stop the services:**
```bash
docker-compose -f docker-compose.fullstack.yml down
```

### Option 2: Manual Setup (Development)

#### Step 1: Start the Backend

Terminal 1:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY if available

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: http://localhost:8000

#### Step 2: Start the Frontend

Terminal 2:
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📋 Prerequisites

### For Docker Method:
- Docker 20.10+
- Docker Compose 2.0+

### For Manual Method:
- Python 3.9+
- Node.js 18+
- npm or yarn

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User's Browser                        │
│                  http://localhost:3000                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ HTTP Requests
                      │
┌─────────────────────▼───────────────────────────────────┐
│              React Frontend (Vite)                      │
│                                                          │
│  - HealthStatus: Monitor backend health                 │
│  - TicketForm: Submit tickets                           │
│  - ResultDisplay: Show analysis                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Proxy: /api/* → http://localhost:8000/*
                      │
┌─────────────────────▼───────────────────────────────────┐
│           FastAPI Backend (Python)                      │
│                                                          │
│  GET  /health          → Health check                   │
│  POST /analyze-ticket  → Ticket analysis                │
│                                                          │
│  Pipeline:                                              │
│  1. Sanitize complaint                                  │
│  2. Classify case type                                  │
│  3. Match transactions                                  │
│  4. Route to department                                 │
│  5. Generate responses (LLM/rules)                      │
│  6. Safety validation                                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ API Calls
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Groq API (Optional)                        │
│           LLM: llama-3.1-8b-instant                     │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Backend Configuration (.env)

```env
# LLM Configuration (optional - works without it)
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=llama-3.1-8b-instant

# Server Configuration
PORT=8000
LOG_LEVEL=INFO
LLM_TIMEOUT=8.0
```

### Frontend Configuration

The frontend automatically connects to the backend through Vite's proxy (see `frontend/vite.config.js`).

For production, update the proxy settings or environment variables.

## 📦 Project Structure

```
QueueStorm_Investigator/
├── app/                          # Backend Python code
│   ├── main.py                   # FastAPI application
│   ├── models.py                 # Pydantic models
│   ├── investigator.py           # Core investigation logic
│   ├── rules.py                  # Rule-based classifier
│   ├── llm.py                    # LLM integration
│   ├── safety.py                 # Safety validation
│   └── config.py                 # Settings
├── frontend/                     # Frontend React code
│   ├── src/
│   │   ├── components/
│   │   │   ├── HealthStatus.*    # Backend health monitor
│   │   │   ├── TicketForm.*      # Ticket submission form
│   │   │   └── ResultDisplay.*   # Results display
│   │   ├── App.*                 # Main app component
│   │   └── main.jsx              # Entry point
│   ├── index.html
│   ├── vite.config.js            # Vite configuration
│   ├── Dockerfile                # Frontend Docker image
│   └── nginx.conf                # Nginx configuration
├── tests/                        # Backend tests
├── Dockerfile                    # Backend Docker image
├── docker-compose.yml            # Backend only
├── docker-compose.fullstack.yml  # Full stack (both services)
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── README.md                     # Backend documentation
├── FRONTEND_SETUP.md             # Frontend setup guide
└── FULLSTACK_GUIDE.md            # This file
```

## 🧪 Testing the Full Stack

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### 2. Test Backend API Directly

```bash
curl -X POST http://localhost:8000/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-TEST-001",
    "complaint": "I sent 5000 taka to wrong number",
    "language": "en",
    "channel": "in_app_chat",
    "user_type": "customer",
    "transaction_history": [
      {
        "transaction_id": "TXN-001",
        "timestamp": "2026-06-26T14:00:00Z",
        "type": "transfer",
        "amount": 5000,
        "counterparty": "+8801712345678",
        "status": "completed"
      }
    ]
  }'
```

### 3. Test Frontend

1. Open http://localhost:3000 in your browser
2. Check that the health status shows "✅ Backend Online"
3. Click "Load Sample Data" button
4. Click "Analyze Ticket"
5. Verify results are displayed correctly

## 🐛 Troubleshooting

### Backend Issues

**Problem:** Backend won't start
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill the process if needed
kill -9 <PID>
```

**Problem:** Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Problem:** LLM timeout errors
- The system works without LLM (uses rule-based fallback)
- Check your GROQ_API_KEY is valid
- Increase LLM_TIMEOUT in .env

### Frontend Issues

**Problem:** Frontend won't start
```bash
# Remove node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem:** Backend offline in UI
1. Check backend is running: `curl http://localhost:8000/health`
2. Check Vite proxy configuration in `vite.config.js`
3. Check browser console for CORS errors

**Problem:** Build errors
```bash
# Clear cache and rebuild
cd frontend
rm -rf dist node_modules
npm install
npm run build
```

### Docker Issues

**Problem:** Docker build fails
```bash
# Clean up Docker
docker-compose -f docker-compose.fullstack.yml down -v
docker system prune -a

# Rebuild
docker-compose -f docker-compose.fullstack.yml up --build
```

**Problem:** Container networking issues
```bash
# Check containers are running
docker ps

# Check logs
docker logs queuestorm-backend
docker logs queuestorm-frontend

# Restart containers
docker-compose -f docker-compose.fullstack.yml restart
```

## 🚀 Production Deployment

### Docker Deployment

1. **Build production images:**
```bash
docker-compose -f docker-compose.fullstack.yml build
```

2. **Run in production mode:**
```bash
docker-compose -f docker-compose.fullstack.yml up -d
```

3. **Check logs:**
```bash
docker-compose -f docker-compose.fullstack.yml logs -f
```

### Manual Deployment

#### Backend:
```bash
# Use a production ASGI server
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Frontend:
```bash
cd frontend
npm run build
# Serve the dist/ folder with nginx or any static server
```

### Environment Variables for Production

Create a `.env.production`:
```env
GROQ_API_KEY=your_production_key
MODEL_NAME=llama-3.1-8b-instant
PORT=8000
LOG_LEVEL=WARNING
LLM_TIMEOUT=8.0
```

## 📊 Monitoring

### Health Checks

Backend:
```bash
curl http://localhost:8000/health
```

Frontend:
- Built-in health status indicator at top of page
- Auto-refreshes every 30 seconds

### Logs

**Docker:**
```bash
# Backend logs
docker logs queuestorm-backend -f

# Frontend logs
docker logs queuestorm-frontend -f
```

**Manual:**
- Backend: Check terminal running uvicorn
- Frontend: Check browser console (F12)

## 🔐 Security Notes

1. **Never commit `.env` files** with real API keys
2. **Use HTTPS in production** for both frontend and backend
3. **Configure CORS properly** in FastAPI if deploying to different domains
4. **Set up authentication** if exposing publicly
5. **Use environment-specific configs** for different stages

## 📈 Performance Tips

### Backend:
- Use multiple workers: `--workers 4`
- Enable response caching for repeated requests
- Monitor LLM API rate limits

### Frontend:
- Production build is optimized (minified, tree-shaken)
- Nginx serves static assets with caching
- Use CDN for static assets in production

## 🤝 Development Workflow

1. **Start both services** in development mode
2. **Make changes** to backend or frontend code
3. **Hot reload** automatically updates
   - Backend: `--reload` flag on uvicorn
   - Frontend: Vite HMR (Hot Module Replacement)
4. **Test changes** in browser
5. **Commit and push** when ready

## 📚 Additional Resources

- [Backend README](README.md) - Detailed backend documentation
- [Frontend Setup](FRONTEND_SETUP.md) - Frontend-specific guide
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)

## 🎯 Next Steps

Now that you have the full stack running:

1. ✅ Test with sample data
2. ✅ Customize the UI styling
3. ✅ Add authentication/authorization
4. ✅ Implement ticket history
5. ✅ Set up monitoring and alerting
6. ✅ Deploy to production

**Happy coding! 🎉**
