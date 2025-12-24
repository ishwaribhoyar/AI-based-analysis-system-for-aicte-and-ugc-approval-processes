"""
Smart Approval AI - FastAPI Backend
Minimal, official architecture - SQLite temporary storage only
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from pathlib import Path

from routers import (
    batches,
    documents,
    processing,
    dashboard,
    reports,
    chatbot,
    compare,
    approval,
    unified_report,
    analytics,
)
from routers import kpi_details
from config.database import init_db

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Initialize SQLite database
init_db()

# CORS configuration (force permissive for local dev to avoid blocked requests)
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = ["*"]
ALLOW_ALL_ORIGINS = True

app = FastAPI(
    title="Smart Approval AI",
    description="AI-Based Document Analysis, Performance Indicators & Reporting System for UGC & AICTE Reviewers",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # keep '*' compatible responses
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_fallback_cors_headers(request, call_next):
    """
    Ensure CORS headers are present even on error responses (e.g., 404/500),
    which some browsers otherwise flag as missing and surface as CORS failures.
    """
    response = await call_next(request)
    origin = request.headers.get("origin")

    if ALLOW_ALL_ORIGINS:
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
    elif origin and origin in ALLOWED_ORIGINS:
        response.headers.setdefault("Access-Control-Allow-Origin", origin)

    if "Access-Control-Allow-Origin" in response.headers:
        response.headers.setdefault("Access-Control-Allow-Credentials", "false")
        response.headers.setdefault(
            "Access-Control-Allow-Headers",
            "Authorization, Content-Type, Accept, Origin, X-Requested-With, *",
        )
        response.headers.setdefault(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        )

    return response

# Mount static directories
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/reports", exist_ok=True)
os.makedirs("storage/db", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="storage/uploads"), name="uploads")
app.mount("/reports", StaticFiles(directory="storage/reports"), name="reports")

# Include routers
app.include_router(batches.router, prefix="/api/batches", tags=["Batches"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(processing.router, prefix="/api/processing", tags=["Processing"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(compare.router, prefix="/api", tags=["Comparison"])
app.include_router(approval.router, prefix="/api", tags=["Approval"])
app.include_router(unified_report.router, prefix="/api", tags=["Unified Report"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(kpi_details.router, prefix="/api/kpi", tags=["KPI Details"])

@app.get("/")
def root():
    return {
        "message": "Smart Approval AI API",
        "version": "2.0.0",
        "status": "operational",
        "architecture": "Information Block Architecture - SQLite Temporary Storage"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
