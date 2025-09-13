"""
Test cases for GitHub client functionality.

This test suite verifies that the GitHub client works correctly with real GitHub API calls
when proper credentials are configured in the .env file.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.github_client import GitHubClient
from app.models.schemas import GitHubFilter

# Load environment variables
load_dotenv()

class TestGitHubClient:
    """Test cases for GitHub client"""
    
    @pytest.fixture(scope="class")
    def github_client(self):
        """Create a GitHub client instance for testing"""
        return GitHubClient()
    
    def test_client_initialization(self, github_client):
        """Test that GitHub client initializes correctly"""
        assert github_client is not None
        assert hasattr(github_client, 'token')
        assert hasattr(github_client, 'organization')
        assert hasattr(github_client, 'github')
        
    def test_configuration_check(self, github_client):
        """Test configuration validation"""
        is_configured = github_client._is_configured()
        
        # Print configuration status for debugging
        print(f"\nGitHub Configuration Status:")
        print(f"  Token: {'✓' if github_client.token else '✗'} {'***' if github_client.token else None}")
        print(f"  Organization: {'✓' if github_client.organization else '✗'} {github_client.organization}")
        print(f"  GitHub Client: {'✓' if github_client.github else '✗'}")
        print(f"  Overall Configured: {'✓' if is_configured else '✗'}")
        
        if not is_configured:
            pytest.skip("GitHub client is not configured. Please set GITHUB_TOKEN in .env file")
    
    def test_connection(self, github_client):
        """Test GitHub connection"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        connection_status = github_client.test_connection()
        print(f"\nGitHub Connection Test: {'✓ PASS' if connection_status else '✗ FAIL'}")
        
        assert connection_status, "Failed to connect to GitHub. Check your token and network connection."
    
    def test_get_authenticated_user(self, github_client):
        """Test getting authenticated user information"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        username = github_client._get_authenticated_user()
        print(f"\nGitHub Authenticated User: {username}")
        
        assert username != "unknown"
        assert isinstance(username, str)
        assert len(username) > 0
    
    def test_get_user_info_authenticated(self, github_client):
        """Test getting detailed user information for authenticated user"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        user_info = github_client.get_user_info()
        
        print(f"\nGitHub User Info Test (Authenticated User):")
        if user_info:
            print(f"  Login: {user_info['login']}")
            print(f"  Name: {user_info['name']}")
            print(f"  Email: {user_info['email']}")
            print(f"  Public Repos: {user_info['public_repos']}")
            print(f"  Followers: {user_info['followers']}")
            print(f"  Following: {user_info['following']}")
            
            assert 'login' in user_info
            assert 'name' in user_info
            assert 'public_repos' in user_info
            assert 'html_url' in user_info
        else:
            pytest.fail("Failed to get authenticated user info")
    
    def test_get_user_info_specific_user(self, github_client):
        """Test getting user information for a specific user"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        # Test with a well-known GitHub user
        test_username = "octocat"
        user_info = github_client.get_user_info(test_username)
        
        print(f"\nGitHub User Info Test (User: {test_username}):")
        if user_info:
            print(f"  Login: {user_info['login']}")
            print(f"  Name: {user_info['name']}")
            print(f"  Public Repos: {user_info['public_repos']}")
            print(f"  Followers: {user_info['followers']}")
            
            assert user_info['login'] == test_username
            assert 'name' in user_info
            assert 'public_repos' in user_info
        else:
            pytest.fail(f"Failed to get user info for {test_username}")
    
    def test_get_repositories(self, github_client):
        """Test getting repository list"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        repositories = github_client.get_repositories()
        
        print(f"\nGitHub Repositories Test:")
        print(f"  Found {len(repositories)} repositories")
        
        if repositories:
            print("  Sample repositories:")
            for repo in repositories[:5]:  # Show first 5 repositories
                print(f"    - {repo}")
        
        assert isinstance(repositories, list)
        # Repository list should not be empty for most users
        if len(repositories) == 0:
            print("  Warning: No repositories found. This might be expected for new accounts.")
    
    def test_get_repository_details(self, github_client):
        """Test getting detailed repository information"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        repo_details = github_client.get_repository_details()
        
        print(f"\nGitHub Repository Details Test:")
        print(f"  Found {len(repo_details)} repositories with details")
        
        if repo_details:
            print("  Sample repository details:")
            for repo in repo_details[:3]:  # Show first 3 repositories
                print(f"    - {repo['name']} ({repo['full_name']})")
                print(f"      Language: {repo['language']}, Stars: {repo['stars']}, Forks: {repo['forks']}")
                print(f"      Private: {repo['private']}, Description: {repo['description'][:50] if repo['description'] else 'None'}...")
                
                # Validate required fields
                assert 'name' in repo
                assert 'full_name' in repo
                assert 'private' in repo
                assert 'html_url' in repo
        
        assert isinstance(repo_details, list)
    
    def test_get_user_organizations(self, github_client):
        """Test getting user organizations"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        organizations = github_client.get_user_organizations()
        
        print(f"\nGitHub Organizations Test:")
        print(f"  Found {len(organizations)} organizations")
        
        if organizations:
            print("  User organizations:")
            for org in organizations[:3]:  # Show first 3 organizations
                print(f"    - {org['login']}: {org['name']}")
                print(f"      Description: {org['description'][:50] if org['description'] else 'None'}...")
        else:
            print("  User is not a member of any organizations")
        
        assert isinstance(organizations, list)
    
    def test_get_commits(self, github_client):
        """Test getting commits from repositories"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        repositories = github_client.get_repositories()
        
        if not repositories:
            pytest.skip("No repositories available to test commits")
            
        # Test with the first few repositories
        test_repos = repositories[:2]  # Limit to 2 repos to avoid API rate limits
        
        filters = GitHubFilter(
            since=datetime.now() - timedelta(days=30)
        )
        
        commits = github_client.get_commits(test_repos, filters)
        
        print(f"\nGitHub Commits Test (Last 30 Days):")
        print(f"  Found {len(commits)} commits from {len(test_repos)} repositories")
        
        if commits:
            print("  Sample commits:")
            for commit in commits[:3]:  # Show first 3 commits
                print(f"    - {commit.sha[:8]}: {commit.message[:50]}...")
                print(f"      Author: {commit.author}, Date: {commit.date}")
                print(f"      Repository: {commit.repository}")
                
                # Validate commit structure
                assert hasattr(commit, 'sha')
                assert hasattr(commit, 'message')
                assert hasattr(commit, 'author')
                assert hasattr(commit, 'date')
                assert hasattr(commit, 'repository')
        
        assert isinstance(commits, list)
    
    def test_get_pull_requests(self, github_client):
        """Test getting pull requests from repositories"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        repositories = github_client.get_repositories()
        
        if not repositories:
            pytest.skip("No repositories available to test pull requests")
            
        # Test with the first few repositories
        test_repos = repositories[:2]  # Limit to 2 repos to avoid API rate limits
        
        filters = GitHubFilter(
            since=datetime.now() - timedelta(days=90)  # Longer period for PRs
        )
        
        pull_requests = github_client.get_pull_requests(test_repos, filters)
        
        print(f"\nGitHub Pull Requests Test (Last 90 Days):")
        print(f"  Found {len(pull_requests)} pull requests from {len(test_repos)} repositories")
        
        if pull_requests:
            print("  Sample pull requests:")
            for pr in pull_requests[:3]:  # Show first 3 PRs
                print(f"    - #{pr.number}: {pr.title[:50]}...")
                print(f"      Author: {pr.author}, State: {pr.state}")
                print(f"      Repository: {pr.repository}, Merged: {pr.merged}")
                
                # Validate PR structure
                assert hasattr(pr, 'number')
                assert hasattr(pr, 'title')
                assert hasattr(pr, 'state')
                assert hasattr(pr, 'author')
                assert hasattr(pr, 'repository')
        
        assert isinstance(pull_requests, list)
    
    def test_get_recent_activity(self, github_client):
        """Test getting recent GitHub activity"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        response = github_client.get_recent_activity(days=7)
        
        print(f"\nGitHub Recent Activity Test (Last 7 Days):")
        print(f"  Commits: {len(response.commits)}")
        print(f"  Pull Requests: {len(response.pull_requests)}")
        print(f"  Repositories: {len(response.repositories)}")
        
        if response.commits:
            print("  Recent commits:")
            for commit in response.commits[:2]:
                print(f"    - {commit.message[:50]}... by {commit.author}")
        
        if response.pull_requests:
            print("  Recent pull requests:")
            for pr in response.pull_requests[:2]:
                print(f"    - #{pr.number}: {pr.title[:50]}... by {pr.author}")
        
        # Validate response structure
        assert hasattr(response, 'commits')
        assert hasattr(response, 'pull_requests')
        assert hasattr(response, 'repositories')
        assert isinstance(response.commits, list)
        assert isinstance(response.pull_requests, list)
        assert isinstance(response.repositories, list)
    
    def test_get_repository_contributors(self, github_client):
        """Test getting repository contributors"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        repositories = github_client.get_repositories()
        
        if not repositories:
            pytest.skip("No repositories available to test contributors")
            
        # Test with the first repository
        test_repo = repositories[0]
        
        contributors = github_client.get_repository_contributors(test_repo)
        
        print(f"\nGitHub Repository Contributors Test (Repo: {test_repo}):")
        print(f"  Found {len(contributors)} contributors")
        
        if contributors:
            print("  Top contributors:")
            for contributor in contributors[:3]:  # Show top 3 contributors
                print(f"    - {contributor['login']}: {contributor['contributions']} contributions")
                print(f"      Name: {contributor['name']}")
                
                # Validate contributor structure
                assert 'login' in contributor
                assert 'contributions' in contributor
                assert 'html_url' in contributor
        
        assert isinstance(contributors, list)
    
    def test_get_repository_issues(self, github_client):
        """Test getting repository issues"""
        if not github_client._is_configured():
            pytest.skip("GitHub client is not configured")
            
        repositories = github_client.get_repositories()
        
        if not repositories:
            pytest.skip("No repositories available to test issues")
            
        # Test with the first repository
        test_repo = repositories[0]
        
        issues = github_client.get_repository_issues(test_repo, state="all")
        
        print(f"\nGitHub Repository Issues Test (Repo: {test_repo}):")
        print(f"  Found {len(issues)} issues")
        
        if issues:
            print("  Sample issues:")
            for issue in issues[:3]:  # Show first 3 issues
                print(f"    - #{issue['number']}: {issue['title'][:50]}...")
                print(f"      Author: {issue['author']}, State: {issue['state']}")
                print(f"      Labels: {', '.join(issue['labels'])}")
                
                # Validate issue structure
                assert 'number' in issue
                assert 'title' in issue
                assert 'state' in issue
                assert 'author' in issue
                assert 'html_url' in issue
        
        assert isinstance(issues, list)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
