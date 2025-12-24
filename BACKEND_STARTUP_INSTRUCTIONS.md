# Backend Server Startup Instructions

## ⚠️ IMPORTANT: Backend Server Must Be Running

The frontend is trying to connect to `http://127.0.0.1:8000/api` but getting `ERR_CONNECTION_REFUSED` because **the backend server is not running**.

## Quick Start (Choose One Method)

### Method 1: PowerShell Script (Easiest)
1. Open PowerShell in the project root directory
2. Run:
   ```powershell
   .\start_backend.ps1
   ```

### Method 2: Batch File
1. Open Command Prompt or PowerShell
2. Navigate to backend directory:
   ```cmd
   cd backend
   ```
3. Run:
   ```cmd
   .\start_server.bat
   ```

### Method 3: Manual Start
1. Open a new terminal/PowerShell window
2. Navigate to backend:
   ```powershell
   cd "c:\Users\datta\OneDrive\Desktop\sih 2\backend"
   ```
3. Activate virtual environment (if exists):
   ```powershell
   .\venv\Scripts\activate
   ```
4. Start the server:
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Method 4: Python Script
1. In project root, run:
   ```powershell
   python check_backend.py start
   ```

## Verify Server is Running

After starting, you should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Test the Server

Open a new terminal and run:
```powershell
curl http://127.0.0.1:8000/api/health
```

Or in PowerShell:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing
```

Expected response: `{"status": "healthy"}`

## What Was Fixed

1. ✅ **Hardcoded URL in KPIDetailsModal.tsx** - Fixed to use centralized API config
2. ✅ **Created startup scripts** - Easy ways to start the backend
3. ✅ **Verified API endpoints** - All endpoints match between frontend and backend
4. ✅ **CORS configuration** - Properly set up for development

## Current Status

- ✅ Frontend API configuration: `http://127.0.0.1:8000/api`
- ✅ Backend CORS: Allows all origins
- ✅ All API endpoints properly mapped
- ⚠️ **Backend server needs to be started manually**

## Troubleshooting

### "Module not found" errors
```powershell
cd backend
pip install -r requirements.txt
```

### Port 8000 already in use
Find and kill the process:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### Python not found
Make sure Python 3.11+ is installed and in PATH:
```powershell
python --version
```

## Next Steps

1. **Start the backend server** using one of the methods above
2. **Keep the terminal window open** (server runs in foreground)
3. **Refresh your frontend** - the connection error should be resolved
4. **Test by creating a batch** - should work now

## Important Notes

- The backend server must be running **before** using the frontend
- Keep the backend terminal window open while developing
- The `--reload` flag auto-restarts the server on code changes
- If you close the terminal, the server stops - restart it when needed

## Files Created/Modified

1. `frontend/components/KPIDetailsModal.tsx` - Fixed hardcoded URL
2. `backend/start_server.bat` - Windows batch startup script
3. `start_backend.ps1` - PowerShell startup script
4. `check_backend.py` - Python script to check/start backend
5. `test_connectivity.py` - Comprehensive connectivity test
6. `CONNECTIVITY_REPORT.md` - Full connectivity report
7. `verify_backend.md` - Verification guide

---

**Once the backend is running, refresh your frontend and try again!**
