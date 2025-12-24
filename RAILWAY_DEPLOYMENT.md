# Railway Deployment Guide

## Prerequisites
- [Railway account](https://railway.app/)
- GitHub repository with this project

## Step 1: Deploy Backend

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Choose **only the `backend` folder** as root directory

### Backend Environment Variables (Required):
Add these in Railway project settings:

```
OPENAI_API_KEY=sk-your-openai-key
```

### Optional Environment Variables:
```
OPENAI_MODEL_PRIMARY=gpt-5-nano
OPENAI_MODEL_FALLBACK=gpt-5-mini
```

5. Wait for deployment to complete
6. Copy the **backend URL** (e.g., `https://your-backend.railway.app`)

---

## Step 2: Deploy Frontend

1. Create another new project in Railway
2. Deploy from the same GitHub repo
3. Choose **only the `frontend` folder** as root directory

### Frontend Environment Variables (Required):
Add this, replacing with your actual backend URL:

```
NEXT_PUBLIC_API_BASE=https://your-backend.railway.app/api
```

5. Wait for deployment to complete
6. Your PWA is now live!

---

## Verification

1. Visit your frontend Railway URL
2. Upload a test document
3. Check if processing completes
4. The chatbot should respond with real AI answers

---

## Troubleshooting

### Backend Health Check
Visit: `https://your-backend.railway.app/health`
Should return: `{"status": "ok"}`

### Frontend Connection
Open browser DevTools → Network tab
API calls should go to your backend URL

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS errors | Add `FRONTEND_URL=https://your-frontend.railway.app` to backend |
| 500 errors | Check Railway logs for backend errors |
| Slow first load | Railway free tier has cold starts, upgrade to paid |

---

## PWA Installation

Users can install the app:
1. Visit frontend URL in Chrome/Edge
2. Click the install icon in address bar (or 3-dot menu → Install)
3. App works offline for cached data

---

## Notes

- **SQLite**: The backend uses SQLite by default. Data persists within the container but may be lost on redeploys. For production, consider Railway PostgreSQL or MongoDB Atlas.
- **File Storage**: Uploaded files are stored in container. For production, use a cloud storage service.
- **Cold Starts**: Railway free tier has cold starts. First request after idle may take 10-30 seconds.
