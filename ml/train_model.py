import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ModelTrainer")

log.info("🔧 Generating training data...")
np.random.seed(42)
n = 1000

churn = np.random.randint(1, 150, n)
complexity = np.random.randint(1, 60, n)
bug_commits = np.random.randint(0, 40, n)
contributors = np.random.randint(1, 25, n)
ai_issues = np.random.randint(0, 15, n)
security = np.random.randint(0, 10, n)

target = (
    churn * 0.25 +
    complexity * 0.30 +
    bug_commits * 0.20 +
    ai_issues * 0.15 +
    security * 0.07 +
    contributors * 0.03
).clip(0, 100)
target += np.random.normal(0, 3, n)
target = target.clip(0, 100)

X = pd.DataFrame({
    "churn": churn,
    "complexity": complexity,
    "bug_commits": bug_commits,
    "contributors": contributors,
    "ai_issues": ai_issues,
    "security": security
})

log.info("🤖 Training Gradient Boosting model...")
X_train, X_test, y_train, y_test = train_test_split(X, target, test_size=0.2, random_state=42)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", GradientBoostingRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42
    ))
])

pipeline.fit(X_train, y_train)
preds = pipeline.predict(X_test)
rmse = root_mean_squared_error(y_test, preds)
cv = cross_val_score(pipeline, X, target, cv=5, scoring="r2")

log.info(f"📊 Test RMSE : {rmse:.2f}")
log.info(f"📊 CV R²    : {cv.mean():.4f} ± {cv.std():.4f}")

os.makedirs("ml", exist_ok=True)
joblib.dump(pipeline, "ml/model.pkl")
log.info("✅ Model saved → ml/model.pkl")