import os
import git
import logging
import tempfile
from github import Github

log = logging.getLogger("TechDebtAnalyzer")


def parse_repo_info(repo_url: str):
    parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
    return parts[0], parts[1]


def fetch_repo_metadata(repo_url: str):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.warning("⚠️  GITHUB_TOKEN not set — skipping metadata fetch")
        return {}

    log.info(f"   Connecting to GitHub API...")
    g = Github(token)
    owner, repo_name = parse_repo_info(repo_url)

    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
        log.info(f"   ✅ Repo found: {repo.full_name} | ⭐ Stars: {repo.stargazers_count} | 🍴 Forks: {repo.forks_count}")
    except Exception as e:
        log.error(f"   ❌ GitHub API error: {str(e)}")
        log.error("   Check your GITHUB_TOKEN in .env — it may be expired or invalid")
        return {}

    file_metadata = {}
    try:
        log.info("   Fetching last 100 commits...")
        commits = list(repo.get_commits())[:100]
        log.info(f"   Found {len(commits)} commits to analyze")
    except Exception as e:
        log.error(f"   ❌ Failed to fetch commits: {str(e)}")
        return {}

    for i, commit in enumerate(commits):
        try:
            for file in commit.files:
                path = file.filename
                if not path.endswith(".py"):
                    continue
                if path not in file_metadata:
                    file_metadata[path] = {
                        "churn_count": 0,
                        "contributors": set(),
                        "bug_commits": 0
                    }
                file_metadata[path]["churn_count"] += 1
                author = commit.author.login if commit.author else "unknown"
                file_metadata[path]["contributors"].add(author)
                msg = commit.commit.message.lower()
                if any(kw in msg for kw in ["fix", "bug", "error", "crash", "issue", "patch", "hotfix"]):
                    file_metadata[path]["bug_commits"] += 1
        except Exception:
            continue

    for path in file_metadata:
        file_metadata[path]["contributor_count"] = len(file_metadata[path]["contributors"])
        del file_metadata[path]["contributors"]

    log.info(f"   📊 Metadata collected for {len(file_metadata)} Python files")
    return file_metadata


def clone_repo(repo_url: str):
    tmp_dir = tempfile.mkdtemp()
    token = os.getenv("GITHUB_TOKEN")
    if token:
        auth_url = repo_url.replace("https://", f"https://{token}@")
    else:
        auth_url = repo_url
        log.warning("⚠️  No GITHUB_TOKEN — cloning as public repo")

    log.info(f"   Cloning into temp dir: {tmp_dir}")
    try:
        git.Repo.clone_from(auth_url, tmp_dir, depth=1)
        log.info("   ✅ Clone successful")
    except Exception as e:
        log.error(f"   ❌ Clone failed: {str(e)}")
        raise e
    return tmp_dir