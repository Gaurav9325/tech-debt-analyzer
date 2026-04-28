import os
import logging
from radon.complexity import cc_visit

log = logging.getLogger("TechDebtAnalyzer")


def scan_file_complexity(file_path: str):
    issues = []
    total_complexity = 0
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        blocks = cc_visit(source)
        for block in blocks:
            total_complexity += block.complexity
            if block.complexity >= 10:
                severity = "🔴 Critical" if block.complexity >= 15 else "🟡 Moderate"
                issues.append({
                    "line_range": f"Line {block.lineno}",
                    "function_name": block.name,
                    "issue_type": "High Complexity",
                    "severity": severity,
                    "description": (
                        f"Function `{block.name}` has cyclomatic complexity of {block.complexity}. "
                        f"This means {block.complexity} independent execution paths — very hard to test and maintain."
                    ),
                    "suggestion": (
                        f"Decompose `{block.name}` into smaller single-responsibility functions. "
                        f"Target complexity below 5 per function."
                    )
                })
    except Exception as e:
        log.debug(f"   Skipped {file_path}: {str(e)}")
    return issues, total_complexity


def scan_repo_complexity(repo_dir: str):
    log.info("   Scanning all Python files for complexity...")
    results = {}
    scanned = 0
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d not in [
            ".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"
        ]]
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_dir)
                issues, complexity = scan_file_complexity(full_path)
                results[rel_path] = {
                    "issues": issues,
                    "total_complexity": complexity
                }
                scanned += 1
                if issues:
                    log.info(f"   ⚠️  {rel_path} — complexity: {complexity}, issues: {len(issues)}")

    log.info(f"   Scanned {scanned} Python files")
    return results