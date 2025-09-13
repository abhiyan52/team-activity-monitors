import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.schemas import GitHubCommit, GitHubPullRequest, GitHubResponse, GitHubFilter

class GitHubClient:
    def __init__(self):
        self.token = settings.github_token
        self.organization = settings.github_organization
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def _is_configured(self) -> bool:
        """Check if GitHub client is properly configured"""
        return bool(self.token)
    
    def get_repositories(self) -> List[str]:
        """Get list of repositories for the organization or user"""
        if not self._is_configured():
            return []
        
        try:
            if self.organization:
                url = f"{self.base_url}/orgs/{self.organization}/repos"
            else:
                url = f"{self.base_url}/user/repos"
            
            response = self._make_request("GET", url, params={"per_page": 100})
            return [repo["name"] for repo in response]
            
        except Exception as e:
            print(f"Error fetching repositories: {e}")
            return []
    
    def get_commits(self, repositories: List[str], filters: GitHubFilter) -> List[GitHubCommit]:
        """Get commits from specified repositories"""
        if not self._is_configured():
            return []
        
        all_commits = []
        
        for repo_name in repositories:
            try:
                params = {"per_page": 30}
                
                if filters.author:
                    params["author"] = filters.author
                
                if filters.since:
                    params["since"] = filters.since.isoformat()
                
                if filters.branch:
                    params["sha"] = filters.branch
                
                owner = self.organization or self._get_authenticated_user()
                url = f"{self.base_url}/repos/{owner}/{repo_name}/commits"
                
                response = self._make_request("GET", url, params=params)
                
                for commit_data in response:
                    commit = GitHubCommit(
                        sha=commit_data["sha"],
                        message=commit_data["commit"]["message"],
                        author=commit_data["commit"]["author"]["name"],
                        date=datetime.fromisoformat(commit_data["commit"]["author"]["date"].replace("Z", "+00:00")),
                        url=commit_data["html_url"],
                        repository=repo_name
                    )
                    all_commits.append(commit)
                    
            except Exception as e:
                print(f"Error fetching commits for {repo_name}: {e}")
                continue
        
        return sorted(all_commits, key=lambda x: x.date, reverse=True)
    
    def get_pull_requests(self, repositories: List[str], filters: GitHubFilter) -> List[GitHubPullRequest]:
        """Get pull requests from specified repositories"""
        if not self._is_configured():
            return []
        
        all_prs = []
        
        for repo_name in repositories:
            try:
                params = {
                    "state": "all",
                    "per_page": 30,
                    "sort": "updated",
                    "direction": "desc"
                }
                
                owner = self.organization or self._get_authenticated_user()
                url = f"{self.base_url}/repos/{owner}/{repo_name}/pulls"
                
                response = self._make_request("GET", url, params=params)
                
                for pr_data in response:
                    # Filter by author if specified
                    if filters.author and pr_data["user"]["login"] != filters.author:
                        continue
                    
                    # Filter by date if specified
                    if filters.since:
                        updated_at = datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00"))
                        if updated_at < filters.since:
                            continue
                    
                    pr = GitHubPullRequest(
                        number=pr_data["number"],
                        title=pr_data["title"],
                        state=pr_data["state"],
                        author=pr_data["user"]["login"],
                        created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00")),
                        url=pr_data["html_url"],
                        repository=repo_name,
                        merged=pr_data["merged"],
                        merged_at=datetime.fromisoformat(pr_data["merged_at"].replace("Z", "+00:00")) if pr_data["merged_at"] else None
                    )
                    all_prs.append(pr)
                    
            except Exception as e:
                print(f"Error fetching pull requests for {repo_name}: {e}")
                continue
        
        return sorted(all_prs, key=lambda x: x.updated_at, reverse=True)
    
    def get_recent_activity(self, days: int = 7, team_members: Optional[List[str]] = None, repositories: Optional[List[str]] = None) -> GitHubResponse:
        """Get recent GitHub activity"""
        if not repositories:
            repositories = self.get_repositories()
        
        filters = GitHubFilter(since=datetime.now() - timedelta(days=days))
        
        all_commits = []
        all_prs = []
        
        if team_members:
            for member in team_members:
                member_filters = GitHubFilter(
                    author=member,
                    since=filters.since
                )
                member_commits = self.get_commits(repositories, member_filters)
                member_prs = self.get_pull_requests(repositories, member_filters)
                all_commits.extend(member_commits)
                all_prs.extend(member_prs)
        else:
            all_commits = self.get_commits(repositories, filters)
            all_prs = self.get_pull_requests(repositories, filters)
        
        return GitHubResponse(
            commits=all_commits,
            pull_requests=all_prs,
            repositories=repositories
        )
    
    def _get_authenticated_user(self) -> str:
        """Get the username of the authenticated user"""
        try:
            response = self._make_request("GET", f"{self.base_url}/user")
            return response["login"]
        except Exception:
            return "unknown"
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to GitHub API"""
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def test_connection(self) -> bool:
        """Test GitHub connection"""
        if not self._is_configured():
            return False
        
        try:
            response = self._make_request("GET", f"{self.base_url}/user")
            return bool(response.get("login"))
        except Exception:
            return False
