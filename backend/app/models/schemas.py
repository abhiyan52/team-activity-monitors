from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Schemas
class ActivityQueryRequest(BaseModel):
    query: str
    team_members: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None  # {"start": "2023-01-01", "end": "2023-01-31"}

class JiraIssueFilter(BaseModel):
    project_key: Optional[str] = None
    assignee: Optional[str] = None
    status: Optional[str] = None
    issue_type: Optional[str] = None
    created_after: Optional[datetime] = None
    updated_after: Optional[datetime] = None

class GitHubFilter(BaseModel):
    repository: Optional[str] = None
    author: Optional[str] = None
    since: Optional[datetime] = None
    branch: Optional[str] = None

# Response Schemas
class JiraIssue(BaseModel):
    key: str
    summary: str
    status: str
    assignee: Optional[str] = None
    priority: Optional[str] = None
    issue_type: str
    created: datetime
    updated: datetime
    description: Optional[str] = None
    url: str

class JiraResponse(BaseModel):
    issues: List[JiraIssue]
    total_count: int
    filtered_count: int

class GitHubCommit(BaseModel):
    sha: str
    message: str
    author: str
    date: datetime
    url: str
    repository: str

class GitHubPullRequest(BaseModel):
    number: int
    title: str
    state: str
    author: str
    created_at: datetime
    updated_at: datetime
    url: str
    repository: str
    merged: bool = False
    merged_at: Optional[datetime] = None

class GitHubResponse(BaseModel):
    commits: List[GitHubCommit]
    pull_requests: List[GitHubPullRequest]
    repositories: List[str]

class ActivitySummary(BaseModel):
    jira: JiraResponse
    github: GitHubResponse
    summary_text: str
    generated_at: datetime
    query_metadata: Dict[str, Any]

# Database Models (for SQLAlchemy)
class ActivityLogBase(BaseModel):
    query: str
    response_data: Dict[str, Any]
    created_at: datetime

class ActivityLogCreate(ActivityLogBase):
    pass

class ActivityLog(ActivityLogBase):
    id: int
    
    class Config:
        from_attributes = True
