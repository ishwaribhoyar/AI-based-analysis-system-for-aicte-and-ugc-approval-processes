"""
Quick script to check if backend is running and start it if needed
"""
import requests
import subprocess
import sys
import time
import os

BACKEND_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running!")
            print(f"   Status: {response.json()}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def start_backend():
    """Start the backend server"""
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    print(f"🚀 Starting backend server...")
    print(f"   Directory: {backend_dir}")
    print(f"   URL: {BACKEND_URL}")
    print()
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Start uvicorn
    try:
        import uvicorn
        from main import app
        print("✅ Dependencies available, starting server...")
        print("   Press Ctrl+C to stop the server")
        print()
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        start_backend()
    else:
        if check_backend():
            print("\n✅ Backend is ready!")
            print(f"   Frontend can connect to: {BACKEND_URL}/api")
        else:
            print("\n⚠️  Backend is not running")
            print("   To start it, run:")
            print("   python check_backend.py start")
            print("   OR")
            print("   cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
