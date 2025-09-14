from typing import Any, Dict, List, Union

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.clients.github_client import GitHubClient
from app.clients.jira_client import JiraClient
from app.models.schemas import AgentIntent, IrrelevantQueryError, IntentParserResponse


class LLMIntentParser:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.tool_schemas = self._get_tool_schemas()
        self.output_parser = PydanticOutputParser(pydantic_object=IntentParserResponse)
        self.prompt_template = self._create_prompt_template()

    def _get_tool_schemas(self) -> str:
        """
        Generates a comprehensive string representation of the available tools and their schemas.
        """
        return """
        JIRA Tools and Capabilities:
        
        1. search_issues: Search for JIRA issues using JQL (JIRA Query Language)
           Parameters: 
           - filters (JiraIssueFilter): Complex filter object with multiple options
           - max_results (int): Maximum number of results (default: 50)
           
           JiraIssueFilter supports:
           - project_key (str): JIRA project key. If project is not mentioned, all projects will be searched.
           - assignee (str): User email or account ID
           - status (str): Issue status (e.g., "In Progress", "Done", "To Do", "In Review")
           - issue_type (str): Issue type (e.g., "Story", "Bug", "Task", "Epic", "Sub-task")
           - created_after (datetime): Filter issues created after this date
           - updated_after (datetime): Filter issues updated after this date
           
           JQL Field Examples:
           - project = "PROJ" AND assignee = "john.doe@company.com"
           - status = "In Progress" AND issuetype = "Story"
           - created >= "2024-01-01" AND updated >= "2024-01-15"
           - priority = "High" AND labels IN ("urgent", "critical")
           
        2. get_recent_activity: Get recent JIRA activity for team members
           Parameters:
           - days (int): Number of days to look back (default: 7)
           - team_members (List[str]): List of team member usernames/emails
           
        3. get_projects: Get list of all JIRA projects
           Parameters: None
           Returns: List of projects with key, name, id, and lead information
           
        4. get_project_users: Get list of assignable users for a specific project
           Parameters:
           - project_key (str): JIRA project key
           - max_results (int): Maximum number of users to return
           
        5. search_users: Search for users by name or email
           Parameters:
           - query (str): Search query for username or email
           - max_results (int): Maximum number of results
           
        6. get_issue_details: Get detailed information about a specific issue
           Parameters:
           - issue_key (str): JIRA issue key (e.g., "PROJ-123")
           Returns: Detailed issue info including comments and transitions

        GitHub Tools and Capabilities:
        
        1. get_repositories: Get list of repositories for the organization or user
           Parameters: None
           Returns: List of repository names
           
        2. get_repository_details: Get detailed information about repositories
           Parameters: None
           Returns: List of repository objects with name, full_name, private, description, 
                   language, stars, forks, updated_at, html_url
           
        3. get_commits: Get commits from specified repositories
           Parameters:
           - repositories (List[str]): List of repository names
           - filters (GitHubFilter): Filter object with options
           
           GitHubFilter supports:
           - author (str): Commit author username
           - since (datetime): Commits since this date
           - branch (str): Branch name (default: default branch)
           
        4. get_pull_requests: Get pull requests from specified repositories
           Parameters:
           - repositories (List[str]): List of repository names
           - filters (GitHubFilter): Filter object with options
           
           GitHubFilter for PRs supports:
           - author (str): PR author username
           - since (datetime): PRs updated since this date
           
        5. get_recent_activity: Get recent GitHub activity
           Parameters:
           - days (int): Number of days to look back
           - team_members (List[str]): List of team member usernames
           - repositories (List[str]): List of repository names
           
        6. get_user_info: Get information about a GitHub user
           Parameters:
           - username (str, optional): GitHub username (defaults to authenticated user)
           Returns: User info including login, name, email, avatar_url, bio, company, 
                   location, public_repos, followers, following, created_at, html_url
           
        7. get_user_organizations: Get organizations for a user
           Parameters:
           - username (str, optional): GitHub username (defaults to authenticated user)
           
        8. get_repository_contributors: Get contributors for a repository
           Parameters:
           - repository (str): Repository name
           
        9. get_repository_issues: Get issues for a repository
           Parameters:
           - repository (str): Repository name
           - creator (str, optional): Issue creator username
           - state (str): Issue state ("open", "closed", "all")

        Advanced Filtering and Query Capabilities:
        
        JIRA JQL (JIRA Query Language) Examples:
        - Simple queries: project = "PROJ" AND status = "In Progress"
        - Date ranges: created >= "2024-01-01" AND created <= "2024-01-31"
        - User queries: assignee = "john.doe@company.com" OR assignee = "jane.smith@company.com"
        - Status transitions: status CHANGED FROM "To Do" TO "In Progress" AFTER "2024-01-01"
        - Text searches: summary ~ "bug fix" OR description ~ "performance"
        - Priority and labels: priority = "High" AND labels IN ("urgent", "critical")
        - Complex combinations: project = "PROJ" AND (status = "In Progress" OR status = "In Review") 
          AND assignee IN ("john.doe@company.com", "jane.smith@company.com")
        
        GitHub Filtering Examples:
        - Repository filtering: Get commits from specific repositories
        - Author filtering: Get commits/PRs by specific authors
        - Date filtering: Get activity since specific dates
        - Branch filtering: Get commits from specific branches
        - State filtering: Get open/closed issues and PRs
        
        Common Use Cases:
        - "Show me all issues assigned to John in the PROJ project"
        - "Get recent commits from the frontend team in the last 7 days"
        - "Find all high priority bugs created this month"
        - "Show me pull requests that were merged last week"
        - "Get all issues in 'In Progress' status for the API project"
        - "Find commits by Sarah in the backend repository since last Monday"
        """

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        Creates the prompt template for the intent parsing LLM.
        """
        # Get format instructions and handle potential template variables
        format_instructions = self.output_parser.get_format_instructions()
        # Escape any curly braces in the format instructions that aren't meant to be template variables
        format_instructions = format_instructions.replace("{", "{{").replace("}", "}}")
        
        system_prompt = f"""
        You are an agentic technical program manager who can understand what a user (developer)
        is working on currently or in the past. You understand what user stories are and how work
        on a user story is quantified. User stories are where the requirements for a feature is
        specified. Typically user stories are defined in JIRA and work associated is found in
        Pull Requests in GitHub.

        Given a user input you first need to check if it is a relevant question or not. Any question
        that is outside scope of development process that does not utilize JIRA and GitHub or is not linked
        to development process and tracking should not be entertained.

        If the query is relevant, identify the intent of the query and structure it according to the
        AgentIntent schema for downstream processing.

        We have exposed a list of sources and tools that can be combined to answer the relevant question. Here is the tool / source
        list of what all are in disposal for your use:

        Available Tools:
        {self.tool_schemas}

        {format_instructions}

        IMPORTANT: You must respond with a structured response that follows the IntentParserResponse schema.
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Chat History:\n{chat_history}\n\nUser Query: {query}")
        ])

    async def parse_intent(
        self, query: str, chat_history: List[Dict[str, str]]
    ) -> Union[AgentIntent, IrrelevantQueryError]:
        """
        Parses the user's query to determine the intent and required tool calls.
        """
        # Create chain with structured output parser
        chain = self.prompt_template | self.llm | self.output_parser
        
        try:
            response = await chain.ainvoke({
                "query": query,
                "chat_history": str(chat_history)
            })
            
            # Return the appropriate response based on relevance
            if response.is_relevant and response.agent_intent:
                return response.agent_intent
            elif response.error:
                return response.error
            else:
                return IrrelevantQueryError(
                    error="Query is not relevant to JIRA or GitHub activity.",
                    reasoning="No valid intent or error found in response."
                )
                
        except Exception as e:
            # Fallback to manual JSON parsing if structured output fails
            try:
                # Try to get the raw response and parse manually
                chain_without_parser = self.prompt_template | self.llm
                raw_response = await chain_without_parser.ainvoke({
                    "query": query,
                    "chat_history": str(chat_history)
                })
                return self._parse_json_response(raw_response.content)
            except Exception:
                return IrrelevantQueryError(
                    error="Query is not relevant to JIRA or GitHub activity.",
                    reasoning=f"Failed to parse intent: {str(e)}"
                )
    
    def _parse_json_response(self, response_text: str) -> Union[AgentIntent, IrrelevantQueryError]:
        """
        Parse the LLM JSON response into the appropriate schema.
        """
        import json
        import re
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # Check if it's an irrelevant query
                if not data.get("is_relevant", True):
                    error_data = data.get("error", {})
                    return IrrelevantQueryError(
                        error=error_data.get("error", "Query is not relevant to JIRA or GitHub activity."),
                        reasoning=error_data.get("reasoning", "No reasoning provided.")
                    )
                
                # Check if it's a relevant query with agent intent
                if data.get("is_relevant", False) and "agent_intent" in data:
                    intent_data = data["agent_intent"]
                    return AgentIntent(**intent_data)
            
            # If we can't parse as JSON, try to determine intent from text
            if any(keyword in response_text.lower() for keyword in ["not relevant", "irrelevant", "not related", "unrelated"]):
                return IrrelevantQueryError(
                    error="Query is not relevant to JIRA or GitHub activity.",
                    reasoning="LLM determined the query is not related to JIRA or GitHub tools."
                )
            
            # Default to irrelevant if we can't parse
            return IrrelevantQueryError(
                error="Query is not relevant to JIRA or GitHub activity.",
                reasoning="Unable to parse LLM response as a valid intent."
            )
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # If parsing fails, return an error
            return IrrelevantQueryError(
                error="Query is not relevant to JIRA or GitHub activity.",
                reasoning=f"Failed to parse LLM response: {str(e)}"
            )
