from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
# Using Pydantic v2 directly for better compatibility

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

# Agent and LLM Schemas
class TimeRange(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    label: Optional[str] = None  # e.g., 'this week', 'last month'

class OperationStep(BaseModel):
    tool: str  # "jira" or "github"
    action: str  # e.g. "search_issues", "get_commits", "list_projects", "get_recent_activity"
    filters: Optional[Dict[str, Any]] = None      # Accepts a JiraIssueFilter or GitHubFilter as dict
    sort_by: Optional[str] = None                 # e.g. "created", "updated"
    order: Optional[str] = None                   # "asc", "desc"
    output_keys: Optional[List[str]] = None       # Which fields to extract
    aggregation: Optional[str] = None             # e.g. "count", "group_by_status"

class AgentIntent(BaseModel):
    # Who/what is being queried
    members: Optional[List[str]] = None                   # ["Sarah", "John"]
    projects: Optional[List[str]] = None                  # ["PROJ", "API_BACKEND"]
    repositories: Optional[List[str]] = None              # ["repo1", "repo2"]
    organizations: Optional[List[str]] = None             # ["my-org"]

    # Stepwise operations (for chaining/filtering)
    operations: Optional[List[OperationStep]] = None      # Allow pipeline of actions

    # High-level modifiers
    time_range: Optional[TimeRange] = None
    limit: Optional[int] = None
    group_by: Optional[str] = None
    intent: Optional[str] = None               # e.g. "status", "list", "summarize", "compare"
    context: Optional[Dict[str, Any]] = None   # Memory/follow-up context

    # Error fields
    error_type: Optional[str] = None
    error_message: Optional[str] = None

class ToolCall(BaseModel):
    """Represents a single tool call to be executed by the agent."""
    tool: str
    action: str
    parameters: Dict[str, Any] = {}

class IrrelevantQueryError(BaseModel):
    """
    Represents a determination by the LLM that the user query is not
    relevant to the available JIRA or GitHub tools.
    """
    error: str = "Query is not relevant to JIRA or GitHub activity."
    reasoning: str

class IntentParserResponse(BaseModel):
    """
    Unified response schema for intent parsing that can handle both
    relevant and irrelevant queries.
    """
    is_relevant: bool
    agent_intent: Optional[AgentIntent] = None
    error: Optional[IrrelevantQueryError] = None
