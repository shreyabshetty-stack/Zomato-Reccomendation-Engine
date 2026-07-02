# Deployment Plan: Zomato AI Restaurant Recommender

This document outlines the deployment strategy for the Zomato AI Restaurant Recommender. Since the current application is built using **Streamlit** (which runs frontend and backend statefully in a single Python process via WebSockets), we present two paths:
1. **Option A (Requested Split)**: Migrate to a split architecture—FastAPI backend on Railway and Next.js frontend on Vercel.
2. **Option B (Fast Monolithic)**: Deploy the existing unified Streamlit application directly to Railway.

---

## Architecture Comparison

| Aspect | Option A: Split (FastAPI + Next.js) | Option B: Unified Monolith (Streamlit) |
| :--- | :--- | :--- |
| **Backend Host** | **Railway** (Python FastAPI) | **Railway** (Entire App) |
| **Frontend Host** | **Vercel** (Next.js / React) | **Railway** (Streamlit serves client) |
| **Effort** | Medium (Requires code split) | Low (Deploy immediately) |
| **Scalability** | High (Stateless API + Edge cached UI) | Medium (Stateful WebSockets) |

---

## Option A: Split Architecture (Railway Backend + Vercel Frontend)

To separate the application, we extract the core engine logic into a REST API and build a modern frontend interface.

### Step 1: Backend Deployment on Railway (FastAPI)

1. **Extract API Code**: Create a `src/api.py` using FastAPI:
   ```python
   from fastapi import FastAPI, HTTPException
   from fastapi.middleware.cors import CORSMiddleware
   from src.data.preprocessor import get_catalog
   from src.engine.recommender import get_recommendations
   from src.input.validator import validate_preferences
   
   app = FastAPI()
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"], # Update to Vercel domain in production
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   
   @app.post("/recommend")
   def recommend(prefs: dict):
       # Load catalog, validate preferences, and call recommender.
       catalog = get_catalog()
       ...
       return recommendations
   ```
2. **Create Dockerfile**: Create a `Dockerfile` for Railway:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt uvicorn
   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
3. **Deploy on Railway**:
   - Link your GitHub repository to Railway.
   - Set up the environment variables:
     - `GROQ_API_KEY`: Your Groq API key.
     - `GROQ_MODEL`: `llama-3.3-70b-versatile`
   - Railway will build and deploy the container and expose a public URL (e.g. `https://zomato-backend.up.railway.app`).

### Step 2: Frontend Deployment on Vercel (Next.js)

1. **Create Next.js Project**: Build a Next.js/React app recreating the preferences panel and restaurant recommendation cards.
2. **API Integration**: Fetch recommendations from the Railway API endpoint:
   ```javascript
   const response = await fetch('https://zomato-backend.up.railway.app/recommend', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(preferences),
   });
   ```
3. **Deploy on Vercel**:
   - Link the Next.js frontend repository to Vercel.
   - Configure target backend endpoint environment variables (e.g. `NEXT_PUBLIC_API_URL`).
   - Trigger build and deploy.

---

## Option B: Monolithic Deployment on Railway (Streamlit)

If you prefer to deploy the existing codebase directly without refactoring the code into API/Frontend, you can run Streamlit directly on Railway.

### Step 1: Prepare Codebase
1. **Create a `Procfile`**: Tell Railway how to start the app:
   ```text
   web: streamlit run src/main.py --server.port $PORT --server.address 0.0.0.0
   ```
2. **Verify `requirements.txt`**: Ensure all libraries are listed (`streamlit`, `groq`, etc.).

### Step 2: Deploy to Railway
1. Go to [Railway.app](https://railway.app) and click **New Project** -> **Deploy from GitHub**.
2. Select this repository.
3. In the project **Settings**, add the following **Variables**:
   - `GROQ_API_KEY`: `your_actual_groq_key`
   - `PYTHONPATH`: `.`
4. Railway will automatically build the environment and expose a public domain.

---

## Recommendation & Verification

For rapid deployment of the current code, **Option B** is recommended as it preserves the existing layouts, dynamic designs, and custom styling without modification. If you intend to scale the application to handle high concurrent traffic or wish to create native mobile apps, **Option A** is the best long-term architectural pattern.
