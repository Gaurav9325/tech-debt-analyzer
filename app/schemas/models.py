from pydantic import BaseModel
from typing import List, Optional

class LineIssue(BaseModel):
    line_range: str
    function_name: Optional[str] = None
    issue_type: str
    severity: str
    description: str
    suggestion: str

class FileReport(BaseModel):
    file_path: str
    debt_score: int
    churn_rate: str
    complexity: int
    issues: List[LineIssue]

class DebtReport(BaseModel):
    repo_url: str
    total_files_analyzed: int
    critical_files: List[FileReport]
    moderate_files: List[FileReport]
    summary: str
    recommendations: List[str]

class AnalysisRequest(BaseModel):
    repo_url: str