# Quick Start Guide

## 🚀 Get Running in 30 Seconds

### One-Command Start (Recommended)

**Mac/Linux:**
```bash
./start-dev.sh
```

**Windows:**
```batch
start-dev.bat
```

### Docker Start
```bash
docker-compose -f docker-compose.fullstack.yml up --build
```

## 📍 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 Quick Test

1. Open http://localhost:3000
2. Click **"Load Sample Data"**
3. Click **"Analyze Ticket"**
4. View results!

## 📋 Manual Setup (If Scripts Don't Work)

### Terminal 1: Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🛠️ Prerequisites

### For Scripts:
- Python 3.9+
- Node.js 18+

### For Docker:
- Docker 20.10+
- Docker Compose 2.0+

## ⚙️ Environment Setup

```bash
cp .env.example .env
# Edit .env and add GROQ_API_KEY (optional)
```

## 📚 Documentation

- **Full Stack**: [FULLSTACK_GUIDE.md](FULLSTACK_GUIDE.md)
- **Frontend**: [FRONTEND_SETUP.md](FRONTEND_SETUP.md)
- **Backend**: [README.md](README.md)
- **Summary**: [FRONTEND_INTEGRATION_SUMMARY.md](FRONTEND_INTEGRATION_SUMMARY.md)

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check port availability
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill existing process
kill -9 <PID>  # Mac/Linux
taskkill /F /PID <PID>  # Windows
```

### Frontend Won't Start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Health Check Shows Offline
```bash
# Test backend directly
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

## 🎨 Key Features

✅ Real-time backend health monitoring  
✅ Interactive ticket submission form  
✅ Transaction history management  
✅ Comprehensive results visualization  
✅ Sample data for quick testing  
✅ Responsive mobile-friendly design  

## 🎓 Next Steps

1. ✅ Test with sample data
2. ✅ Try your own tickets
3. ✅ Customize the UI
4. ✅ Read full documentation
5. ✅ Deploy to production

## 📞 Need Help?

See **Troubleshooting** section in [FULLSTACK_GUIDE.md](FULLSTACK_GUIDE.md)

---

**That's it! You're ready to go! 🎉**
