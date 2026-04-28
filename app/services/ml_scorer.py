import numpy as np
import joblib
import os
import logging

log = logging.getLogger("TechDebtAnalyzer")
MODEL_PATH = "ml/model.pkl"


def compute_debt_score(
    churn_count: int,
    complexity: int,
    bug_commits: int,
    contributor_count: int,
    ai_issue_count: int,
    security_count: int
) -> int:
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            features = np.array([[
                churn_count,
                complexity,
                bug_commits,
                contributor_count,
                ai_issue_count,
                security_count
            ]])
            score = float(model.predict(features)[0])
            return min(int(score), 100)
        except Exception as e:
            log.warning(f"   ⚠️  ML model predict failed: {str(e)} — using fallback scoring")

    score = (
        min(churn_count * 1.2, 25) +
        min(complexity * 1.0, 20) +
        min(bug_commits * 2.5, 20) +
        min(ai_issue_count * 3.0, 25) +
        min(security_count * 5.0, 10)
    )
    return min(int(score), 100)