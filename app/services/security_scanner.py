import subprocess
import json
import os
import sys
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("TechDebtAnalyzer")


def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def explain_security_issue(issue: dict, code_context: str):
    log.info(f"      🔐 Explaining: {issue['test_name']} on line {issue['line_number']}")
    prompt = f"""A security scanner flagged this issue in Python code:

Issue: {issue['issue_text']}
Rule: {issue['test_name']} ({issue['test_id']})
Severity: {issue['issue_severity']}

Code context:
{code_context}

In 1–2 sentences explain specifically:
1. Why this is dangerous in this exact context
2. The exact fix

Be concrete and specific to the code above, not generic."""

    try:
        response = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"      ⚠️  LLM explanation failed: {str(e)}")
        return issue.get("issue_text", "Review this security issue immediately.")


def scan_security(repo_dir: str):
    log.info("   Running Bandit security scanner...")
    results = {}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", repo_dir, "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip()
        if not output:
            log.info("   ✅ Bandit found no security issues")
            return {}

        data = json.loads(output)
        issues_found = data.get("results", [])
        log.info(f"   🔐 Bandit found {len(issues_found)} security issue(s)")

        for issue in issues_found:
            file_path = os.path.relpath(issue["filename"], repo_dir)
            log.info(f"   📁 {file_path} — {issue['test_name']} (Line {issue['line_number']})")

            code_context = ""
            try:
                with open(issue["filename"], "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                start = max(0, issue["line_number"] - 3)
                end = min(len(lines), issue["line_number"] + 3)
                code_context = "".join(lines[start:end])
            except Exception:
                pass

            explanation = explain_security_issue(issue, code_context)

            if file_path not in results:
                results[file_path] = []

            results[file_path].append({
                "line_range": f"Line {issue['line_number']}",
                "function_name": None,
                "issue_type": f"Security: {issue['test_name']}",
                "severity": "🔴 Critical" if issue["issue_severity"] == "HIGH" else "🟡 Moderate",
                "description": explanation,
                "suggestion": f"Fix Bandit rule {issue['test_id']} — see https://bandit.readthedocs.io"
            })

    except json.JSONDecodeError:
        log.warning("   ⚠️  Bandit output could not be parsed")
    except Exception as e:
        log.error(f"   ❌ Bandit scan failed: {str(e)}")

    return results