from github import Github
from github.GithubException import GithubException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.core.config import settings



class GitHubClient:
    def __init__(self):
        self.token = settings.github_token
        self.organization = settings.github_organization
        self.github = None
        self.github_repositories = settings.github_repo_names.split(",") if settings.github_repo_names else None
        self.github = Github(self.token)
    
    def _is_configured(self) -> bool:
        """Check if GitHub client is properly configured"""
        return bool(self.token and self.github)
    
    def _get_repo_full_name(self, repository: str) -> str:
        """Get full repository name (owner/repo)"""
        if "/" in repository:
            return repository
        
        if self.organization:
            return f"{self.organization}/{repository}"
        else:
            user = self.github.get_user()
            return f"{user.login}/{repository}"
        
    def get_pull_requests(
        self,
        author: Optional[str] = None,
        repositories: Optional[List[str]] = None,
        state: str = "all",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all pull requests with flexible filtering options.
        
        Args:
            author: Filter by PR author username
            repository: Single repository name to search
            repositories: List of repository names to search
            state: PR state - "open", "closed", "all" (default: "all")
            since: Get PRs updated after this date
            until: Get PRs updated before this date
            limit: Maximum number of PRs to return per repository (default: 100)
        
        Returns:
            List of pull request dictionaries with detailed information
        """
        if not self._is_configured():
            return []
        
        # Determine repositories to search
        search_repos = []
        if repositories:
            search_repos = repositories
        else:
            # Get all accessible repositories
            search_repos = self._get_all_repositories()
        
        all_prs = []

        
        for repo_name in search_repos:
            try:
                repo_full_name = self._get_repo_full_name(repo_name)
                repo = self.github.get_repo(repo_full_name)
                
                # Get pull requests with state filter
                prs = repo.get_pulls(state=state, sort='updated', direction='desc')
                
                pr_count = 0
                for pr in prs:
                    if pr_count >= limit:
                        break
                    
                    # Filter by author
                    if author and pr.user.login.lower() != author.lower():
                        continue
                    
                    # Filter by date range
                    if since:
                        # Make since timezone-aware if it's not already
                        since_aware = since.replace(tzinfo=timezone.utc) if since.tzinfo is None else since
                        if pr.updated_at < since_aware:
                            continue
                    if until:
                        # Make until timezone-aware if it's not already
                        until_aware = until.replace(tzinfo=timezone.utc) if until.tzinfo is None else until
                        if pr.updated_at > until_aware:
                            continue
                    
                    pr_data = {
                        "number": pr.number,
                        "title": pr.title,
                        "state": pr.state,
                        "author": pr.user.login,
                        "author_name": pr.user.name or pr.user.login,
                        "created_at": pr.created_at.isoformat() if pr.created_at else None,
                        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                        "merged": pr.merged,
                        "draft": pr.draft,
                        "url": pr.html_url,
                        "repository": repo_name,
                        "repository_full_name": repo_full_name,
                        "base_branch": pr.base.ref,
                        "head_branch": pr.head.ref,
                        "commits": pr.commits,
                        "additions": pr.additions,
                        "deletions": pr.deletions,
                        "changed_files": pr.changed_files,
                        "labels": [label.name for label in pr.labels],
                        "assignees": [assignee.login for assignee in pr.assignees],
                        "reviewers": [reviewer.login for reviewer in pr.requested_reviewers],
                        "body": pr.body or ""
                    }
                    all_prs.append(pr_data)
                    pr_count += 1
                    
            except GithubException as e:
                print(f"Error fetching pull requests for {repo_name}: {e}")
                continue

        # Sort by updated date (most recent first)
        return sorted(all_prs, key=lambda x: x['updated_at'] or '', reverse=True)

    def get_commits(
        self,
        author: Optional[str] = None,
        repositories: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        branch: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all commits with flexible filtering options.
        
        Args:
            author: Filter by commit author username or email
            repository: Single repository name to search
            repositories: List of repository names to search
            since: Get commits after this date
            until: Get commits before this date
            branch: Branch name to search (default: default branch)
            limit: Maximum number of commits to return per repository (default: 100)
        
        Returns:
            List of commit dictionaries with detailed information
        """
        if not self._is_configured():
            return []
        
        # Determine repositories to search
        search_repos = []
        if repositories:
            search_repos = repositories
        else:
            # Get all accessible repositories
            search_repos = self._get_all_repositories()
        
        all_commits = []
        
        for repo_name in search_repos:
            try:
                repo_full_name = self._get_repo_full_name(repo_name)
                repo = self.github.get_repo(repo_full_name)
                
                # Build commit query parameters
                kwargs = {}
                if author:
                    kwargs["author"] = author
                if since:
                    kwargs["since"] = since
                if until:
                    kwargs["until"] = until
                if branch:
                    kwargs["sha"] = branch
                
                # Get commits
                commits = repo.get_commits(**kwargs)
                
                commit_count = 0
                for commit in commits:
                    if commit_count >= limit:
                        break
                    
                    commit_data = {
                        "message": commit.commit.message,
                        "author": commit.commit.author.name,
                        "author_email": commit.commit.author.email,
                        "author_username": commit.author.login if commit.author else None,
                        "committer": commit.commit.committer.name,
                        "committer_email": commit.commit.committer.email,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None,
                        "url": commit.html_url,
                        "repository": repo_name,
                        "repository_full_name": repo_full_name
                    }
                    all_commits.append(commit_data)
                    commit_count += 1
                    
            except GithubException as e:
                print(f"Error fetching commits for {repo_name}: {e}")
                continue
        
        # Sort by date (most recent first)
        return sorted(all_commits, key=lambda x: x['date'] or '', reverse=True)

    def get_repositories_with_contributors(self) -> List[Dict[str, Any]]:
        """
        Get all accessible repositories along with their contributors.
        
        Returns:
            List of repository dictionaries with contributor information
        """
        if not self._is_configured():
            return []
        
        repositories = []
        
        try:
            # Get repositories
            if self.organization:
                org = self.github.get_organization(self.organization)
                repo_list = org.get_repos()
            else:
                repo_list = self.github.get_user().get_repos()

            
            for repo in repo_list:
                try:
                    if self.github_repositories and self._get_repo_full_name(repo.name) not in self.github_repositories:
                        continue

                    # Get contributors
                    contributors = []
                    for contributor in repo.get_contributors():

                        contributors.append({
                            "name": contributor.name or contributor.login,
                            "contributions": contributor.contributions,
                            "username": contributor.login
                        })
                    
                    # Get repository languages
                    languages = {}
                    try:
                        languages = repo.get_languages()
                    except GithubException:
                        pass

                    
                    repo_data = {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "private": repo.private,
                        "fork": repo.fork,
                        "language": repo.language,
                        "languages": languages,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "watchers": repo.watchers_count,
                        "size": repo.size,
                        "open_issues": repo.open_issues_count,
                        "default_branch": repo.default_branch,
                        "created_at": repo.created_at.isoformat() if repo.created_at else None,
                        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                        "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                        "contributors": contributors,
                        "contributor_count": len(contributors)
                    }
                    repositories.append(repo_data)
                    
                except GithubException as e:
                    print(f"Error processing repository {repo.name}: {e}")
                    continue
                    
        except GithubException as e:
            print(f"Error fetching repositories: {e}")
            return []

        
        return sorted(repositories, key=lambda x: x['updated_at'] or '', reverse=True)

    def get_repository_details(self, repository: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific repository.
        
        Args:
            repository: Repository name (can be just name or owner/name)
        
        Returns:
            Dictionary with detailed repository information
        """
        if not self._is_configured():
            return None
        
        try:
            repo_full_name = self._get_repo_full_name(repository)
            repo = self.github.get_repo(repo_full_name)
            
            # Get contributors
            contributors = []
            try:
                for contributor in repo.get_contributors():
                    contributors.append({
                        "login": contributor.login,
                        "name": contributor.name or contributor.login,
                        "avatar_url": contributor.avatar_url,
                        "contributions": contributor.contributions,
                        "html_url": contributor.html_url,
                        "type": contributor.type
                    })
            except GithubException:
                pass
            
            # Get languages
            languages = {}
            try:
                languages = repo.get_languages()
            except GithubException:
                pass
            
            # Get recent releases
            releases = []
            try:
                for release in repo.get_releases()[:5]:  # Get last 5 releases
                    releases.append({
                        "tag_name": release.tag_name,
                        "name": release.title,
                        "published_at": release.published_at.isoformat() if release.published_at else None,
                        "html_url": release.html_url,
                        "prerelease": release.prerelease,
                        "draft": release.draft
                    })
            except GithubException:
                pass
            
            # Get branches
            branches = []
            try:
                for branch in repo.get_branches():
                    branches.append({
                        "name": branch.name,
                        "protected": branch.protected,
                        "commit_sha": branch.commit.sha
                    })
            except GithubException:
                pass
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "fork": repo.fork,
                "archived": repo.archived,
                "disabled": repo.disabled,
                "language": repo.language,
                "languages": languages,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "size": repo.size,
                "open_issues": repo.open_issues_count,
                "default_branch": repo.default_branch,
                "has_issues": repo.has_issues,
                "has_projects": repo.has_projects,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
                "has_downloads": repo.has_downloads,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "homepage": repo.homepage,
                "topics": repo.get_topics(),
                "license": repo.license.name if repo.license else None,
                "contributors": contributors,
                "contributor_count": len(contributors),
                "releases": releases,
                "branches": branches,
                "branch_count": len(branches)
            }
            
        except GithubException as e:
            print(f"Error fetching repository details for {repository}: {e}")
            return None
    
    def get_recent_activities(
        self,
        usernames: List[str],
        days: int = 7,
        include_commits: bool = True,
        include_prs: bool = True,
        repositories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get recent activities for specified users.
        
        Args:
            usernames: List of GitHub usernames to get activities for
            days: Number of days to look back (default: 7)
            include_commits: Whether to include commit activities (default: True)
            include_prs: Whether to include PR activities (default: True)
            repositories: Optional list of repositories to limit search
        
        Returns:
            Dictionary with user activities and summary statistics
        """
        if not self._is_configured():
            return {}
        
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        activities = {
            "period": {
                "days": days,
                "since": since_date.isoformat(),
                "until": datetime.now(timezone.utc).isoformat()
            },
            "users": {},
            "summary": {
                "total_commits": 0,
                "total_prs": 0,
                "total_repositories": 0,
                "most_active_user": None,
                "most_active_repository": None
            }
        }
        
        repo_activity = {}
        
        for username in usernames:
            user_activities = {
                "username": username,
                "commits": [],
                "pull_requests": [],
                "commit_count": 0,
                "pr_count": 0,
                "repositories_contributed": set()
            }
            
            # Get commits
            if include_commits:
                commits = self.get_commits(
                    author=username,
                    repositories=repositories,
                    since=since_date,
                    limit=200
                )
                user_activities["commits"] = commits
                user_activities["commit_count"] = len(commits)
                
                for commit in commits:
                    user_activities["repositories_contributed"].add(commit["repository"])
                    repo_activity[commit["repository"]] = repo_activity.get(commit["repository"], 0) + 1
            
            # Get pull requests
            if include_prs:
                prs = self.get_pull_requests(
                    author=username,
                    repositories=repositories,
                    since=since_date,
                    limit=100
                )
                user_activities["pull_requests"] = prs
                user_activities["pr_count"] = len(prs)
                
                for pr in prs:
                    user_activities["repositories_contributed"].add(pr["repository"])
                    repo_activity[pr["repository"]] = repo_activity.get(pr["repository"], 0) + 1
            
            # Convert set to list for JSON serialization
            user_activities["repositories_contributed"] = list(user_activities["repositories_contributed"])
            user_activities["repository_count"] = len(user_activities["repositories_contributed"])
            
            activities["users"][username] = user_activities
            
            # Update summary
            activities["summary"]["total_commits"] += user_activities["commit_count"]
            activities["summary"]["total_prs"] += user_activities["pr_count"]
        
        # Calculate summary statistics
        activities["summary"]["total_repositories"] = len(repo_activity)
        
        if activities["users"]:
            # Find most active user
            most_active = max(
                activities["users"].items(),
                key=lambda x: x[1]["commit_count"] + x[1]["pr_count"]
            )
            activities["summary"]["most_active_user"] = {
                "username": most_active[0],
                "total_activities": most_active[1]["commit_count"] + most_active[1]["pr_count"]
            }
        
        if repo_activity:
            # Find most active repository
            most_active_repo = max(repo_activity.items(), key=lambda x: x[1])
            activities["summary"]["most_active_repository"] = {
                "repository": most_active_repo[0],
                "activity_count": most_active_repo[1]
            }
        
        return activities

    def _get_all_repositories(self) -> List[str]:
        """Get list of all accessible repository names"""
        repos = []

        if self.github_repositories: # A user might have a lot of repositories, this I added so that i can show only those I want to show.
            return self.github_repositories

        try:
            if self.organization:
                org = self.github.get_organization(self.organization)
                for repo in org.get_repos():
                    repos.append(repo.name)
            else:
                for repo in self.github.get_user().get_repos():
                    if self.github_repositories and repo.name not in self.github_repositories:
                        continue
                    repos.append(repo.name)
        except GithubException as e:
            print(f"Error fetching repository list: {e}")
            return []
            
        return repos

    
    def test_connection(self) -> bool:
        """Test GitHub connection"""
        if not self._is_configured():
            return False
        
        try:
            user = self.github.get_user()
            return bool(user.login)
        except GithubException:
            return False

    @property
    def context(self) -> str:
        return self.get_repositories_with_contributors()