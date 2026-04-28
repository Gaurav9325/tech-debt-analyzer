import os
import ast
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
            client = OpenAI(api_key=openai_key)
            log.info("   🔵 Using OpenAI (gpt-4o-mini)")
            return "openai", client
        except Exception as e:
            log.warning(f"   ⚠️  OpenAI init failed: {e} — falling back to Groq")

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            log.info("   🟢 Using Groq fallback (llama-3.3-70b-versatile)")
            return "groq", Groq(api_key=groq_key)
        except ImportError:
            log.warning("   ⚠️  groq package not installed — run: pip install groq")

    log.warning("   ⚠️  No AI API key found — AI review will be skipped")
    return None, None


# ── Extract functions via AST ─────────────────────────────────────────────
def extract_functions(file_path: str):
    functions = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            lines = source.splitlines()

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = lines[node.lineno - 1: node.end_lineno]
                func_source = "\n".join(func_lines)
                functions.append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "source": func_source
                })
    except Exception as e:
        log.debug(f"   AST parse failed for {file_path}: {str(e)}")
    return functions


# ── Review a single function ──────────────────────────────────────────────
def ai_review_function(func: dict, file_path: str, provider: str, client):
    prompt = f"""You are a senior software engineer doing a thorough code review.

File: {file_path}
Function: `{func['name']}` (Lines {func['start_line']}–{func['end_line']})

Code:
```python
{func['source']}
```

Carefully analyze this function. Find ALL real issues present in the actual code above.

Return a JSON array. Each item must have:
- "line_range": exact line number(s) where the issue exists
- "function_name": "{func['name']}"
- "issue_type": one of [Logic Bug, Security Risk, Performance Issue, Error Handling, Code Smell, Dead Code, Hardcoded Value, Complexity, Missing Validation]
- "severity": one of ["🔴 Critical", "🟡 Moderate", "🟢 Minor"]
- "description": specific explanation referencing the actual code
- "suggestion": the exact fix for this specific code

Return ONLY a valid JSON array. No markdown. No explanation outside the JSON.
If no real issues found, return []."""

    try:
        if provider == "openai":
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
        else:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )

        content = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
            if content.startswith("json"):
                content = content[4:].strip()

        return json.loads(content)

    except json.JSONDecodeError as e:
        log.warning(f"   ⚠️  JSON parse error for {func['name']}: {str(e)}")
        return []
    except Exception as e:
        err_str = str(e)
        # If OpenAI quota exceeded, switch to Groq on the fly
        if "429" in err_str or "insufficient_quota" in err_str:
            log.warning(f"   ⚠️  OpenAI quota exceeded — switching to Groq for this function")
            return _retry_with_groq(func, file_path, prompt)
        log.warning(f"   ⚠️  [{provider}] review failed for {func['name']}: {err_str}")
        return []


# ── Groq retry on quota error ─────────────────────────────────────────────
def _retry_with_groq(func: dict, file_path: str, prompt: str):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        log.warning("   ⚠️  No GROQ_API_KEY set — cannot retry")
        return []
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
            if content.startswith("json"):
                content = content[4:].strip()
        issues = json.loads(content)
        log.info(f"   ✅ [groq-fallback] {func['name']} → {len(issues)} issues")
        return issues if isinstance(issues, list) else []
    except Exception as e:
        log.warning(f"   ⚠️  Groq fallback also failed: {str(e)}")
        return []


# ── Review a single file ──────────────────────────────────────────────────
def ai_review_file(file_path: str, provider: str, client):
    functions = extract_functions(file_path)
    if not functions:
        return []

    all_issues = []
    log.info(f"   🤖 Reviewing {os.path.basename(file_path)} — {len(functions)} functions")

    for func in functions:
        if func["end_line"] - func["start_line"] < 3:
            continue
        log.info(f"      → Reviewing `{func['name']}()` (Lines {func['start_line']}–{func['end_line']})")
        issues = ai_review_function(func, file_path, provider, client)
        if isinstance(issues, list):
            if issues:
                log.info(f"        Found {len(issues)} issue(s)")
            all_issues.extend(issues)

    return all_issues


# ── Scan entire repo ──────────────────────────────────────────────────────
def scan_repo_with_ai(repo_dir: str):
    provider, client = get_client()

    if client is None:
        log.warning("   ⚠️  No AI client available — skipping AI review")
        return {}

    log.info(f"   Starting AI review with [{provider}]...")
    results = {}
    py_files = []

    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d not in [
            ".git", "__pycache__", "node_modules",
            ".venv", "venv", "env", "dist", "build"
        ]]
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    log.info(f"   Found {len(py_files)} Python files to review")

    for i, full_path in enumerate(py_files):
        rel_path = os.path.relpath(full_path, repo_dir)
        log.info(f"   [{i+1}/{len(py_files)}] {rel_path}")
        try:
            issues = ai_review_file(full_path, provider, client)
            if issues:
                results[rel_path] = issues
                log.info(f"   ✅ {rel_path} — {len(issues)} total issues found")
            else:
                log.info(f"   ✅ {rel_path} — clean")
        except Exception as e:
            log.error(f"   ❌ Failed to review {rel_path}: {str(e)}")
            continue

    log.info(f"   AI review complete — {len(results)} files have issues")
    return results