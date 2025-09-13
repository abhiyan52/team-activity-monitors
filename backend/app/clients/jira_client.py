import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.schemas import JiraIssue, JiraResponse, JiraIssueFilter

class JiraClient:
    def __init__(self):
        self.server_url = settings.jira_server_url
        self.username = settings.jira_username
        self.api_token = settings.jira_api_token
        self.session = requests.Session()
        
        if self.username and self.api_token:
            self.session.auth = (self.username, self.api_token)
    
    def _is_configured(self) -> bool:
        """Check if JIRA client is properly configured"""
        return bool(self.server_url and self.username and self.api_token)
    
    def search_issues(self, filters: JiraIssueFilter, max_results: int = 50) -> JiraResponse:
        """Search for JIRA issues based on filters"""
        if not self._is_configured():
            return JiraResponse(issues=[], total_count=0, filtered_count=0)
        
        # Build JQL query
        jql_parts = []
        
        if filters.project_key:
            jql_parts.append(f"project = {filters.project_key}")
        
        if filters.assignee:
            jql_parts.append(f"assignee = '{filters.assignee}'")
        
        if filters.status:
            jql_parts.append(f"status = '{filters.status}'")
        
        if filters.issue_type:
            jql_parts.append(f"issuetype = '{filters.issue_type}'")
        
        if filters.created_after:
            date_str = filters.created_after.strftime("%Y-%m-%d")
            jql_parts.append(f"created >= '{date_str}'")
        
        if filters.updated_after:
            date_str = filters.updated_after.strftime("%Y-%m-%d")
            jql_parts.append(f"updated >= '{date_str}'")
        
        jql = " AND ".join(jql_parts) if jql_parts else "order by updated DESC"
        
        try:
            response = self._make_request(
                "GET",
                f"{self.server_url}/rest/api/2/search",
                params={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "key,summary,status,assignee,priority,issuetype,created,updated,description"
                }
            )
            
            issues = []
            for issue_data in response.get("issues", []):
                fields = issue_data["fields"]
                
                issue = JiraIssue(
                    key=issue_data["key"],
                    summary=fields.get("summary", ""),
                    status=fields.get("status", {}).get("name", "Unknown"),
                    assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                    priority=fields.get("priority", {}).get("name") if fields.get("priority") else None,
                    issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
                    created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")),
                    updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")),
                    description=fields.get("description", ""),
                    url=f"{self.server_url}/browse/{issue_data['key']}"
                )
                issues.append(issue)
            
            return JiraResponse(
                issues=issues,
                total_count=response.get("total", 0),
                filtered_count=len(issues)
            )
            
        except Exception as e:
            print(f"Error fetching JIRA issues: {e}")
            return JiraResponse(issues=[], total_count=0, filtered_count=0)
    
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
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to JIRA API"""
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def test_connection(self) -> bool:
        """Test JIRA connection"""
        if not self._is_configured():
            return False
        
        try:
            response = self._make_request("GET", f"{self.server_url}/rest/api/2/myself")
            return bool(response.get("accountId"))
        except Exception:
            return False
