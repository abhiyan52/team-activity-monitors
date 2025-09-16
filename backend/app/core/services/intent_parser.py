from typing import Dict, List
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from app.clients.jira_client import JiraClient
from datetime import datetime
from app.clients.github_client import GitHubClient


class AgentIntentParser:

    _cached_context = {"jira": None, "github": None}


    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.jira_client = JiraClient()
        self.github_client = GitHubClient()

    def _get_tool_capabilities(self) -> str:
        """
        Get comprehensive information about available tools and their capabilities.
        """
        return """
            ## Cross-Platform Tools

            ### 1. `get_recent_activity`
            **Signature:** `get_recent_activity(team_members: Optional[List[str]] = None, days: int = 7, repositories: Optional[List[str]] = None, projects: Optional[List[str]] = None) -> str`

            **When to use:**
            - Get comprehensive activity from both JIRA and GitHub
            - Monitor team activity across platforms
            - Get unified activity summary

            **Example:**
            ```python
            # Get activity for specific team members
            get_recent_activity(team_members=["john", "jane"])

            # Get activity for last month
            get_recent_activity(days=30)

            # Get activity for specific repositories and projects
            get_recent_activity(repositories=["my-app"], projects=["PROJ"])

            # Get complete team overview
            get_recent_activity()
            ```


            ## JIRA Tools

            ### 1. `search_jira_issues`
            **Signature:** `search_jira_issues(project_key: Optional[str] = None, assignee: Optional[str] = None, status: Optional[str] = None, issue_type: Optional[str] = None, max_results: int = 50) -> str`

            **When to use:**
            - Search for JIRA issues with flexible filtering
            - Find issues by assignee, project, status, or type
            - Get recent issues across all projects

            **Example:**
            ```python
            # Find all issues assigned to John
            search_jira_issues(assignee="john.doe")

            # Find all bugs across all projects
            search_jira_issues(issue_type="Bug")

            # Find in-progress issues in specific project
            search_jira_issues(project_key="PROJ", status="In Progress")

            # Get recent issues (no filters)
            search_jira_issues()
            ```

            ### 2. `get_jira_projects`
            **Signature:** `get_jira_projects() -> str`

            **When to use:**
            - List all available JIRA projects
            - Find project keys for other searches
            - Get project information and leads

            **Example:**
            ```python
            # Get all projects
            get_jira_projects()
            ```

            ### 3. `get_jira_project_users`
            **Signature:** `get_jira_project_users(project_key: str, max_results: int = 50) -> str`

            **When to use:**
            - Find assignable users for a specific project
            - Get team members for a project
            - Find valid assignee names

            **Example:**
            ```python
            # Get users for PROJ project
            get_jira_project_users(project_key="PROJ")

            # Get users with custom limit
            get_jira_project_users(project_key="API-BACKEND", max_results=100)
            ```

            ### 4. `search_jira_users`
            **Signature:** `search_jira_users(query: str, max_results: int = 20) -> str`

            **When to use:**
            - Find users by partial name or email
            - Look up team members across all JIRA
            - Find correct assignee format

            **Example:**
            ```python
            # Search for user by partial name
            search_jira_users(query="john")

            # Search by email
            search_jira_users(query="john@company.com")

            # Search with custom limit
            search_jira_users(query="sarah", max_results=50)
            ```

            ### 5. `get_jira_issue_details`
            **Signature:** `get_jira_issue_details(issue_key: str) -> str`

            **When to use:**
            - Get detailed information about specific issues
            - View issue descriptions and comments
            - Check issue status and transitions

            **Example:**
            ```python
            # Get details for specific issue
            get_jira_issue_details(issue_key="PROJ-123")

            # Get details for API issue
            get_jira_issue_details(issue_key="API-456")
            ```



            ## GitHub Tools

            ### 1. `get_github_commits`
            **Signature:** `get_github_commits(repositories: Optional[List[str]] = None, author: Optional[str] = None, since_days: int = 7, branch: Optional[str] = None, limit: int = 100) -> str`

            **When to use:**
            - Get commits with flexible filtering
            - Track commit activity by author or repository
            - Monitor code changes over time periods

            **Example:**
            ```python
            # Get commits by specific author
            get_github_commits(author="john")

            # Get commits from specific repository
            get_github_commits(repositories=["my-app"])

            # Get commits from last month
            get_github_commits(since_days=30)

            # Get commits from specific branch
            get_github_commits(branch="develop", since_days=7)
            ```

            ### 2. `get_github_repositories`
            **Signature:** `get_github_repositories() -> str`

            **When to use:**
            - List all repositories with contributors
            - Get repository metadata and team information
            - Find repository names for other operations

            **Example:**
            ```python
            # Get all repositories
            get_github_repositories()
            ```

            ### 3. `get_github_repository_details`
            **Signature:** `get_github_repository_details(repository: str) -> str`

            **When to use:**
            - Get comprehensive repository information
            - View contributors, releases, branches
            - Get repository statistics and languages

            **Example:**
            ```python
            # Get details for specific repository
            get_github_repository_details(repository="frontend")

            # Get details for backend project
            get_github_repository_details(repository="my-app")
            ```

            ### 4. `get_github_pull_requests`
            **Signature:** `get_github_pull_requests(repositories: Optional[List[str]] = None, author: Optional[str] = None, since_days: int = 7, state: str = "all", limit: int = 100) -> str`

            **When to use:**
            - Track pull request activity
            - Monitor PR status and authors
            - Get PR information for specific repositories

            **Example:**
            ```python
            # Get recent pull requests
            get_github_pull_requests()

            # Get PRs by specific author
            get_github_pull_requests(author="john")

            # Get open PRs only
            get_github_pull_requests(state="open")

            # Get PRs from specific repositories
            get_github_pull_requests(repositories=["frontend", "backend"])
            ```

            ### 5. `get_github_recent_activities`
            **Signature:** `get_github_recent_activities(usernames: List[str], days: int = 7, include_commits: bool = True, include_prs: bool = True, repositories: Optional[List[str]] = None) -> str`

            **When to use:**
            - Track comprehensive user activity
            - Monitor team activity over time
            - Get detailed activity analytics

            **Example:**
            ```python
            # Get activity for specific users
            get_github_recent_activities(usernames=["john.doe", "jane.smith"])

            # Get activity for last month
            get_github_recent_activities(usernames=["john"], days=30)

            # Get only commits (no PRs)
            get_github_recent_activities(usernames=["john"], include_prs=False)

            # Get activity for specific repositories
            get_github_recent_activities(usernames=["john"], repositories=["my-app"])
            ```
        """

    def _create_system_prompt(self) -> str:
        """
        Create the system prompt for intent parsing.
        """
        # Get context information
        jira_context = str(self.jira_client.context) if self._cached_context["jira"] is None else self._cached_context["jira"]
        github_context = str(self.github_client.context) if self._cached_context["github"] is None else self._cached_context["github"]

        self._cached_context["jira"] = jira_context
        self._cached_context["github"] = github_context

        tool_capabilities = self._get_tool_capabilities()
        
        return f"""You are an expert intent parser in project management domain whose job is to take the user input and convert it into a step by step procedure to complete the query.

            Your have context of integrations and their available tools signature and you job is to generate a JSON in a given structure to complete the user query. 

            For now you will have access to two tools Jira and Github. Jira is a popular project management tool which is used to track the project progress, tasks, assignees and lifecycle. Github is a version control platform that uses git to store code.

            You first need to determine the query is valid or not. We only entertain queries which are related to project management and these tools.

            For a valid query we need to determine the following keys:

            1. assignee: A list of project team member names or team names for which the query is asked.We need to find the correct assignee name for the query. We you have context on the project members for JIRA and Github separately. Based on the query we need to find the correct assignee name for the query. We have contributors information for github and users for jira. We need to take
            displayName from username in JIRA and username from contributors for github. For each assignee we need to find the correct name and add it to the list.

            2. projects: A list of project for which the question is asked. If no specific project is there we need to find the correct project name for the query. We have project information for JIRA and repositories for github. We need to take project key from project information and name from repositories. For each project we need to find the correct name and add it to the list.

            2. time_range: A string representation of the time range for which the question is asked. Like today, last week, this week.

            4. operations: A list of operations that needs to be done step by step to complete the user query. This should have description of the tool call what to do. This should be a plain english description of the tool call. If the multiple steps require input
            from previous steps, you should mention that correctly. This is the cruicial step.

            Here is the context of the projects and repositories which we are having access to:

            # JIRA Projects
            {jira_context}

            # Github Repositories
            {github_context}

            Here is the description of the tools which we are having access to:
            {tool_capabilities}

            ## Examples

            Here are some examples of the user queries and the expected output:

            User Query: What did John work on last week?

            Expected Output:
            {{
            "is_relevant": true,
            "intent": "Find recent activities for John",
            "operations": [
                {{
                    "tool": "get_recent_activity",
                    "action": "Get activity for John across JIRA and GitHub",
                    "filters": {{"team_members": ["john", "john.doe"], "days": 7}},
                    "output_keys": ["jira_activity", "github_activity"]
                }}
            ],
            "members": ["john", "john.doe"],
            "projects": [],
            "repositories": [],
            "time_range": {{"start": null, "end": null, "label": "last week"}},
            "context": {{"user_matching": "john -> john, john.doe", "notes": "Cross-platform activity search"}},
            "error": null
            }}

            Explanation:
            Here we have used cross platform tool which we will be using to get the recent activity for the user john and john.doe.
            Adding both names is important because we have different names for the same user in Jira and Github.

            User Query: What all commits has been done by john this week

            {{
            "is_relevant": true,
            "intent": "Get GitHub commits by John for this week",
            "operations": [
                {{
                    "tool": "get_github_commits",
                    "action": "Retrieve commits by john.doe",
                    "filters": {{"author": "john.doe", "since_days": 7}},
                    "output_keys": ["commits"]
                }}
            ],
            "members": ["john.doe"],
            "projects": [],
            "repositories": [],
            "time_range": {{"start": null, "end": null, "label": "this week"}},
            "context": {{"user_matching": "john -> john.doe", "notes": "GitHub-specific query"}},
            "error": null
            }}

            Explanation:
            Here we have used github commits tool to get the commits for the user john.doe.
            We have not added jira commits because we have not found the user john.doe in jira.

            User Query: Show me recent activity for john

            {{
            "is_relevant": true,
            "intent": "Get recent activity for John",
            "operations": [
                {{
                    "tool": "get_recent_activity",
                    "action": "Get activity for john across platforms",
                    "filters": {{"team_members": ["john.doe", "john"], "days": 7}},
                    "output_keys": ["jira_activity", "github_activity"]
                }}
            ],
            "members": ["john.doe", "john"],
            "projects": [],
            "repositories": [],
            "time_range": {{"start": null, "end": null, "label": "last 7 days"}},
            "context": {{"user_matching": "john -> john.doe, john", "notes": "Cross-platform activity search"}},
            "error": null
            }}

            User Query: Give me a list of tasks assigned to john on JIRA

            {{
            "is_relevant": true,
            "intent": "Get JIRA issues assigned to John",
            "operations": [
                {{
                    "tool": "search_jira_issues",
                    "action": "Search issues assigned to john",
                    "filters": {{"assignee": "john"}},
                    "output_keys": ["issues"]
                }}
            ],
            "members": ["john"],
            "projects": [],
            "repositories": [],
            "time_range": {{"start": null, "end": null, "label": "all time"}},
            "context": {{"user_matching": "john -> john", "notes": "JIRA-specific query"}},
            "error": null
            }}

            User Query: What's the weather like today?

            {{
            "is_relevant": false,
            "intent": null,
            "operations": [],
            "members": [],
            "projects": [],
            "repositories": [],
            "time_range": null,
            "context": null,
            "error": {{"error": "Query not relevant", "reasoning": "Not related to JIRA or GitHub activities"}}
            }}

            Return ONLY a valid JSON object. Do not include any text before or after the JSON."""

    async def parse_intent(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Parse user query and return raw LLM response.
        """
        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create system and human messages
        system_message = SystemMessage(content=self._create_system_prompt())
        
        human_content = f"""Current Time: {current_time}

        Chat History: {str(chat_history)}

        User Query: {query}

        Please analyze this query and return the JSON response."""
        
        human_message = HumanMessage(content=human_content)
        
        # Call LLM directly
        response = await self.llm.ainvoke([system_message, human_message])
        
        # Return raw content
        return response.content if hasattr(response, 'content') else str(response)
