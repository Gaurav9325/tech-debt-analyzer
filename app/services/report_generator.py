import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("TechDebtAnalyzer")


# ── AI Client — OpenAI first, Groq fallback ───────────────────────────────
def get_client():
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            return "openai", OpenAI(api_key=openai_key)
        except Exception as e:
            log.warning(f"   ⚠️  OpenAI init failed: {e}")

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            return "groq", Groq(api_key=groq_key)
        except ImportError:
            log.warning("   ⚠️  groq package not installed")

    return None, None


def call_llm(client, provider: str, prompt: str) -> str:
    if provider == "openai":
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.2
        )
    else:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.2
        )
    return response.choices[0].message.content.strip()


# ── Rule-based fallback ───────────────────────────────────────────────────
def build_fallback_report(repo_url: str, file_reports: list):
    if not file_reports:
        return {
            "summary": (
                "No Python files with issues were found in this repository. "
                "All scanned files passed the complexity, security, and code quality checks. "
                "This is a great starting point — focus on adding tests to keep it this way."
            ),
            "recommendations": [
                "Add unit tests to cover all important functions",
                "Set up automatic checks on every code change",
                "Add comments to explain tricky parts of the code",
                "Review your dependencies and remove unused ones",
                "Document how to run and set up the project for new developers"
            ]
        }

    total          = len(file_reports)
    critical_files = [f for f in file_reports if f["debt_score"] >= 70]
    moderate_files = [f for f in file_reports if 40 <= f["debt_score"] < 70]
    healthy_files  = [f for f in file_reports if f["debt_score"] < 40]
    top            = file_reports[0]
    best           = file_reports[-1]

    sec_files     = [f for f in file_reports if any(
                      "Security" in (i.get("issue_type") or "")
                      for i in f.get("issues", []))]
    complex_files = sorted(file_reports, key=lambda x: x.get("complexity", 0), reverse=True)
    most_complex  = complex_files[0] if complex_files else None
    churn_high    = [f for f in file_reports if f.get("churn_rate") == "High"]
    churn_medium  = [f for f in file_reports if f.get("churn_rate") == "Medium"]

    all_issues      = [i for f in file_reports for i in f.get("issues", [])]
    critical_issues = [i for i in all_issues if "Critical" in (i.get("severity") or "")]
    moderate_issues = [i for i in all_issues if "Moderate" in (i.get("severity") or "")]

    issue_type_counts = {}
    for i in all_issues:
        t = i.get("issue_type", "Unknown")
        issue_type_counts[t] = issue_type_counts.get(t, 0) + 1
    top_issue_type = max(issue_type_counts, key=issue_type_counts.get) if issue_type_counts else None

    # Summary
    summary_parts = []
    if critical_files:
        summary_parts.append(
            f"Out of {total} file(s) scanned, {len(critical_files)} "
            f"{'needs' if len(critical_files) == 1 else 'need'} urgent attention — "
            f"`{critical_files[0]['file_path']}` is the worst with a score of "
            f"{critical_files[0]['debt_score']}/100."
        )
    elif moderate_files:
        summary_parts.append(
            f"All {total} file(s) are in reasonable shape, but {len(moderate_files)} "
            f"{'has' if len(moderate_files) == 1 else 'have'} moderate issues worth fixing — "
            f"starting with `{moderate_files[0]['file_path']}` (score {moderate_files[0]['debt_score']}/100)."
        )
    else:
        summary_parts.append(
            f"All {total} file(s) scored below 40/100 — this repository is in healthy condition. "
            f"The file that needs the most attention is `{top['file_path']}` with a score of {top['debt_score']}/100."
        )

    if sec_files:
        sec_names = " and ".join(f"`{f['file_path']}`" for f in sec_files[:2])
        summary_parts.append(
            f"The most urgent issue is a security risk in {sec_names} — "
            f"security problems should always be fixed before anything else."
        )
    elif critical_issues:
        worst = critical_issues[0]
        summary_parts.append(
            f"The most serious problem found is in "
            f"`{worst.get('function_name') or 'unknown function'}` — "
            f"{worst.get('description', 'a critical issue that needs immediate attention')[:120]}."
        )
    elif most_complex and most_complex.get("complexity", 0) > 10:
        summary_parts.append(
            f"`{most_complex['file_path']}` has the most complicated code "
            f"(complexity score: {most_complex['complexity']}) — this makes it "
            f"harder to understand and more likely to contain hidden bugs."
        )
    else:
        summary_parts.append(
            f"No critical security risks or serious bugs were detected across any of the {total} file(s). "
            f"The cleanest file is `{best['file_path']}` with a score of just {best['debt_score']}/100."
        )

    total_issue_count = len(all_issues)
    if total_issue_count == 0:
        summary_parts.append(
            "No line-level issues were detected in any file — focus on adding tests "
            "to protect this clean codebase going forward."
        )
    else:
        summary_parts.append(
            f"A total of {total_issue_count} issue(s) were found across all files "
            f"({len(critical_issues)} critical, {len(moderate_issues)} moderate) — "
            f"fixing the critical ones first will have the biggest impact."
        )

    # Recommendations
    recs = []
    if critical_files:
        recs.append(
            f"`{critical_files[0]['file_path']}` has a debt score of {critical_files[0]['debt_score']}/100 "
            f"with {len(critical_files[0].get('issues', []))} issue(s) — "
            f"open this file first and work through the problems listed in its breakdown above."
        )
    elif moderate_files:
        recs.append(
            f"`{moderate_files[0]['file_path']}` scored {moderate_files[0]['debt_score']}/100 — "
            f"it has {len(moderate_files[0].get('issues', []))} issue(s) that are worth fixing "
            f"before they grow into bigger problems."
        )
    else:
        recs.append(
            f"`{top['file_path']}` scored {top['debt_score']}/100 — "
            f"even though it is healthy, reviewing it will help maintain quality as the project grows."
        )

    if sec_files:
        names = " and ".join(f"`{f['file_path']}`" for f in sec_files[:2])
        sec_count = sum(
            sum(1 for i in f.get("issues", []) if "Security" in (i.get("issue_type") or ""))
            for f in sec_files[:2]
        )
        recs.append(
            f"Fix the {sec_count} security risk(s) in {names} immediately — "
            f"these are the most dangerous type of problem because they could allow "
            f"attackers to misuse the application."
        )
    elif most_complex and most_complex.get("complexity", 0) > 10:
        recs.append(
            f"`{most_complex['file_path']}` has a complexity score of {most_complex['complexity']} — "
            f"find the largest functions inside it and split each one into 2–3 smaller focused functions."
        )

    if churn_high:
        names = " and ".join(f"`{f['file_path']}`" for f in churn_high[:2])
        recs.append(
            f"{names} {'has' if len(churn_high[:2]) == 1 else 'have'} changed very frequently — "
            f"rewriting the most-changed parts more clearly will reduce future problems."
        )
    elif churn_medium:
        recs.append(
            f"`{churn_medium[0]['file_path']}` has been updated several times recently — "
            f"add tests around its most important logic so future changes don't accidentally break things."
        )
    else:
        recs.append(
            f"All {total} file(s) have low churn — they rarely need to be changed. "
            f"Write tests to lock in this stable behavior."
        )

    if top_issue_type and issue_type_counts[top_issue_type] > 1:
        count = issue_type_counts[top_issue_type]
        recs.append(
            f"The most common problem found across this repo is '{top_issue_type}' "
            f"({count} occurrence(s)) — search for this type of issue across all files "
            f"and fix them all in one focused session."
        )
    elif healthy_files:
        recs.append(
            f"`{healthy_files[0]['file_path']}` is already healthy — "
            f"use it as a reference for how to write clean code in the rest of this project."
        )
    else:
        recs.append(
            "Add automated tests that run every time code is changed — "
            "this catches problems early before they reach real users."
        )

    if len(file_reports) == 1:
        recs.append(
            "This repo currently has only 1 Python file — as it grows, "
            "split new features into separate files so each file stays small, focused, and easy to maintain."
        )
    elif len(critical_files) == 0 and len(moderate_files) == 0:
        recs.append(
            f"This repo has {len(healthy_files)} healthy file(s) — "
            f"set up a linting check (like Flake8 or Ruff) that runs automatically "
            f"on every code change to keep quality high without manual effort."
        )
    else:
        remaining = len(critical_files) + len(moderate_files)
        recs.append(
            f"After fixing the {remaining} file(s) that need work, re-run this analyzer "
            f"to confirm the scores improved. Aim for every file to score below 40/100."
        )

    return {
        "summary": " ".join(summary_parts),
        "recommendations": recs[:5]
    }


# ── Main report generator ─────────────────────────────────────────────────
def generate_full_report(repo_url: str, file_reports: list, total_files: int):
    log.info("   Generating AI summary + recommendations...")

    provider, client = get_client()

    if client:
        try:
            top_issues = []
            for f in file_reports[:6]:
                issue_types = list(set(
                    i.get("issue_type", "Unknown") for i in f["issues"][:4]
                ))
                top_issues.append(
                    f"- {f['file_path']} "
                    f"(debt score: {f['debt_score']}/100, "
                    f"complexity: {f['complexity']}, "
                    f"issues: {', '.join(issue_types[:3]) or 'none'})"
                )

            prompt = f"""You are reviewing a GitHub repository: {repo_url}

Tech debt scan results:
- Total Python files analyzed: {total_files}
- Critical files (score 70+): {len([f for f in file_reports if f['debt_score'] >= 70])}
- Moderate files (score 40–69): {len([f for f in file_reports if 40 <= f['debt_score'] < 70])}
- Healthy files (score <40): {len([f for f in file_reports if f['debt_score'] < 40])}
- Total issues found: {sum(len(f.get('issues',[])) for f in file_reports)}

Top files by debt score:
{chr(10).join(top_issues) if top_issues else "No significant debt found"}

Write a JSON object with exactly these two keys:
1. "summary": 3 plain-English sentences about this repo's overall health. Mention actual file names. No jargon. Write like explaining to a junior developer.
2. "recommendations": exactly 5 specific, actionable plain-English items. Each must mention specific file names or issue types from the data above. No generic advice.

Return ONLY valid JSON. No markdown. No extra text."""

            content = call_llm(client, provider, prompt)

            if content.startswith("```"):
                parts = content.split("```")
                content = parts[1] if len(parts) > 1 else content
                if content.startswith("json"):
                    content = content[4:].strip()

            result = json.loads(content)
            log.info(f"   ✅ [{provider}] AI report generated successfully")
            return result

        except Exception as e:
            err = str(e)
            # OpenAI quota — retry with Groq
            if ("429" in err or "insufficient_quota" in err) and provider == "openai":
                log.warning("   ⚠️  OpenAI quota exceeded — retrying with Groq...")
                groq_key = os.getenv("GROQ_API_KEY")
                if groq_key:
                    try:
                        from groq import Groq
                        groq_client = Groq(api_key=groq_key)
                        content = call_llm(groq_client, "groq", prompt)
                        if content.startswith("```"):
                            parts = content.split("```")
                            content = parts[1] if len(parts) > 1 else content
                            if content.startswith("json"):
                                content = content[4:].strip()
                        result = json.loads(content)
                        log.info("   ✅ [groq-fallback] report generated")
                        return result
                    except Exception as e2:
                        log.warning(f"   ⚠️  Groq fallback failed: {str(e2)[:60]}")

            log.warning(f"   ⚠️  AI report failed ({err[:60]}) — using rule-based fallback")

    # Rule-based fallback — always works
    log.info("   ✅ Rule-based report generated")
    return build_fallback_report(repo_url, file_reports)