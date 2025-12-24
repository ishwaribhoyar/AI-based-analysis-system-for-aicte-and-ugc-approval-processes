# Backend Server Verification Guide

## Quick Start

### Option 1: Use PowerShell Script (Recommended)
```powershell
.\start_backend.ps1
```

### Option 2: Manual Start
```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Option 3: Use Batch File
```cmd
cd backend
.\start_server.bat
```

## Verify Server is Running

### Check 1: Port Listening
```powershell
netstat -ano | findstr :8000
```
You should see output showing port 8000 is in LISTENING state.

### Check 2: Health Endpoint
```powershell
curl http://127.0.0.1:8000/api/health
```
Or in PowerShell:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing
```

Expected response:
```json
{"status": "healthy"}
```

### Check 3: Root Endpoint
```powershell
curl http://127.0.0.1:8000/
```

Expected response:
```json
{
  "message": "Smart Approval AI API",
  "version": "2.0.0",
  "status": "operational",
  "architecture": "Information Block Architecture - SQLite Temporary Storage"
}
```

## Troubleshooting

### Server Won't Start

1. **Check Python is installed:**
   ```powershell
   python --version
   ```
   Should be Python 3.11+

2. **Check dependencies:**
   ```powershell
   cd backend
   pip list | findstr uvicorn
   ```
   If not found:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Check for port conflicts:**
   ```powershell
   netstat -ano | findstr :8000
   ```
   If port is in use, either:
   - Stop the process using port 8000
   - Change the port in `main.py` and `frontend/lib/api.ts`

### Server Starts But Frontend Can't Connect

1. **Verify CORS is enabled** (should be in `backend/main.py`):
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       ...
   )
   ```

2. **Check firewall** - Windows Firewall might be blocking connections

3. **Verify API base URL** in `frontend/lib/api.ts`:
   ```typescript
   const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api';
   ```

4. **Check browser console** for CORS errors

### Common Errors

- **ModuleNotFoundError**: Install missing dependencies with `pip install -r requirements.txt`
- **Port already in use**: Kill the process or change port
- **Permission denied**: Run as administrator or check file permissions
- **Database error**: Ensure `backend/storage/db/` directory exists and is writable

## Server Logs

When running, you should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Next Steps

Once the server is running:
1. Open frontend in browser (usually http://localhost:3000)
2. Try creating a batch
3. Check browser console for any errors
4. Check backend terminal for request logs
