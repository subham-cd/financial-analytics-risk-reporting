"""
FinSight Platform - Financial Reports Generation & Delivery API Routes
"""

import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from reports.generate_pdf_report import generate_board_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

class ReportGenerateRequest(BaseModel):
    fiscal_year: int = Field(2026, description="Fiscal Year")
    fiscal_month: int = Field(12, ge=1, le=12, description="Fiscal Month (1-12)")
    report_type: str = Field("Monthly Board Report", description="Type of report")

@router.get("/monthly")
def list_available_reports():
    """Lists generated financial and risk reports available in the platform catalog."""
    reports = []
    if os.path.exists(REPORTS_DIR):
        for f in os.listdir(REPORTS_DIR):
            if f.endswith(".pdf"):
                full_path = os.path.join(REPORTS_DIR, f)
                stat = os.stat(full_path)
                reports.append({
                    "filename": f,
                    "report_name": "Executive & Board Financial Report" if "board" in f else "Financial Report",
                    "file_size_bytes": stat.st_size,
                    "file_size_formatted": f"{stat.st_size / 1024:.1f} KB",
                    "created_at": stat.st_mtime,
                    "download_url": f"/api/reports/download/{f}"
                })
    return {
        "status": "success",
        "count": len(reports),
        "reports": reports
    }

@router.post("/generate")
def generate_report_endpoint(req: ReportGenerateRequest):
    """Triggers generation of an executive-grade PDF board report."""
    try:
        pdf_path = generate_board_report(target_month=req.fiscal_month, fiscal_year=req.fiscal_year)
        filename = os.path.basename(pdf_path)
        stat = os.stat(pdf_path)
        return {
            "status": "success",
            "message": f"Successfully generated report for FY{req.fiscal_year}-M{req.fiscal_month}",
            "filename": filename,
            "file_size_bytes": stat.st_size,
            "download_url": f"/api/reports/download/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile PDF report: {str(e)}")

@router.get("/download/{filename}")
def download_report(filename: str):
    """Streams the requested PDF report file to the client."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(REPORTS_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested report file not found.")
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_name
    )
