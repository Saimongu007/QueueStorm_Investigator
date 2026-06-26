# Frontend Setup Guide

This guide will help you set up and run the React frontend for QueueStorm Investigator.

## Prerequisites

Before starting, ensure you have:
- **Node.js 18+** installed ([Download here](https://nodejs.org/))
- **npm** or **yarn** package manager
- **Backend API** running on `http://localhost:8000`

## Installation Steps

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

Using npm:
```bash
npm install
```

Or using yarn:
```bash
yarn install
```

This will install all required dependencies:
- React 18.2.0
- Vite (build tool)
- Axios (HTTP client)
- Lucide React (icons)

### 3. Start the Backend API

Before running the frontend, make sure the backend is running:

```bash
# In the root directory (not frontend/)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Start the Frontend Development Server

```bash
npm run dev
```

Or with yarn:
```bash
yarn dev
```

The frontend will start on `http://localhost:3000`

## Using the Application

### 1. Check Backend Status

Look at the top of the page for the health status indicator:
- ✅ **Backend Online** - API is running and accessible
- ❌ **Backend Offline** - API is not accessible
- ⏳ **Checking...** - Currently checking status

### 2. Submit a Ticket

#### Quick Test with Sample Data

Click the **"Load Sample Data"** button to populate the form with a sample ticket.

#### Manual Entry

Fill in the form fields:

**Basic Information:**
- **Ticket ID** (required): e.g., `TKT-001`
- **Complaint** (required): Describe the customer issue
- **Language**: English, Bangla, or Mixed
- **Channel**: In-App Chat, Call Center, Email, etc.
- **User Type**: Customer, Merchant, Agent, or Unknown
- **Campaign Context** (optional): e.g., "Eid cashback campaign"

**Transaction History:**
1. Click **"+ Add Transaction"**
2. Fill in transaction details:
   - Transaction ID (required)
   - Timestamp (date/time)
   - Type (transfer, payment, cash_in, etc.)
   - Amount (required)
   - Status (completed, failed, pending, reversed)
   - Counterparty (phone number or merchant/agent ID)
3. Click **"Save Transaction"**
4. Repeat to add multiple transactions

### 3. Analyze the Ticket

Click **"Analyze Ticket"** to submit to the backend API.

The system will:
- Validate your input
- Send the request to the backend
- Display the analysis results

### 4. Review Results

The results display includes:

**Key Metrics:**
- Case Type
- Severity Level (Low, Medium, High, Critical)
- Department assignment
- Evidence Verdict

**Assessment:**
- Confidence Score (percentage)
- Human Review Requirement status

**Details:**
- Relevant Transaction ID (if found)
- Agent Summary
- Recommended Next Action
- Customer Reply Draft

**Actions:**
- Copy customer reply to clipboard
- View raw JSON response

## API Proxy Configuration

The frontend uses Vite's proxy to communicate with the backend:

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

All frontend requests to `/api/*` are proxied to `http://localhost:8000/*`

## Troubleshooting

### Backend Offline Error

**Problem:** Health status shows "Backend Offline"

**Solutions:**
1. Check if backend is running: `curl http://localhost:8000/health`
2. Start the backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Check for port conflicts on 8000

### Port 3000 Already in Use

**Problem:** Frontend can't start because port 3000 is occupied

**Solution:** Change the port in `vite.config.js`:
```javascript
server: {
  port: 3001, // Use a different port
  // ... rest of config
}
```

### CORS Errors

**Problem:** Browser shows CORS-related errors

**Solution:** The Vite proxy should handle this, but if issues persist:
1. Ensure `changeOrigin: true` is set in `vite.config.js`
2. Check that the backend allows the origin in CORS settings

### Form Validation Errors

**Problem:** Can't submit the form

**Solution:**
- Ensure **Ticket ID** is filled
- Ensure **Complaint** is not empty
- Check that transaction amounts are valid numbers

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## File Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── HealthStatus.*  # Backend health monitor
│   │   ├── TicketForm.*    # Ticket submission form
│   │   └── ResultDisplay.* # Results visualization
│   ├── App.*              # Main application
│   ├── main.jsx           # Entry point
│   └── index.css          # Global styles
├── index.html             # HTML template
├── vite.config.js         # Vite configuration
└── package.json           # Dependencies
```

## Production Deployment

### 1. Build the Application

```bash
npm run build
```

This creates an optimized production bundle in `dist/`

### 2. Serve the Static Files

You can serve the `dist/` folder using:

**Option A: Simple HTTP Server**
```bash
npm run preview
```

**Option B: Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option C: Docker**
Create a `Dockerfile` in the frontend directory:
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Environment-Specific Configuration

For different environments (dev, staging, production), create `.env` files:

**.env.development:**
```env
VITE_API_URL=http://localhost:8000
```

**.env.production:**
```env
VITE_API_URL=https://api.your-domain.com
```

Update the code to use these variables:
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

## Support

For issues or questions:
1. Check backend logs: Look at the terminal running uvicorn
2. Check browser console: Press F12 and check for JavaScript errors
3. Verify API connectivity: Test `curl http://localhost:8000/health`
4. Review the backend README: `../README.md`

## Next Steps

- Customize the UI colors and branding
- Add authentication/authorization
- Implement ticket history browsing
- Add export functionality for reports
- Integrate with your existing dashboard

Enjoy using QueueStorm Investigator! 🎫✨
