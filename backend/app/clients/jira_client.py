from jira import JIRA
from jira.exceptions import JIRAError
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.schemas import JiraIssue, JiraResponse, JiraIssueFilter
from app.core.services.simple_cache import cached


class JiraClient:
    def __init__(self):
        self.server_url = settings.jira_server_url
        self.email = settings.jira_email
        self.api_token = settings.jira_api_token
        self.jira = None
        
        if self._is_configured():
            try:
                self.jira = JIRA(
                    server=self.server_url,
                    basic_auth=(self.email, self.api_token)
                )
            except JIRAError as e:
                print(f"Failed to initialize JIRA client: {e}")
                self.jira = None
    
    def _is_configured(self) -> bool:
        """Check if JIRA client is properly configured"""
        return bool(self.server_url and self.email and self.api_token)
    
    @cached(ttl=300)
    def search_issues(self, filters: JiraIssueFilter, max_results: int = 50) -> JiraResponse:
        """Search for JIRA issues based on filters"""
        if not self._is_configured() or not self.jira:
            return JiraResponse(issues=[], total_count=0, filtered_count=0)
        
        # Build JQL query
        jql_parts = []
        
        if filters.project_key:
            jql_parts.append(f"project = {filters.project_key}")
        
        if filters.assignee:
            # Handle both email and account ID formats
            if "@" in filters.assignee:
                # Try to find user by email first
                try:
                    users = self.jira.search_users(query=filters.assignee, maxResults=1)
                    if users:
                        jql_parts.append(f'assignee = "{users[0].accountId}"')
                    else:
                        jql_parts.append(f'assignee = "{filters.assignee}"')
                except JIRAError:
                    jql_parts.append(f'assignee = "{filters.assignee}"')
            else:
                jql_parts.append(f'assignee = "{filters.assignee}"')
        
        if filters.status:
            jql_parts.append(f'status = "{filters.status}"')
        
        if filters.issue_type:
            jql_parts.append(f'issuetype = "{filters.issue_type}"')
        
        if filters.created_after:
            date_str = filters.created_after.strftime("%Y-%m-%d")
            jql_parts.append(f"created >= '{date_str}'")
        
        if filters.updated_after:
            date_str = filters.updated_after.strftime("%Y-%m-%d")
            jql_parts.append(f"updated >= '{date_str}'")
        
        if jql_parts:
            jql = " AND ".join(jql_parts) + " order by updated DESC"
        else:
            # Add a default time restriction to avoid unbounded queries
            default_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            jql = f"updated >= '{default_date}' order by updated DESC"
        
        try:
            issues_result = self.jira.search_issues(
                jql_str=jql,
                maxResults=max_results,
                fields="key,summary,status,assignee,priority,issuetype,created,updated,description"
            )
            
            issues = []
            for issue in issues_result:
                jira_issue = JiraIssue(
                    key=issue.key,
                    summary=issue.fields.summary or "",
                    status=issue.fields.status.name if issue.fields.status else "Unknown",
                    assignee=issue.fields.assignee.displayName if issue.fields.assignee else None,
                    priority=issue.fields.priority.name if issue.fields.priority else None,
                    issue_type=issue.fields.issuetype.name if issue.fields.issuetype else "Unknown",
                    created=datetime.fromisoformat(str(issue.fields.created).replace("Z", "+00:00")),
                    updated=datetime.fromisoformat(str(issue.fields.updated).replace("Z", "+00:00")),
                    description=issue.fields.description or "",
                    url=f"{self.server_url}/browse/{issue.key}"
                )
                issues.append(jira_issue)
            
            return JiraResponse(
                issues=issues,
                total_count=issues_result.total,
                filtered_count=len(issues)
            )
            
        except JIRAError as e:
            print(f"Error fetching JIRA issues: {e}")
            return JiraResponse(issues=[], total_count=0, filtered_count=0)

    @cached(ttl=300)
    def get_recent_activity(self, days: int = 7, team_members: Optional[List[str]] = None) -> JiraResponse:
        """Get recent JIRA activity for team members"""
        filters = JiraIssueFilter(
            updated_after=datetime.now() - timedelta(days=days)
        )
        
        if team_members:
            # For multiple assignees, we'll need to make multiple requests or use a more complex JQL
            all_issues = []
            for member in team_members:
                member_filters = JiraIssueFilter(
                    assignee=member,
                    updated_after=filters.updated_after
                )
                member_response = self.search_issues(member_filters)
                all_issues.extend(member_response.issues)
            
            return JiraResponse(
                issues=all_issues,
                total_count=len(all_issues),
                filtered_count=len(all_issues)
            )
        
        return self.search_issues(filters)

    @cached(ttl=300)
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of all JIRA projects"""
        if not self._is_configured() or not self.jira:
            return []
        
        try:
            projects = self.jira.projects()
            return [
                {
                    "key": project.key,
                    "name": project.name,
                    "id": project.id,
                    "lead": project.lead.displayName if hasattr(project, 'lead') and project.lead else None
                }
                for project in projects
            ]
        except JIRAError as e:
            print(f"Error fetching JIRA projects: {e}")
            return []

    @cached(ttl=300)    
    def get_project_users(self, project_key: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get list of assignable users for a specific project"""
        if not self._is_configured() or not self.jira:
            return []
        
        try:
            users = self.jira.search_assignable_users_for_projects(
                username='',
                projectKeys=project_key,
                maxResults=max_results
            )
            return [
                {
                    "accountId": user.accountId,
                    "displayName": user.displayName,
                    "emailAddress": getattr(user, 'emailAddress', None),
                    "active": getattr(user, 'active', True)
                }
                for user in users
            ]
        except JIRAError as e:
            print(f"Error fetching project users: {e}")
            return []

    @cached(ttl=300)
    def search_users(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for users by name or email"""
        if not self._is_configured() or not self.jira:
            return []
        
        try:
            users = self.jira.search_users(query=query, maxResults=max_results)
            return [
                {
                    "accountId": user.accountId,
                    "displayName": user.displayName,
                    "emailAddress": getattr(user, 'emailAddress', None),
                    "active": getattr(user, 'active', True)
                }
                for user in users
            ]
        except JIRAError as e:
            print(f"Error searching users: {e}")
            return []

    @cached(ttl=300)    
    def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific issue"""
        if not self._is_configured() or not self.jira:
            return None
        
        try:
            issue = self.jira.issue(issue_key)
            
            # Get comments
            comments = []
            try:
                issue_comments = self.jira.comments(issue_key)
                comments = [
                    {
                        "author": comment.author.displayName,
                        "body": comment.body,
                        "created": str(comment.created)
                    }
                    for comment in issue_comments
                ]
            except JIRAError:
                # Comments might not be accessible
                pass
            
            # Get transitions
            transitions = []
            try:
                issue_transitions = self.jira.transitions(issue)
                transitions = [
                    {
                        "id": transition['id'],
                        "name": transition['name']
                    }
                    for transition in issue_transitions
                ]
            except JIRAError:
                # Transitions might not be accessible
                pass
            
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description or "",
                "status": issue.fields.status.name if issue.fields.status else "Unknown",
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "issue_type": issue.fields.issuetype.name if issue.fields.issuetype else "Unknown",
                "created": str(issue.fields.created),
                "updated": str(issue.fields.updated),
                "url": f"{self.server_url}/browse/{issue.key}",
                "comments": comments,
                "transitions": transitions
            }
            
        except JIRAError as e:
            print(f"Error fetching issue details: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test JIRA connection"""
        if not self._is_configured() or not self.jira:
            return False
        
        try:
            # Try to get current user info
            myself = self.jira.myself()
            return bool(myself.get('accountId'))
        except JIRAError:
            return False

    @property
    @cached(ttl=3600)
    def context(self) -> str:
        projects = self.get_projects()

        project_context = {"project_information": []}
        for project in projects:
            project["users"] = self.get_project_users(project["key"])
            project_context["project_information"].append(project)
        return project_context     
