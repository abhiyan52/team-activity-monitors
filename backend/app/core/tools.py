from langchain_core.tools import tool
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from app.clients.jira_client import JiraClient
from app.clients.github_client import GitHubClient
from app.models.schemas import JiraIssueFilter


# Initialize clients
jira_client = JiraClient()
github_client = GitHubClient()


@tool("search_jira_issues")
def search_jira_issues(
    project_key: Optional[str] = None, 
    assignee: Optional[str] = None, 
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    max_results: int = 50
) -> str:
    """
    Search JIRA issues with flexible filtering. ALL PARAMETERS ARE OPTIONAL - you can search with any combination or none at all.
    
    IMPORTANT: You don't need to find all information before searching. Start with whatever information is available:
    - If user mentions a person's name, use that as assignee
    - If user mentions a project, use that as project_key  
    - If user mentions issue type (bug, story, task), use that as issue_type
    - If user mentions status (in progress, done, etc.), use that as status
    - If no parameters provided, searches ALL issues (limited by max_results)
    
    Common usage patterns:
    - search_jira_issues(assignee="john.doe") - Find all issues for John
    - search_jira_issues(issue_type="Bug") - Find all bugs across all projects
    - search_jira_issues(project_key="PROJ", status="In Progress") - Find in-progress issues in PROJ
    - search_jira_issues() - Get recent issues across all projects
    
    Args:
        project_key (optional): JIRA project key like "PROJ", "API-BACKEND". If not provided, searches ALL projects.
        assignee (optional): User email, name, or account ID. Can be partial name like "john" or full email.
        status (optional): Issue status like "In Progress", "Done", "To Do", "In Review", "Open", "Closed".
        issue_type (optional): Issue type like "Story", "Bug", "Task", "Epic", "Sub-task", "Improvement".
        max_results (optional): Maximum results to return (default: 50, max recommended: 100).
    
    Returns:
        JSON string with issue details including keys, summaries, statuses, assignees, and URLs.
    """
    try:
        # Create filter object
        filters = JiraIssueFilter(
            project_key=project_key,
            assignee=assignee,
            status=status,
            issue_type=issue_type
        )
        
        # Search issues
        response = jira_client.search_issues(filters, max_results)
        
        # Convert to serializable format
        result = {
            "total_count": response.total_count,
            "filtered_count": response.filtered_count,
            "issues": [
                {
                    "key": issue.key,
                    "summary": issue.summary,
                    "status": issue.status,
                    "assignee": issue.assignee,
                    "priority": issue.priority,
                    "issue_type": issue.issue_type,
                    "created": issue.created.isoformat() if issue.created else None,
                    "updated": issue.updated.isoformat() if issue.updated else None,
                    "url": issue.url
                }
                for issue in response.issues
            ]
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to search JIRA issues: {str(e)}",
            "total_count": 0,
            "filtered_count": 0,
            "issues": []
        })


@tool("get_github_commits")
def get_github_commits(
    repositories: Optional[List[str]] = None, 
    author: Optional[str] = None,
    since_days: int = 7,
    branch: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    Get GitHub commits with flexible filtering. ALL PARAMETERS ARE OPTIONAL.
    
    IMPORTANT: You can search commits immediately with whatever information you have:
    - If user mentions a person's name, use that as author
    - If user mentions repositories, use that as repositories list
    - If user mentions a time period, adjust since_days accordingly
    - If no parameters provided, gets commits from ALL repositories for the specified time period
    
    Time period examples:
    - "last week" or "past week" -> since_days=7
    - "last month" or "past month" -> since_days=30  
    - "yesterday" -> since_days=1
    - "last 3 days" -> since_days=3
    - "this year" -> since_days=365
    
    Common usage patterns:
    - get_github_commits(author="john") - All commits by John in last 7 days
    - get_github_commits(repositories=["my-app"]) - All commits in my-app repository
    - get_github_commits(author="john", since_days=30) - John's commits in last month
    - get_github_commits(since_days=1) - All commits from yesterday
    
    Args:
        repositories (optional): List of repository names like ["my-app", "frontend"]. If not provided, searches ALL repositories.
        author (optional): GitHub username, can be partial like "john" or full username "john.doe".
        since_days (optional): Days to look back (default: 7). Use 1=yesterday, 7=week, 30=month, 365=year.
        branch (optional): Branch name like "main", "develop", "feature-branch". If not provided, uses default branch.
        limit (optional): Maximum commits to return per repository (default: 100).
    
    Returns:
        JSON string with commit details including messages, authors, dates, and repository names.
    """
    try:
        # Calculate since date
        since_date = datetime.now() - timedelta(days=since_days) if since_days else None
        
        # Get commits using new client method
        commits = github_client.get_commits(
            author=author,
            repositories=repositories,
            since=since_date,
            branch=branch,
            limit=limit
        )
        
        # Convert to serializable format
        result = {
            "commit_count": len(commits),
            "commits": commits
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get GitHub commits: {str(e)}",
            "commits": []
        })


@tool("get_recent_activity")
def get_recent_activity(
    team_members: Optional[List[str]] = None,
    days: int = 7,
    repositories: Optional[List[str]] = None,
    projects: Optional[List[str]] = None
) -> str:
    """
    Get comprehensive recent activity from both JIRA and GitHub. ALL PARAMETERS ARE OPTIONAL.
    
    IMPORTANT: This is a powerful summary tool that works with any combination of parameters:
    - If user mentions people, use team_members list
    - If user mentions specific repos, use repositories list  
    - If user mentions projects, use projects list
    - If user mentions time period, adjust days
    - If NO parameters provided, gets activity for ALL team members across ALL projects and repositories
    
    This tool automatically combines:
    - JIRA issues (created, updated, assigned)
    - GitHub commits (authored by team members)
    - GitHub pull requests (created, updated by team members)
    - Activity summary with counts and statistics
    
    Time period examples:
    - "this week" -> days=7
    - "last month" -> days=30
    - "yesterday" -> days=1
    - "last 2 weeks" -> days=14
    
    Common usage patterns:
    - get_recent_activity(team_members=["john", "jane"]) - Activity for John and Jane
    - get_recent_activity(days=30) - All team activity in last month
    - get_recent_activity(team_members=["john"], repositories=["my-app"]) - John's activity in my-app
    - get_recent_activity() - Complete team activity overview for last week
    
    Args:
        team_members (optional): List of usernames/emails like ["john.doe", "jane.smith"]. If not provided, includes ALL team members.
        days (optional): Days to look back (default: 7). Use 1=yesterday, 7=week, 30=month.
        repositories (optional): List of GitHub repo names like ["frontend", "backend"]. If not provided, searches ALL repositories.
        projects (optional): List of JIRA project keys like ["PROJ", "API"]. If not provided, searches ALL projects.
    
    Returns:
        JSON string with comprehensive activity summary including JIRA issues, GitHub commits, PRs, and statistics.
    """
    try:
        result = {
            "period_days": days,
            "team_members": team_members or [],
            "jira_activity": {},
            "github_activity": {},
            "summary": {}
        }
        
        # Get JIRA activity
        try:
            jira_response = jira_client.get_recent_activity(days=days, team_members=team_members)
            result["jira_activity"] = {
                "total_issues": jira_response.total_count,
                "filtered_issues": jira_response.filtered_count,
                "issues": [
                    {
                        "key": issue.key,
                        "summary": issue.summary,
                        "status": issue.status,
                        "assignee": issue.assignee,
                        "updated": issue.updated.isoformat() if issue.updated else None
                    }
                    for issue in jira_response.issues
                ]
            }
        except Exception as e:
            result["jira_activity"] = {"error": f"Failed to get JIRA activity: {str(e)}"}
        
        # Get GitHub activity
        try:
            if team_members:
                github_activities = github_client.get_recent_activities(
                    usernames=team_members,
                    days=days,
                    include_commits=True,
                    include_prs=True,
                    repositories=repositories
                )
                result["github_activity"] = github_activities
            else:
                # If no team members specified, get general activity
                commits = github_client.get_commits(
                    repositories=repositories,
                    since=datetime.now() - timedelta(days=days),
                    limit=50
                )
                prs = github_client.get_pull_requests(
                    repositories=repositories,
                    since=datetime.now() - timedelta(days=days),
                    limit=50
                )
                result["github_activity"] = {
                    "commits": commits[:10],  # Limit to first 10
                    "pull_requests": prs[:10],  # Limit to first 10
                    "commit_count": len(commits),
                    "pr_count": len(prs)
                }
        except Exception as e:
            result["github_activity"] = {"error": f"Failed to get GitHub activity: {str(e)}"}
        
        # Generate summary
        jira_count = result["jira_activity"].get("filtered_issues", 0)
        github_commits = result["github_activity"].get("commit_count", 0)
        github_prs = result["github_activity"].get("pr_count", 0)
        
        result["summary"] = {
            "total_jira_issues": jira_count,
            "total_github_commits": github_commits,
            "total_github_prs": github_prs,
            "most_active_members": team_members[:3] if team_members else []
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get recent activity: {str(e)}",
            "jira_activity": {},
            "github_activity": {},
            "summary": {}
        })


@tool("get_jira_projects")
def get_jira_projects() -> str:
    """
    Get list of all JIRA projects. No parameters needed.
    
    IMPORTANT: This tool retrieves ALL available JIRA projects that the authenticated user has access to.
    Use this when user asks about:
    - "What projects are available?"
    - "List all JIRA projects"
    - "Show me the projects"
    - Or when you need to find project keys for other searches
    
    Returns:
        JSON string with project details including keys, names, IDs, and project leads.
    """
    try:
        projects = jira_client.get_projects()
        result = {
            "project_count": len(projects),
            "projects": projects
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get JIRA projects: {str(e)}",
            "projects": []
        })


@tool("get_jira_project_users")
def get_jira_project_users(project_key: str, max_results: int = 50) -> str:
    """
    Get list of assignable users for a specific JIRA project.
    
    IMPORTANT: Use this when you need to find who can be assigned to issues in a specific project.
    Common usage:
    - "Who can work on the PROJ project?"
    - "List team members for API project"
    - Finding valid assignee names for issue searches
    
    Args:
        project_key (required): JIRA project key like "PROJ", "API-BACKEND".
        max_results (optional): Maximum number of users to return (default: 50).
    
    Returns:
        JSON string with user details including account IDs, display names, and email addresses.
    """
    try:
        users = jira_client.get_project_users(project_key, max_results)
        result = {
            "project_key": project_key,
            "user_count": len(users),
            "users": users
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get project users: {str(e)}",
            "project_key": project_key,
            "users": []
        })


@tool("search_jira_users")
def search_jira_users(query: str, max_results: int = 20) -> str:
    """
    Search for JIRA users by name or email.
    
    IMPORTANT: Use this to find users across all JIRA when you have partial information:
    - User mentions a partial name like "john" or "sarah"
    - You need to find the correct assignee format
    - Looking up team members by name
    
    Args:
        query (required): Search query like "john", "sarah.smith", or "john@company.com".
        max_results (optional): Maximum number of results (default: 20).
    
    Returns:
        JSON string with matching users including account IDs, display names, and email addresses.
    """
    try:
        users = jira_client.search_users(query, max_results)
        result = {
            "query": query,
            "user_count": len(users),
            "users": users
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to search users: {str(e)}",
            "query": query,
            "users": []
        })


@tool("get_jira_issue_details")
def get_jira_issue_details(issue_key: str) -> str:
    """
    Get detailed information about a specific JIRA issue including comments and transitions.
    
    IMPORTANT: Use this when user asks for specific issue details:
    - "Tell me about issue PROJ-123"
    - "What's the status of PROJ-456?"
    - "Show me comments on this issue"
    - Getting full context about a particular issue
    
    Args:
        issue_key (required): JIRA issue key like "PROJ-123", "API-456".
    
    Returns:
        JSON string with complete issue details including description, comments, and available transitions.
    """
    try:
        issue_details = jira_client.get_issue_details(issue_key)
        if not issue_details:
            return json.dumps({
                "error": f"Issue {issue_key} not found or not accessible",
                "issue_key": issue_key
            })
        
        return json.dumps(issue_details, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get issue details: {str(e)}",
            "issue_key": issue_key
        })


@tool("get_github_repositories")
def get_github_repositories() -> str:
    """
    Get all repositories with contributors. No parameters needed.
    
    IMPORTANT: Use this when you need repository information with contributors:
    - "What repositories are available?"
    - "List all repos with contributors"
    - "Show me repository details and team members"
    - Finding repository names and contributor information for other GitHub operations
    
    Returns:
        JSON string with repository details including contributors, languages, and metadata.
    """
    try:
        repos = github_client.get_repositories_with_contributors()
        result = {
            "repository_count": len(repos),
            "repositories": repos
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get repositories: {str(e)}",
            "repositories": []
        })


@tool("get_github_repository_details")
def get_github_repository_details(repository: str) -> str:
    """
    Get detailed information about a specific repository including contributors, releases, branches, etc.
    
    IMPORTANT: Use this when user wants comprehensive information about a specific repository:
    - "Tell me about the frontend repository"
    - "What's in the my-app repo?"
    - "Show me details for backend project"
    - Repository statistics, contributors, releases, and branches
    
    Args:
        repository (required): Repository name like "frontend", "my-app", "backend".
    
    Returns:
        JSON string with detailed repository information including contributors, releases, branches, languages.
    """
    try:
        repo_details = github_client.get_repository_details(repository)
        if not repo_details:
            return json.dumps({
                "error": f"Repository '{repository}' not found or not accessible",
                "repository": repository
            })
        
        return json.dumps(repo_details, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get repository details: {str(e)}",
            "repository": repository
        })


@tool("get_github_pull_requests")
def get_github_pull_requests(
    repositories: Optional[List[str]] = None,
    author: Optional[str] = None,
    since_days: int = 7,
    state: str = "all",
    limit: int = 100
) -> str:
    """
    Get GitHub pull requests with flexible filtering. ALL PARAMETERS ARE OPTIONAL.
    
    IMPORTANT: Use this for PR-specific queries:
    - "Show me recent pull requests"
    - "What PRs has John created?"
    - "List PRs for the frontend repo"
    - "Show me open pull requests"
    - PR activity and status tracking
    
    Args:
        repositories (optional): List of repo names like ["frontend", "backend"]. If not provided, searches ALL repositories.
        author (optional): GitHub username for PR author filtering.
        since_days (optional): Days to look back (default: 7). Use 1=yesterday, 7=week, 30=month.
        state (optional): PR state - "open", "closed", "all" (default: "all").
        limit (optional): Maximum PRs to return per repository (default: 100).
    
    Returns:
        JSON string with PR details including numbers, titles, states, authors, and merge status.
    """
    try:
        # Calculate since date
        since_date = datetime.now() - timedelta(days=since_days) if since_days else None
        
        # Get pull requests using new client method
        prs = github_client.get_pull_requests(
            author=author,
            repositories=repositories,
            state=state,
            since=since_date,
            limit=limit
        )
        
        result = {
            "pr_count": len(prs),
            "pull_requests": prs
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get pull requests: {str(e)}",
            "pull_requests": []
        })


@tool("get_github_recent_activities")
def get_github_recent_activities(
    usernames: List[str],
    days: int = 7,
    include_commits: bool = True,
    include_prs: bool = True,
    repositories: Optional[List[str]] = None
) -> str:
    """
    Get recent GitHub activities for specified users with comprehensive tracking.
    
    IMPORTANT: Use this for detailed user activity analysis:
    - "What has John been working on lately?"
    - "Show me team activity for the past month"
    - "Track commits and PRs for specific users"
    - Comprehensive activity reporting and analytics
    
    Args:
        usernames (required): List of GitHub usernames like ["john.doe", "jane.smith"].
        days (optional): Days to look back (default: 7). Use 1=yesterday, 7=week, 30=month.
        include_commits (optional): Whether to include commit activities (default: True).
        include_prs (optional): Whether to include PR activities (default: True).
        repositories (optional): List of repository names to limit search.
    
    Returns:
        JSON string with comprehensive activity data including commits, PRs, and summary statistics.
    """
    try:
        activities = github_client.get_recent_activities(
            usernames=usernames,
            days=days,
            include_commits=include_commits,
            include_prs=include_prs,
            repositories=repositories
        )
        
        return json.dumps(activities, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get recent activities: {str(e)}",
            "activities": {}
        })


@tool("test_jira_connection")
def test_jira_connection() -> str:
    """
    Test JIRA connection and configuration status.
    
    IMPORTANT: Use this for troubleshooting JIRA connectivity:
    - "Is JIRA working?"
    - "Test JIRA connection"
    - Debugging JIRA access issues
    
    Returns:
        JSON string with connection status and configuration details.
    """
    try:
        is_configured = jira_client._is_configured()
        is_connected = jira_client.test_connection()
        
        result = {
            "configured": is_configured,
            "connected": is_connected,
            "status": "healthy" if (is_configured and is_connected) else "unhealthy",
            "message": "JIRA is properly configured and connected" if (is_configured and is_connected) 
                      else "JIRA configuration or connection issue"
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to test JIRA connection: {str(e)}",
            "configured": False,
            "connected": False,
            "status": "error"
        })


@tool("test_github_connection")
def test_github_connection() -> str:
    """
    Test GitHub connection and configuration status.
    
    IMPORTANT: Use this for troubleshooting GitHub connectivity:
    - "Is GitHub working?"
    - "Test GitHub connection"
    - Debugging GitHub access issues
    
    Returns:
        JSON string with connection status and configuration details.
    """
    try:
        is_configured = github_client._is_configured()
        is_connected = github_client.test_connection()
        
        result = {
            "configured": is_configured,
            "connected": is_connected,
            "status": "healthy" if (is_configured and is_connected) else "unhealthy",
            "message": "GitHub is properly configured and connected" if (is_configured and is_connected) 
                      else "GitHub configuration or connection issue"
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to test GitHub connection: {str(e)}",
            "configured": False,
            "connected": False,
            "status": "error"
        })


@tool("get_current_time")
def get_current_time(format_type: str = "datetime") -> str:
    """
    Get the current date and/or time in various formats.
    
    IMPORTANT: Use this when you need current date/time information:
    - "What's the current time?"
    - "What date is it today?"
    - "Get current timestamp"
    - For time-based filtering and date calculations
    
    Args:
        format_type (optional): Format type - "time", "date", "datetime", "timestamp", "iso" (default: "datetime").
            - "time": Returns time only (HH:MM:SS)
            - "date": Returns date only (YYYY-MM-DD)
            - "datetime": Returns date and time (YYYY-MM-DD HH:MM:SS)
            - "timestamp": Returns Unix timestamp
            - "iso": Returns ISO format (YYYY-MM-DDTHH:MM:SS)
    
    Returns:
        JSON string with current date/time information.
    """
    try:
        now = datetime.now()
        
        if format_type == "time":
            result = {
                "time": now.strftime("%H:%M:%S"),
                "format": "time",
                "description": "Current time only"
            }
        elif format_type == "date":
            result = {
                "date": now.strftime("%Y-%m-%d"),
                "format": "date", 
                "description": "Current date only"
            }
        elif format_type == "datetime":
            result = {
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "format": "datetime",
                "description": "Current date and time"
            }
        elif format_type == "timestamp":
            result = {
                "timestamp": int(now.timestamp()),
                "format": "timestamp",
                "description": "Unix timestamp"
            }
        elif format_type == "iso":
            result = {
                "iso": now.isoformat(),
                "format": "iso",
                "description": "ISO format datetime"
            }
        else:
            # Default to datetime if invalid format
            result = {
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "format": "datetime",
                "description": "Current date and time (default)",
                "note": f"Invalid format '{format_type}', used default 'datetime'"
            }
        
        # Add common formats for convenience
        result.update({
            "timezone": "local",
            "all_formats": {
                "time": now.strftime("%H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(now.timestamp()),
                "iso": now.isoformat()
            }
        })
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get current time: {str(e)}",
            "format_type": format_type
        })


# Export tools list
tools = [
    # Core activity tools
    search_jira_issues,
    get_github_commits,
    get_recent_activity,
    
    # JIRA-specific tools
    get_jira_projects,
    get_jira_project_users,
    search_jira_users,
    get_jira_issue_details,
    test_jira_connection,
    
    # GitHub-specific tools (updated for new client)
    get_github_repositories,
    get_github_repository_details,
    get_github_pull_requests,
    get_github_recent_activities,
    test_github_connection,
    
    # Utility tools
    get_current_time
]