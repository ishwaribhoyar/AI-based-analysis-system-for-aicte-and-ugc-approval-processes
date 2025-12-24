"""
Script to start backend server and run comprehensive tests
"""
import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def check_server_running():
    """Check if server is already running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the backend server"""
    if check_server_running():
        print("✅ Server already running on port 8000")
        return True
    
    print("🚀 Starting backend server...")
    # Start server in background
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Use start_server.bat if it exists, otherwise use uvicorn directly
    if Path("start_server.bat").exists():
        subprocess.Popen(["start_server.bat"], shell=True, cwd=script_dir)
    else:
        venv_python = Path("venv/Scripts/python.exe")
        if venv_python.exists():
            subprocess.Popen([
                str(venv_python), "-m", "uvicorn", 
                "main:app", "--host", "127.0.0.1", "--port", "8000"
            ], cwd=script_dir)
        else:
            subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "main:app", "--host", "127.0.0.1", "--port", "8000"
            ], cwd=script_dir)
    
    # Wait for server to start
    for i in range(30):
        time.sleep(1)
        if check_server_running():
            print("✅ Server started successfully!")
            return True
        print(f"⏳ Waiting for server... ({i+1}/30)")
    
    print("❌ Server failed to start")
    return False

def run_tests():
    """Run all E2E tests"""
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE BACKEND TESTS")
    print("="*70)
    
    test_files = [
        "tests/e2e_sample_pdf.py",
        "tests/e2e_institute_report.py",
        "tests/e2e_institute_report_ugc.py",
        "test_complete_system_e2e.py"
    ]
    
    results = {}
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
        
        print(f"\n📋 Running {test_file}...")
        try:
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=600
            )
            results[test_file] = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            if result.returncode == 0:
                print(f"✅ {test_file} PASSED")
            else:
                print(f"❌ {test_file} FAILED")
                print(result.stderr[:500])
        except subprocess.TimeoutExpired:
            print(f"⏱️  {test_file} TIMED OUT")
            results[test_file] = {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"❌ {test_file} ERROR: {e}")
            results[test_file] = {"success": False, "error": str(e)}
    
    return results

if __name__ == "__main__":
    print("="*70)
    print("BACKEND SERVER STARTUP AND TEST SCRIPT")
    print("="*70)
    
    if start_server():
        time.sleep(2)  # Give server a moment to fully initialize
        results = run_tests()
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        passed = sum(1 for r in results.values() if r.get("success"))
        total = len(results)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            print(f"  {status}: {test_name}")
    else:
        print("❌ Cannot proceed without server")
        sys.exit(1)

