import shutil
import logging
import time
from app.services.github_service import fetch_repo_metadata, clone_repo
from app.services.complexity_scanner import scan_repo_complexity
from app.services.ai_reviewer import scan_repo_with_ai
from app.services.security_scanner import scan_security
from app.services.ml_scorer import compute_debt_score
from app.services.report_generator import generate_full_report

log = logging.getLogger("TechDebtAnalyzer")


def build_score_breakdown(churn_count, complexity, bug_commits, ai_issue_count, security_count, score):

    factors = []

    # Churn
    churn_pts = min(churn_count * 1.2, 25)
    factors.append({
        "label": "How Often This File Changes",
        "value": churn_count,
        "points": round(churn_pts, 1),
        "max": 25,
        "status": "high" if churn_pts > 15 else "medium" if churn_pts > 5 else "good",
        "explanation": (
            f"This file was changed {churn_count} time(s) in recent commits. "
            + ("Files that change very often usually have messy or unstable code inside." if churn_count > 20
               else "It changes sometimes — worth keeping an eye on it." if churn_count > 5
               else "It rarely changes, which means the code inside is stable and reliable.")
        ),
        "fix": (
            "Try splitting this file into smaller pieces so each part does just one job."
            if churn_count > 10 else "Nothing to do here — this file is in good shape."
        )
    })

    # Complexity
    comp_pts = min(complexity * 1.0, 20)
    factors.append({
        "label": "How Complicated the Code Is",
        "value": complexity,
        "points": round(comp_pts, 1),
        "max": 20,
        "status": "high" if comp_pts > 14 else "medium" if comp_pts > 7 else "good",
        "explanation": (
            f"The code has a complexity score of {complexity}. Think of this as how many "
            f"different paths someone reading the code has to follow. "
            + ("Very high — this code is hard to read and even harder to fix when something breaks." if complexity > 15
               else "Medium — some parts could be simpler and easier to understand." if complexity > 7
               else "Low — the code is easy to read and follow.")
        ),
        "fix": (
            "Break up any large functions into smaller ones, each doing just one clear task."
            if complexity > 7 else "The code is simple and easy to understand. No changes needed."
        )
    })

    # Bug commits
    bug_pts = min(bug_commits * 2.5, 20)
    factors.append({
        "label": "How Many Times Bugs Were Fixed Here",
        "value": bug_commits,
        "points": round(bug_pts, 1),
        "max": 20,
        "status": "high" if bug_pts > 12 else "medium" if bug_pts > 5 else "good",
        "explanation": (
            f"{bug_commits} recent commit(s) fixed bugs in this file. "
            + ("Many bug fixes in one file is a warning sign — the code may be fragile." if bug_commits > 8
               else "A few bugs were fixed here — the logic might need a second look." if bug_commits > 3
               else "Very few bugs found here — the code seems reliable.")
        ),
        "fix": (
            "Write tests that check this file's behavior so future changes don't accidentally break things."
            if bug_commits > 3 else "Keep writing tests to make sure it stays this clean."
        )
    })

    # AI issues
    ai_pts = min(ai_issue_count * 3.0, 25)
    factors.append({
        "label": "Problems Found by AI Review",
        "value": ai_issue_count,
        "points": round(ai_pts, 1),
        "max": 25,
        "status": "high" if ai_pts > 15 else "medium" if ai_pts > 6 else "good",
        "explanation": (
            f"The AI reviewer looked at every function in this file and found {ai_issue_count} problem(s). "
            + ("Several problems were found that could cause bugs or make the code hard to maintain." if ai_issue_count > 5
               else "A few small problems were found — they are worth fixing." if ai_issue_count > 2
               else "Almost no problems found — the code quality looks great.")
        ),
        "fix": (
            "Fix the problems listed above, starting with the ones marked Critical."
            if ai_issue_count > 0 else "No problems found by the AI. Keep writing clean code like this."
        )
    })

    # Security
    sec_pts = min(security_count * 5.0, 10)
    factors.append({
        "label": "Security Risks",
        "value": security_count,
        "points": round(sec_pts, 1),
        "max": 10,
        "status": "high" if sec_pts > 6 else "medium" if sec_pts > 2 else "good",
        "explanation": (
            f"The security scanner found {security_count} risk(s) in this file. "
            + ("These risks could allow attackers to misuse the app — fix them right away." if security_count > 2
               else "There are some security concerns worth reviewing." if security_count > 0
               else "No security risks found — this file looks safe.")
        ),
        "fix": (
            "Security problems should always be fixed before anything else. Check the issues listed above."
            if security_count > 0 else "No security fixes needed here."
        )
    })

    # Verdict and next steps
    if score < 20:
        verdict = "This file is in great shape! The low score means it is clean, stable, and easy to maintain."
        next_steps = [
            "Add tests to make sure the code keeps working as expected",
            "Add comments to explain any tricky parts for other developers",
            "Set up automatic checks so future changes don't introduce problems"
        ]
    elif score < 40:
        verdict = "This file is mostly healthy but has a few small things worth cleaning up."
        next_steps = [
            "Fix the small problems the AI found",
            "Simplify any functions that feel hard to read",
            "Add tests for parts that recently changed"
        ]
    elif score < 70:
        verdict = "This file has some issues that will make it harder to work with over time. Worth fixing soon."
        next_steps = [
            "Start by fixing the most serious problems (marked Critical)",
            "Break up any large, complicated functions",
            "Look at which parts of the code keep breaking and fix the root cause"
        ]
    else:
        verdict = "This file needs serious attention. Leaving it as-is will slow down the whole project."
        next_steps = [
            "Plan time specifically to clean up and rewrite this file",
            "Fix all security risks immediately — they are the most dangerous",
            "Split this file into smaller, well-tested pieces"
        ]

    return {
        "score": score,
        "verdict": verdict,
        "next_steps": next_steps,
        "factors": factors
    }


def run_full_analysis(repo_url: str):
    log.info("=" * 60)
    log.info(f"🚀 Starting analysis: {repo_url}")
    log.info("=" * 60)
    total_start = time.time()

    log.info("📥 [1/6] Cloning repository...")
    t = time.time()
    repo_dir = clone_repo(repo_url)
    log.info(f"✅ Cloned in {time.time()-t:.1f}s")

    try:
        log.info("🔍 [2/6] Fetching GitHub commit metadata...")
        t = time.time()
        metadata = fetch_repo_metadata(repo_url)
        log.info(f"✅ Metadata done in {time.time()-t:.1f}s — {len(metadata)} files tracked")

        log.info("📐 [3/6] Running Radon complexity scan...")
        t = time.time()
        complexity_data = scan_repo_complexity(repo_dir)
        total_c_issues = sum(len(v["issues"]) for v in complexity_data.values())
        log.info(f"✅ Complexity done in {time.time()-t:.1f}s — {len(complexity_data)} files, {total_c_issues} issues")

        log.info("🤖 [4/6] Running GPT-4o AI review (30–90s)...")
        t = time.time()
        ai_review_data = scan_repo_with_ai(repo_dir)
        total_ai = sum(len(v) for v in ai_review_data.values())
        log.info(f"✅ AI review done in {time.time()-t:.1f}s — {len(ai_review_data)} files, {total_ai} issues")

        log.info("🔐 [5/6] Running Bandit security scan...")
        t = time.time()
        security_data = scan_security(repo_dir)
        total_sec = sum(len(v) for v in security_data.values())
        log.info(f"✅ Security done in {time.time()-t:.1f}s — {total_sec} vulnerabilities")

        log.info("📊 [6/6] Scoring + generating report...")
        t = time.time()

        all_files = set(
            list(complexity_data.keys()) +
            list(ai_review_data.keys()) +
            list(security_data.keys())
        )
        log.info(f"   Total unique Python files: {len(all_files)}")

        file_reports = []

        for file_path in all_files:
            if not file_path.endswith(".py"):
                continue

            meta = metadata.get(file_path, {
                "churn_count": 0,
                "bug_commits": 0,
                "contributor_count": 1
            })
            complexity_info = complexity_data.get(file_path, {
                "issues": [],
                "total_complexity": 0
            })
            ai_issues       = ai_review_data.get(file_path, [])
            security_issues = security_data.get(file_path, [])
            all_issues = (
                complexity_info.get("issues", []) +
                ai_issues +
                security_issues
            )

            churn_count    = meta.get("churn_count", 0)
            bug_commits    = meta.get("bug_commits", 0)
            complexity_val = complexity_info.get("total_complexity", 0)

            score = compute_debt_score(
                churn_count=churn_count,
                complexity=complexity_val,
                bug_commits=bug_commits,
                contributor_count=meta.get("contributor_count", 1),
                ai_issue_count=len(ai_issues),
                security_count=len(security_issues)
            )

            breakdown = build_score_breakdown(
                churn_count=churn_count,
                complexity=complexity_val,
                bug_commits=bug_commits,
                ai_issue_count=len(ai_issues),
                security_count=len(security_issues),
                score=score
            )

            file_reports.append({
                "file_path": file_path,
                "debt_score": score,
                "churn_rate": (
                    "High"   if churn_count > 20
                    else "Medium" if churn_count > 5
                    else "Low"
                ),
                "complexity": complexity_val,
                "issues": all_issues,
                "breakdown": breakdown
            })
            log.info(f"   📁 {file_path} → Score: {score}/100 | Issues: {len(all_issues)}")

        file_reports.sort(key=lambda x: x["debt_score"], reverse=True)

        critical = [f for f in file_reports if f["debt_score"] >= 70]
        moderate = [f for f in file_reports if 40 <= f["debt_score"] < 70]
        healthy  = [f for f in file_reports if f["debt_score"] < 40]

        log.info(f"   🔴 Critical: {len(critical)} | 🟡 Moderate: {len(moderate)} | 🟢 Healthy: {len(healthy)}")

        report = generate_full_report(repo_url, file_reports, len(all_files))
        log.info(f"✅ Scoring + report done in {time.time()-t:.1f}s")

        total_time = time.time() - total_start
        log.info("=" * 60)
        log.info(f"🏁 ANALYSIS COMPLETE in {total_time:.1f}s")
        log.info(f"   Files analyzed  : {len(all_files)}")
        log.info(f"   Critical files  : {len(critical)}")
        log.info(f"   Moderate files  : {len(moderate)}")
        log.info(f"   Healthy files   : {len(healthy)}")
        log.info(f"   Total issues    : {sum(len(f['issues']) for f in file_reports)}")
        log.info("=" * 60)

        return {
            "repo_url": repo_url,
            "total_files_analyzed": len(all_files),
            "critical_files": critical[:5],
            "moderate_files": moderate[:5],
            "healthy_files":  healthy[:5],
            "summary": report.get("summary", ""),
            "recommendations": report.get("recommendations", [])
        }

    except Exception as e:
        log.error(f"❌ Analysis failed: {str(e)}")
        raise e

    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)
        log.info("🧹 Temp directory cleaned up")