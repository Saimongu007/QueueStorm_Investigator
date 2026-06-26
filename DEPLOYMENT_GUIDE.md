# Full-Stack Deployment Guide (Render + Vercel)

This guide walks you through deploying the **FastAPI backend on Render** and the **React frontend on Vercel**.

---

## Part 1: Deploying the Backend on Render

Render is an excellent platform for hosting Python/FastAPI backends. It natively supports Python environments and Docker.

### 1. Preparation
1. Ensure your code is pushed to your GitHub repository (e.g., `main` branch).
2. Go to [Render.com](https://render.com/) and create an account or sign in.

### 2. Create the Web Service
1. In the Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub account (if not already done) and select the `QueueStorm_Investigator` repository.
3. Configure the service:
   - **Name:** `queuestorm-api` (or any preferred name)
   - **Region:** Choose the one closest to your users.
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   
   *(Note: Render automatically injects the `$PORT` environment variable).*

### 3. Environment Variables
1. Scroll down to **Environment Variables** and add the following:
   - `GROQ_API_KEY`: `your_groq_api_key` (Required for LLM features)
   - `PYTHON_VERSION`: `3.10.0` (Recommended to ensure compatibility)
2. Click **Create Web Service**.

### 4. Verification
1. Wait for the build and deployment to complete (usually 2-3 minutes).
2. Once deployed, you will get a URL like `https://queuestorm-api.onrender.com`.
3. Open `https://queuestorm-api.onrender.com/health` in your browser. You should see `{"status": "ok"}`.
4. **Copy this URL**, you will need it for the frontend deployment.

---

## Part 2: Deploying the Frontend on Vercel

Vercel is optimized for React/Vite applications and provides a global CDN.

### 1. Update `vercel.json` (Proxy Configuration)
Since the frontend code fetches API endpoints via relative paths (e.g., `/api/health`), we use a `vercel.json` file to proxy these requests to Render, avoiding CORS issues completely.

In your repository, open `frontend/vercel.json` and replace `YOUR_RENDER_BACKEND_URL` with your actual Render URL (without a trailing slash):

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://queuestorm-api.onrender.com/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

*Commit and push this change to GitHub before proceeding.*

### 2. Create the Vercel Project
1. Go to [Vercel.com](https://vercel.com/) and sign in.
2. Click **Add New** -> **Project**.
3. Import your GitHub repository (`QueueStorm_Investigator`).

### 3. Configure the Build
1. In the **Configure Project** screen, set the **Framework Preset** to `Vite`.
2. Open the **Root Directory** section, click **Edit**, and select the `frontend` folder (this is crucial since your React code is inside the `frontend` subdirectory).
3. The Build Command should automatically be `npm run build` and Output Directory `dist`.
4. Click **Deploy**.

### 4. Verification
1. Wait for Vercel to build and deploy the app (usually < 1 minute).
2. Click on the generated dashboard URL (e.g., `https://queuestorm-investigator.vercel.app`).
3. Check the **Health Status** indicator on the page. If it turns green, your frontend is successfully communicating with your Render backend!

---

## Summary Checklist
- [x] Push code to GitHub
- [x] Create Web Service on Render (Python 3, Uvicorn start command)
- [x] Add `GROQ_API_KEY` to Render Environment Variables
- [x] Update `frontend/vercel.json` with Render backend URL
- [x] Import repository into Vercel
- [x] Set Vercel Root Directory to `frontend/`
- [x] Deploy and verify!
