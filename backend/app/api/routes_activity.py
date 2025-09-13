from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from app.clients.jira_client import JiraClient
from app.clients.github_client import GitHubClient
from app.utils.query_parser import QueryParser
from app.core.response_templates import ResponseGenerator
from app.models.schemas import ActivityQueryRequest, ActivitySummary, JiraIssueFilter, GitHubFilter

router = APIRouter()
jira_client = JiraClient()
github_client = GitHubClient()
query_parser = QueryParser()
response_generator = ResponseGenerator()

@router.post("/query", response_model=ActivitySummary)
def query_team_activity(request: ActivityQueryRequest):
    """Main endpoint for querying team activity with natural language"""
    try:
        # Parse the query
        parsed_query = query_parser.parse_query(request.query)
        
        # Use parsed info or fallback to request parameters
        team_members = request.team_members or parsed_query.get("team_members")
        date_range = None
        
        # Handle date range from request or parsed query
        if request.date_range:
            date_range = {
                "start": datetime.fromisoformat(request.date_range["start"]),
                "end": datetime.fromisoformat(request.date_range["end"])
            }
        elif parsed_query.get("date_range"):
            date_range = parsed_query["date_range"]
        
        # Determine which sources to query
        sources = parsed_query["data_sources"]
        
        # Initialize responses
        jira_response = None
        github_response = None
        
        # Query JIRA if needed
        if sources["jira"]:
            jira_filters = JiraIssueFilter(
                project_key=parsed_query.get("project_key"),
                assignee=team_members[0] if team_members and len(team_members) == 1 else None,
                status=parsed_query.get("status"),
                updated_after=date_range["start"] if date_range else None
            )
            
            if team_members and len(team_members) > 1:
                # Handle multiple team members
                jira_response = jira_client.get_recent_activity(
                    days=7 if not date_range else None,
                    team_members=team_members
                )
            else:
                jira_response = jira_client.search_issues(jira_filters)
        
        # Query GitHub if needed
        if sources["github"]:
            github_filters = GitHubFilter(
                repository=parsed_query.get("repository"),
                since=date_range["start"] if date_range else None
            )
            
            repositories = [parsed_query["repository"]] if parsed_query.get("repository") else None
            
            github_response = github_client.get_recent_activity(
                days=7 if not date_range else None,
                team_members=team_members,
                repositories=repositories
            )
        
        # Create combined activity data
        activity_data = {}
        if jira_response:
            activity_data["jira"] = {
                "issues": [issue.dict() for issue in jira_response.issues],
                "total_count": jira_response.total_count,
                "filtered_count": jira_response.filtered_count
            }
        
        if github_response:
            activity_data["github"] = {
                "commits": [commit.dict() for commit in github_response.commits],
                "pull_requests": [pr.dict() for pr in github_response.pull_requests],
                "repositories": github_response.repositories
            }
        
        # Generate natural language summary
        summary_text = response_generator.generate_activity_summary(activity_data)
        
        # Create activity summary response
        return ActivitySummary(
            jira=jira_response or JiraClient().search_issues(JiraIssueFilter()),
            github=github_response or GitHubClient().get_recent_activity(),
            summary_text=summary_text,
            generated_at=datetime.now(),
            query_metadata={
                "original_query": request.query,
                "parsed_info": parsed_query,
                "team_members": team_members,
                "date_range": {
                    "start": date_range["start"].isoformat() if date_range else None,
                    "end": date_range["end"].isoformat() if date_range else None
                } if date_range else None
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")

@router.get("/status", response_model=Dict[str, Any])
def get_system_status():
    """Get the status of all integrated systems"""
    jira_status = jira_client.test_connection()
    github_status = github_client.test_connection()
    
    return {
        "jira": {
            "configured": jira_client._is_configured(),
            "connected": jira_status,
            "status": "healthy" if jira_status else "unhealthy"
        },
        "github": {
            "configured": github_client._is_configured(),
            "connected": github_status,
            "status": "healthy" if github_status else "unhealthy"
        },
        "overall_status": "healthy" if (jira_status or github_status) else "unhealthy",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/parse-query", response_model=Dict[str, Any])
def parse_natural_language_query(query: str):
    """Parse a natural language query and return extracted information"""
    try:
        return query_parser.parse_query(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing query: {e}")

@router.get("/recent-summary", response_model=ActivitySummary)
def get_recent_activity_summary(days: int = 7):
    """Get a summary of recent activity across all systems"""
    try:
        # Get recent activity from both sources
        jira_response = jira_client.get_recent_activity(days=days)
        github_response = github_client.get_recent_activity(days=days)
        
        # Create combined activity data
        activity_data = {
            "jira": {
                "issues": [issue.dict() for issue in jira_response.issues],
                "total_count": jira_response.total_count,
                "filtered_count": jira_response.filtered_count
            },
            "github": {
                "commits": [commit.dict() for commit in github_response.commits],
                "pull_requests": [pr.dict() for pr in github_response.pull_requests],
                "repositories": github_response.repositories
            }
        }
        
        # Generate summary
        summary_text = response_generator.generate_activity_summary(activity_data)
        
        return ActivitySummary(
            jira=jira_response,
            github=github_response,
            summary_text=summary_text,
            generated_at=datetime.now(),
            query_metadata={
                "original_query": f"Recent activity summary for last {days} days",
                "parsed_info": {"data_sources": {"jira": True, "github": True}},
                "team_members": None,
                "date_range": None
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recent summary: {e}")
