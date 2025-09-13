from github import Github
from github.GithubException import GithubException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.schemas import GitHubCommit, GitHubPullRequest, GitHubResponse, GitHubFilter


class GitHubClient:
    def __init__(self):
        self.token = settings.github_token
        self.organization = settings.github_organization
        self.github = None
        
        if self.token:
            try:
                self.github = Github(self.token)
            except GithubException as e:
                print(f"Failed to initialize GitHub client: {e}")
                self.github = None
    
    def _is_configured(self) -> bool:
        """Check if GitHub client is properly configured"""
        return bool(self.token and self.github)
    
    def get_repositories(self) -> List[str]:
        """Get list of repositories for the organization or user"""
        if not self._is_configured():
            return []
        
        try:
            repos = []
            if self.organization:
                # Get repositories from organization
                org = self.github.get_organization(self.organization)
                for repo in org.get_repos():
                    repos.append(repo.name)
            else:
                # Get repositories for authenticated user
                for repo in self.github.get_user().get_repos():
                    repos.append(repo.name)
            
            return repos
            
        except GithubException as e:
            print(f"Error fetching repositories: {e}")
            return []
    
    def get_repository_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about repositories"""
        if not self._is_configured():
            return []
        
        try:
            repos = []
            if self.organization:
                # Get repositories from organization
                org = self.github.get_organization(self.organization)
                repo_list = org.get_repos()
            else:
                # Get repositories for authenticated user
                repo_list = self.github.get_user().get_repos()
            
            for repo in repo_list:
                repos.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "private": repo.private,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "html_url": repo.html_url
                })
            
            return repos
            
        except GithubException as e:
            print(f"Error fetching repository details: {e}")
            return []
    
    def get_commits(self, repositories: List[str], filters: GitHubFilter) -> List[GitHubCommit]:
        """Get commits from specified repositories"""
        if not self._is_configured():
            return []
        
        all_commits = []
        
        for repo_name in repositories:
            try:
                # Get repository object
                if self.organization:
                    repo = self.github.get_repo(f"{self.organization}/{repo_name}")
                else:
                    user = self.github.get_user()
                    repo = self.github.get_repo(f"{user.login}/{repo_name}")
                
                # Build parameters for commit query
                kwargs = {}
                
                if filters.author:
                    kwargs["author"] = filters.author
                
                if filters.since:
                    kwargs["since"] = filters.since
                
                if filters.branch:
                    kwargs["sha"] = filters.branch
                
                # Get commits
                commits = repo.get_commits(**kwargs)
                
                # Limit to avoid too many API calls
                commit_count = 0
                max_commits = 30
                
                for commit in commits:
                    if commit_count >= max_commits:
                        break
                    
                    github_commit = GitHubCommit(
                        sha=commit.sha,
                        message=commit.commit.message,
                        author=commit.commit.author.name,
                        date=commit.commit.author.date,
                        url=commit.html_url,
                        repository=repo_name
                    )
                    all_commits.append(github_commit)
                    commit_count += 1
                    
            except GithubException as e:
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
                # Get repository object
                if self.organization:
                    repo = self.github.get_repo(f"{self.organization}/{repo_name}")
                else:
                    user = self.github.get_user()
                    repo = self.github.get_repo(f"{user.login}/{repo_name}")
                
                # Get pull requests
                prs = repo.get_pulls(state='all', sort='updated', direction='desc')
                
                # Limit to avoid too many API calls
                pr_count = 0
                max_prs = 30
                
                for pr in prs:
                    if pr_count >= max_prs:
                        break
                    
                    # Filter by author if specified
                    if filters.author and pr.user.login != filters.author:
                        continue
                    
                    # Filter by date if specified
                    if filters.since:
                        # Ensure both datetimes are timezone-aware for comparison
                        pr_updated = pr.updated_at
                        if pr_updated.tzinfo is None:
                            pr_updated = pr_updated.replace(tzinfo=filters.since.tzinfo)
                        elif filters.since.tzinfo is None:
                            filters_since = filters.since.replace(tzinfo=pr_updated.tzinfo)
                        else:
                            filters_since = filters.since
                        
                        if pr_updated < filters_since:
                            continue
                    
                    github_pr = GitHubPullRequest(
                        number=pr.number,
                        title=pr.title,
                        state=pr.state,
                        author=pr.user.login,
                        created_at=pr.created_at,
                        updated_at=pr.updated_at,
                        url=pr.html_url,
                        repository=repo_name,
                        merged=pr.merged,
                        merged_at=pr.merged_at
                    )
                    all_prs.append(github_pr)
                    pr_count += 1
                    
            except GithubException as e:
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
    
    def get_user_info(self, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get information about a GitHub user"""
        if not self._is_configured():
            return None
        
        try:
            if username:
                user = self.github.get_user(username)
            else:
                user = self.github.get_user()
            
            return {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "company": user.company,
                "location": user.location,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "html_url": user.html_url
            }
            
        except GithubException as e:
            print(f"Error fetching user info: {e}")
            return None
    
    def get_user_organizations(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get organizations for a user"""
        if not self._is_configured():
            return []
        
        try:
            if username:
                user = self.github.get_user(username)
            else:
                user = self.github.get_user()
            
            orgs = []
            for org in user.get_orgs():
                orgs.append({
                    "login": org.login,
                    "name": org.name,
                    "description": org.description,
                    "avatar_url": org.avatar_url,
                    "html_url": org.html_url
                })
            
            return orgs
            
        except GithubException as e:
            print(f"Error fetching user organizations: {e}")
            return []
    
    def get_repository_contributors(self, repository: str) -> List[Dict[str, Any]]:
        """Get contributors for a repository"""
        if not self._is_configured():
            return []
        
        try:
            # Get repository object
            if self.organization:
                repo = self.github.get_repo(f"{self.organization}/{repository}")
            else:
                user = self.github.get_user()
                repo = self.github.get_repo(f"{user.login}/{repository}")
            
            contributors = []
            for contrib in repo.get_contributors():
                contributors.append({
                    "login": contrib.login,
                    "name": contrib.name,
                    "avatar_url": contrib.avatar_url,
                    "contributions": contrib.contributions,
                    "html_url": contrib.html_url
                })
            
            return contributors
            
        except GithubException as e:
            print(f"Error fetching repository contributors: {e}")
            return []
    
    def get_repository_issues(self, repository: str, creator: Optional[str] = None, state: str = "all") -> List[Dict[str, Any]]:
        """Get issues for a repository"""
        if not self._is_configured():
            return []
        
        try:
            # Get repository object
            if self.organization:
                repo = self.github.get_repo(f"{self.organization}/{repository}")
            else:
                user = self.github.get_user()
                repo = self.github.get_repo(f"{user.login}/{repository}")
            
            kwargs = {"state": state}
            if creator:
                kwargs["creator"] = creator
            
            issues = []
            issue_count = 0
            max_issues = 50
            
            for issue in repo.get_issues(**kwargs):
                if issue_count >= max_issues:
                    break
                
                # Skip pull requests (they appear as issues in GitHub API)
                if issue.pull_request:
                    continue
                
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "author": issue.user.login,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "body": issue.body,
                    "labels": [label.name for label in issue.labels],
                    "html_url": issue.html_url
                })
                issue_count += 1
            
            return issues
            
        except GithubException as e:
            print(f"Error fetching repository issues: {e}")
            return []
    
    def _get_authenticated_user(self) -> str:
        """Get the username of the authenticated user"""
        if not self._is_configured():
            return "unknown"
        
        try:
            user = self.github.get_user()
            return user.login
        except GithubException:
            return "unknown"
    
    def test_connection(self) -> bool:
        """Test GitHub connection"""
        if not self._is_configured():
            return False
        
        try:
            user = self.github.get_user()
            return bool(user.login)
        except GithubException:
            return False