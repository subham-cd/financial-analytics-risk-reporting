"""
FinSight Platform - Financial Analytics and Risk Reporting System
FastAPI Application Entry Point
Evaluation Project: Nexvia Technologies
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.routes.dashboard import router as dashboard_router
from backend.routes.financial import router as financial_router
from backend.routes.budget import router as budget_router
from backend.routes.credit import router as credit_router
from backend.routes.reports import router as reports_router

app = FastAPI(
    title="FinSight – Financial Intelligence & Risk Analytics Platform",
    description="Automated enterprise analytics platform providing financial statement modeling, budget variance analysis, credit risk scorecard prediction, and automated monthly board reporting.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard_router)
app.include_router(financial_router)
app.include_router(budget_router)
app.include_router(credit_router)
app.include_router(reports_router)

@app.get("/api/health", tags=["System"])
def health_check():
    """Health status and database connectivity check."""
    from backend.app.database import execute_one
    try:
        db_check = execute_one("SELECT 1 AS status")
        db_healthy = db_check.get("status") == 1
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "platform": "FinSight Financial Intelligence",
        "version": "2.0.0",
        "database_connected": db_healthy
    }

# Mount frontend build static files if present, else serve frontend/public/index.html
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
FRONTEND_PUBLIC = os.path.join(BASE_DIR, "frontend", "public")

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    @app.get("/{full_path:path}", tags=["Frontend"])
    async def serve_spa_dist(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            return None
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
elif os.path.exists(FRONTEND_PUBLIC):
    app.mount("/static", StaticFiles(directory=FRONTEND_PUBLIC), name="static")
    @app.get("/", tags=["Frontend"])
    async def serve_root():
        index_file = os.path.join(FRONTEND_PUBLIC, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "FinSight API Engine Operational. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    print("[*] Starting FinSight Enterprise Server on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
