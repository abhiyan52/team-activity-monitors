from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from app.clients.jira_client import JiraClient
from app.models.schemas import JiraResponse, JiraIssueFilter

router = APIRouter()
jira_client = JiraClient()

@router.get("/health", response_model=dict)
def check_jira_health():
    """Check if JIRA client is properly configured and can connect"""
    is_connected = jira_client.test_connection()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "configured": jira_client._is_configured(),
        "connected": is_connected
    }

@router.get("/issues", response_model=JiraResponse)
def get_jira_issues(
    project_key: Optional[str] = Query(None, description="JIRA project key"),
    assignee: Optional[str] = Query(None, description="Issue assignee"),
    status: Optional[str] = Query(None, description="Issue status"),
    issue_type: Optional[str] = Query(None, description="Issue type"),
    created_after: Optional[str] = Query(None, description="Created after date (YYYY-MM-DD)"),
    updated_after: Optional[str] = Query(None, description="Updated after date (YYYY-MM-DD)"),
    max_results: int = Query(50, description="Maximum number of results")
):
    """Get JIRA issues based on filters"""
    try:
        # Parse date strings
        created_after_dt = None
        updated_after_dt = None
        
        if created_after:
            created_after_dt = datetime.strptime(created_after, "%Y-%m-%d")
        
        if updated_after:
            updated_after_dt = datetime.strptime(updated_after, "%Y-%m-%d")
        
        # Create filters
        filters = JiraIssueFilter(
            project_key=project_key,
            assignee=assignee,
            status=status,
            issue_type=issue_type,
            created_after=created_after_dt,
            updated_after=updated_after_dt
        )
        
        return jira_client.search_issues(filters, max_results)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching JIRA issues: {e}")

@router.get("/recent-activity", response_model=JiraResponse)
def get_recent_jira_activity(
    days: int = Query(7, description="Number of days to look back"),
    team_members: Optional[List[str]] = Query(None, description="List of team member usernames"),
    max_results: int = Query(50, description="Maximum number of results")
):
    """Get recent JIRA activity for team members"""
    try:
        return jira_client.get_recent_activity(
            days=days,
            team_members=team_members
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent JIRA activity: {e}")

@router.get("/projects", response_model=List[dict])
def get_jira_projects():
    """Get list of available JIRA projects"""
    try:
        return jira_client.get_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching JIRA projects: {e}")

@router.get("/users", response_model=List[dict])
def get_jira_users(
    query: Optional[str] = Query(None, description="Search query for users"),
    project_key: Optional[str] = Query(None, description="Project key to get assignable users"),
    max_results: int = Query(20, description="Maximum number of results")
):
    """Get list of JIRA users (for team member suggestions)"""
    try:
        if project_key:
            return jira_client.get_project_users(project_key, max_results)
        elif query:
            return jira_client.search_users(query, max_results)
        else:
            # Return empty list if no search criteria provided
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching JIRA users: {e}")

@router.get("/issues/{issue_key}", response_model=dict)
def get_jira_issue_details(issue_key: str):
    """Get detailed information about a specific JIRA issue"""
    try:
        issue_details = jira_client.get_issue_details(issue_key)
        if not issue_details:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
        return issue_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching issue details: {e}")
