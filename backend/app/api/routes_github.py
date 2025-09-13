from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from app.clients.github_client import GitHubClient
from app.models.schemas import GitHubResponse, GitHubFilter

router = APIRouter()
github_client = GitHubClient()

@router.get("/health", response_model=dict)
def check_github_health():
    """Check if GitHub client is properly configured and can connect"""
    is_connected = github_client.test_connection()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "configured": github_client._is_configured(),
        "connected": is_connected
    }

@router.get("/repositories", response_model=List[str])
def get_repositories():
    """Get list of available repositories"""
    try:
        return github_client.get_repositories()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching repositories: {e}")

@router.get("/commits", response_model=List[dict])
def get_commits(
    repositories: Optional[List[str]] = Query(None, description="List of repository names"),
    author: Optional[str] = Query(None, description="Commit author"),
    since: Optional[str] = Query(None, description="Since date (YYYY-MM-DD)"),
    branch: Optional[str] = Query(None, description="Branch name")
):
    """Get commits from repositories"""
    try:
        # Parse date string
        since_dt = None
        if since:
            since_dt = datetime.strptime(since, "%Y-%m-%d")
        
        # Use all repositories if none specified
        if not repositories:
            repositories = github_client.get_repositories()
        
        # Create filters
        filters = GitHubFilter(
            author=author,
            since=since_dt,
            branch=branch
        )
        
        commits = github_client.get_commits(repositories, filters)
        return [commit.dict() for commit in commits]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching commits: {e}")

@router.get("/pull-requests", response_model=List[dict])
def get_pull_requests(
    repositories: Optional[List[str]] = Query(None, description="List of repository names"),
    author: Optional[str] = Query(None, description="PR author"),
    since: Optional[str] = Query(None, description="Since date (YYYY-MM-DD)")
):
    """Get pull requests from repositories"""
    try:
        # Parse date string
        since_dt = None
        if since:
            since_dt = datetime.strptime(since, "%Y-%m-%d")
        
        # Use all repositories if none specified
        if not repositories:
            repositories = github_client.get_repositories()
        
        # Create filters
        filters = GitHubFilter(
            author=author,
            since=since_dt
        )
        
        pull_requests = github_client.get_pull_requests(repositories, filters)
        return [pr.dict() for pr in pull_requests]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pull requests: {e}")

@router.get("/recent-activity", response_model=GitHubResponse)
def get_recent_github_activity(
    days: int = Query(7, description="Number of days to look back"),
    team_members: Optional[List[str]] = Query(None, description="List of team member usernames"),
    repositories: Optional[List[str]] = Query(None, description="List of repository names")
):
    """Get recent GitHub activity for team members"""
    try:
        return github_client.get_recent_activity(
            days=days,
            team_members=team_members,
            repositories=repositories
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent GitHub activity: {e}")

@router.get("/user", response_model=dict)
def get_authenticated_user():
    """Get information about the authenticated GitHub user"""
    try:
        username = github_client._get_authenticated_user()
        return {"username": username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user info: {e}")
