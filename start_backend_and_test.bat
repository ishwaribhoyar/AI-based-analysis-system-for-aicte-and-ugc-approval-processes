@echo off
echo ============================================================
echo Starting Backend Server and Running Comprehensive Tests
echo ============================================================

cd backend

echo.
echo [1/3] Starting backend server...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000
timeout /t 5 /nobreak >nul

echo.
echo [2/3] Waiting for server to be ready...
:wait_loop
python -c "import requests, time; [time.sleep(1) for _ in range(30) if not requests.get('http://localhost:8000/', timeout=2).status_code == 200]" 2>nul
if errorlevel 1 (
    echo Server is ready!
    goto test
)
timeout /t 1 /nobreak >nul
goto wait_loop

:test
echo.
echo [3/3] Running comprehensive tests...
python comprehensive_test.py

echo.
echo ============================================================
echo Test Complete
echo ============================================================
pause

