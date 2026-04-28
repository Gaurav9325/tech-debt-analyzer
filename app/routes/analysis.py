import logging
import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.schemas.models import AnalysisRequest
from app.services.analysis_engine import run_full_analysis

log = logging.getLogger("TechDebtAnalyzer")
router = APIRouter(prefix="/api", tags=["analysis"])

@router.post("/analyze")    
def analyze_repo(request: AnalysisRequest):
    log.info(f"📨 Received request for: {request.repo_url}")
    try:
        report = run_full_analysis(request.repo_url)
        log.info("📤 Sending report to frontend")
        return JSONResponse(content=report)
    except Exception as e:
        log.error("=" * 50)
        log.error(f"❌ FULL ERROR TRACEBACK:")
        log.error(traceback.format_exc())
        log.error("=" * 50)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "detail": traceback.format_exc()}
        )