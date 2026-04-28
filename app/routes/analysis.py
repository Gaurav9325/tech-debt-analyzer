from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
from app.services.analysis_engine import run_full_analysis
import asyncio
import threading

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/api/analyze", response_class=HTMLResponse)
async def run_analysis(request: Request, repo_url: str = Form(...)):
    if not repo_url.startswith("https://github.com/"):
        return RedirectResponse(url="/analyze", status_code=303)

    # Reset state
    request.app.state.last_result     = None
    request.app.state.analysis_status = "running"

    # Run in a real background thread (not asyncio task)
    def background_job():
        try:
            result = run_full_analysis(repo_url)
            request.app.state.last_result     = result
            request.app.state.analysis_status = "done"
        except Exception as e:
            request.app.state.analysis_status = f"error:{str(e)}"

    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()

    # Redirect immediately to loading page
    return RedirectResponse(url=f"/loading?repo={quote(repo_url)}", status_code=303)


@router.get("/api/landing-stats")
async def landing_stats(request: Request):
    result = getattr(request.app.state, "last_result", None)
    if not result:
        return {
            "has_data":    False,
            "files":       0,
            "issues":      0,
            "score":       None,
            "ai_engine":   "GPT-4o / Groq",
            "repo":        None
        }

    all_files = (
        result.get("critical_files", []) +
        result.get("moderate_files", []) +
        result.get("healthy_files", [])
    )
    avg_score = round(
        sum(f.get("debt_score", 0) for f in all_files) / max(len(all_files), 1)
    ) if all_files else 0

    total_issues = sum(len(f.get("issues", [])) for f in all_files)
    repo_name    = result.get("repo_url", "").replace("https://github.com/", "")

    return {
        "has_data":  True,
        "files":     result.get("total_files_analyzed", len(all_files)),
        "issues":    total_issues,
        "score":     avg_score,
        "ai_engine": "GPT-4o" if result.get("ai_engine") == "openai" else "Groq LLaMA 3.3",
        "repo":      repo_name
    }


@router.get("/api/status")
async def get_status(request: Request):
    status = getattr(request.app.state, "analysis_status", "idle")  
    return {"status": status}   