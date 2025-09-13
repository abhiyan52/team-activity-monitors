"""
Test cases for JIRA client functionality.

This test suite verifies that the JIRA client works correctly with real JIRA API calls
when proper credentials are configured in the .env file.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.jira_client import JiraClient
from app.models.schemas import JiraIssueFilter

# Load environment variables
load_dotenv()

class TestJiraClient:
    """Test cases for JIRA client"""
    
    @pytest.fixture(scope="class")
    def jira_client(self):
        """Create a JIRA client instance for testing"""
        return JiraClient()
    
    def test_client_initialization(self, jira_client):
        """Test that JIRA client initializes correctly"""
        assert jira_client is not None
        assert hasattr(jira_client, 'server_url')
        assert hasattr(jira_client, 'email')
        assert hasattr(jira_client, 'api_token')
        
    def test_configuration_check(self, jira_client):
        """Test configuration validation"""
        is_configured = jira_client._is_configured()
        
        # Print configuration status for debugging
        print(f"\nJIRA Configuration Status:")
        print(f"  Server URL: {'✓' if jira_client.server_url else '✗'} {jira_client.server_url}")
        print(f"  Email: {'✓' if jira_client.email else '✗'} {jira_client.email}")
        print(f"  API Token: {'✓' if jira_client.api_token else '✗'} {'***' if jira_client.api_token else None}")
        print(f"  JIRA Client: {'✓' if jira_client.jira else '✗'}")
        print(f"  Overall Configured: {'✓' if is_configured else '✗'}")
        
        if not is_configured:
            pytest.skip("JIRA client is not configured. Please set JIRA_SERVER_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env file")
    
    def test_connection(self, jira_client):
        """Test JIRA connection"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        connection_status = jira_client.test_connection()
        print(f"\nJIRA Connection Test: {'✓ PASS' if connection_status else '✗ FAIL'}")
        
        assert connection_status, "Failed to connect to JIRA. Check your credentials and network connection."
    
    def test_get_projects(self, jira_client):
        """Test getting JIRA projects"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        projects = jira_client.get_projects()
        
        print(f"\nJIRA Projects Test:")
        print(f"  Found {len(projects)} projects")
        
        if projects:
            print("  Sample projects:")
            for project in projects[:3]:  # Show first 3 projects
                print(f"    - {project['key']}: {project['name']}")
        
        assert isinstance(projects, list)
        # Projects list can be empty for some JIRA instances, so we don't assert length > 0
    
    def test_search_users(self, jira_client):
        """Test searching for users"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        # Try to search for users with a common query
        users = jira_client.search_users("admin", max_results=5)
        
        print(f"\nJIRA Users Search Test:")
        print(f"  Found {len(users)} users matching 'admin'")
        
        if users:
            print("  Sample users:")
            for user in users[:3]:  # Show first 3 users
                print(f"    - {user['displayName']} ({user['accountId']})")
        
        assert isinstance(users, list)
    
    def test_search_issues_without_filters(self, jira_client):
        """Test searching for issues without specific filters (should use default time range)"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        # Create empty filters (should apply default 30-day range)
        filters = JiraIssueFilter()
        response = jira_client.search_issues(filters, max_results=10)
        
        print(f"\nJIRA Issues Search Test (No Filters):")
        print(f"  Found {len(response.issues)} issues (total: {response.total_count})")
        
        if response.issues:
            print("  Sample issues:")
            for issue in response.issues[:3]:  # Show first 3 issues
                print(f"    - {issue.key}: {issue.summary[:50]}...")
                print(f"      Status: {issue.status}, Assignee: {issue.assignee}")
        
        assert isinstance(response.issues, list)
        assert isinstance(response.total_count, int)
        assert isinstance(response.filtered_count, int)
    
    def test_search_issues_with_date_filter(self, jira_client):
        """Test searching for issues with date filter"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        # Search for issues updated in the last 7 days
        filters = JiraIssueFilter(
            updated_after=datetime.now() - timedelta(days=7)
        )
        response = jira_client.search_issues(filters, max_results=10)
        
        print(f"\nJIRA Issues Search Test (Last 7 Days):")
        print(f"  Found {len(response.issues)} issues updated in last 7 days")
        
        if response.issues:
            print("  Recent issues:")
            for issue in response.issues[:3]:
                print(f"    - {issue.key}: {issue.summary[:50]}...")
                print(f"      Updated: {issue.updated}, Status: {issue.status}")
        
        assert isinstance(response.issues, list)
    
    def test_search_issues_with_project_filter(self, jira_client):
        """Test searching for issues with project filter"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        # First get available projects
        projects = jira_client.get_projects()
        
        if not projects:
            pytest.skip("No projects available to test with")
            
        # Use the first project for testing
        project_key = projects[0]['key']
        
        filters = JiraIssueFilter(
            project_key=project_key,
            updated_after=datetime.now() - timedelta(days=30)
        )
        response = jira_client.search_issues(filters, max_results=5)
        
        print(f"\nJIRA Issues Search Test (Project: {project_key}):")
        print(f"  Found {len(response.issues)} issues in project {project_key}")
        
        if response.issues:
            print("  Project issues:")
            for issue in response.issues[:3]:
                print(f"    - {issue.key}: {issue.summary[:50]}...")
                print(f"      Status: {issue.status}, Type: {issue.issue_type}")
        
        assert isinstance(response.issues, list)
    
    def test_get_recent_activity(self, jira_client):
        """Test getting recent activity"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        response = jira_client.get_recent_activity(days=7)
        
        print(f"\nJIRA Recent Activity Test (Last 7 Days):")
        print(f"  Found {len(response.issues)} issues with recent activity")
        
        if response.issues:
            print("  Recent activity:")
            for issue in response.issues[:3]:
                print(f"    - {issue.key}: {issue.summary[:50]}...")
                print(f"      Updated: {issue.updated}, Assignee: {issue.assignee}")
        
        assert isinstance(response.issues, list)
        assert isinstance(response.total_count, int)
    
    def test_get_project_users(self, jira_client):
        """Test getting users assignable to a project"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        # First get available projects
        projects = jira_client.get_projects()
        
        if not projects:
            pytest.skip("No projects available to test with")
            
        # Use the first project for testing
        project_key = projects[0]['key']
        
        users = jira_client.get_project_users(project_key, max_results=10)
        
        print(f"\nJIRA Project Users Test (Project: {project_key}):")
        print(f"  Found {len(users)} assignable users")
        
        if users:
            print("  Assignable users:")
            for user in users[:3]:
                print(f"    - {user['displayName']} ({user['accountId']})")
                print(f"      Email: {user.get('emailAddress', 'N/A')}")
        
        assert isinstance(users, list)
    
    def test_get_issue_details(self, jira_client):
        """Test getting detailed issue information"""
        if not jira_client._is_configured():
            pytest.skip("JIRA client is not configured")
            
        # First get some issues to test with
        filters = JiraIssueFilter()
        response = jira_client.search_issues(filters, max_results=1)
        
        if not response.issues:
            pytest.skip("No issues available to test with")
            
        # Get details for the first issue
        issue_key = response.issues[0].key
        issue_details = jira_client.get_issue_details(issue_key)
        
        print(f"\nJIRA Issue Details Test (Issue: {issue_key}):")
        
        if issue_details:
            print(f"  Issue: {issue_details['key']}")
            print(f"  Summary: {issue_details['summary']}")
            print(f"  Status: {issue_details['status']}")
            print(f"  Assignee: {issue_details['assignee']}")
            print(f"  Comments: {len(issue_details['comments'])}")
            print(f"  Transitions: {len(issue_details['transitions'])}")
            
            assert issue_details['key'] == issue_key
            assert 'summary' in issue_details
            assert 'status' in issue_details
            assert 'url' in issue_details
            assert 'comments' in issue_details
            assert 'transitions' in issue_details
        else:
            pytest.fail(f"Failed to get details for issue {issue_key}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
