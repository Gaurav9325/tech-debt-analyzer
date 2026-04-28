from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html")


@router.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    error = request.query_params.get("error", "")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"error": error}
    )


@router.get("/loading", response_class=HTMLResponse)
async def loading_page(request: Request):
    repo = request.query_params.get("repo", "")
    return templates.TemplateResponse(
        request=request,
        name="loading.html",
        context={"repo_url": repo}
    )


@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    result = getattr(request.app.state, "last_result", None)

    if not result:
        return RedirectResponse(url="/analyze", status_code=303)

    repo_url  = result.get("repo_url", "")
    repo_name = repo_url.replace("https://github.com/", "")

    all_file_reports = (
        result.get("critical_files", []) +
        result.get("moderate_files", []) +
        result.get("healthy_files", [])
    )

    total_files           = result.get("total_files_analyzed", len(all_file_reports))
    total_issues          = sum(len(f.get("issues", [])) for f in all_file_reports)
    total_lines           = f"{sum(f.get('complexity', 0) * 15 for f in all_file_reports):,}"
    security_issues_count = sum(
        sum(1 for i in f.get("issues", []) if "Security" in (i.get("issue_type") or ""))
        for f in all_file_reports
    )
    avg_complexity = round(
        sum(f.get("complexity", 0) for f in all_file_reports) / max(len(all_file_reports), 1), 1
    )
    final_score = round(
        sum(f.get("debt_score", 0) for f in all_file_reports) / max(len(all_file_reports), 1)
    ) if all_file_reports else 0

    # File table
    files_table = []
    for f in all_file_reports:
        issues    = f.get("issues", [])
        sec_count = sum(1 for i in issues if "Security" in (i.get("issue_type") or ""))
        score     = f.get("debt_score", 0)
        c         = f.get("complexity", 0)
        files_table.append({
            "name":       f.get("file_path", "unknown"),
            "score":      score,
            "complexity": "High" if c > 15 else "Medium" if c > 7 else "Low",
            "security":   f"{sec_count} issue{'s' if sec_count != 1 else ''}" if sec_count else "Clean",
            "grade":      "A" if score < 30 else "B" if score < 50 else "C" if score < 70 else "D",
            "churn":      f.get("churn_rate", "Low"),
        })

    # Top issues
    severity_icon = {
        "🔴 Critical": "🔴",
        "🟡 Moderate": "🟡",
        "🟢 Minor":    "🔵"
    }
    top_issues = []
    for f in all_file_reports:
        for issue in f.get("issues", []):
            top_issues.append({
                "icon":          severity_icon.get(issue.get("severity", ""), "🔵"),
                "title":         issue.get("issue_type", "Issue"),
                "desc":          issue.get("description", ""),
                "file":          f"{f.get('file_path', '')}:{issue.get('line_range', '')}",
                "suggestion":    issue.get("suggestion", ""),
                "severity_sort": 0 if "Critical" in (issue.get("severity") or "")
                                 else 1 if "Moderate" in (issue.get("severity") or "") else 2,
            })
    top_issues.sort(key=lambda x: x["severity_sort"])
    top_issues = top_issues[:8]

    # Verdict chip
    if final_score >= 70:
        verdict_chip = ("chip-red",    "🔴 High Debt")
    elif final_score >= 40:
        verdict_chip = ("chip-yellow", "⚠ Moderate Debt")
    else:
        verdict_chip = ("chip-green",  "✓ Healthy Codebase")

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "repo_url":        repo_url,
            "repo_name":       repo_name,
            "final_score":     final_score,
            "total_files":     total_files,
            "total_lines":     total_lines,
            "total_issues":    total_issues,
            "security_issues": security_issues_count,
            "avg_complexity":  avg_complexity,
            "ai_reviewed":     len(all_file_reports),
            "summary":         result.get("summary", ""),
            "recommendations": result.get("recommendations", []),
            "files_table":     files_table,
            "top_issues":      top_issues,
            "verdict_chip":    verdict_chip,
            "critical_count":  len(result.get("critical_files", [])),
            "moderate_count":  len(result.get("moderate_files", [])),
            "healthy_count":   len(result.get("healthy_files", [])),
        }
    )