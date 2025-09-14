from typing import Dict, List, Union
import json

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.models.schemas import AgentIntent, IrrelevantQueryError, IntentParserResponse
from app.core.tools import get_current_time
from app.clients.jira_client import JiraClient
from app.clients.github_client import GitHubClient


class AgentIntentParser:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.jira_client = JiraClient()
        self.github_client = GitHubClient()
        self.output_parser = PydanticOutputParser(pydantic_object=IntentParserResponse)
        
        # Initialize the agent with datetime tool
        self.tools = [get_current_time]
        self.agent_prompt = self._create_agent_prompt()
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.agent_prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def _get_context_information(self) -> str:
        """
        Get comprehensive information about the context of the JIRA and GitHub projects.
        """
        return f"""
        JIRA Context:
        {self.jira_client.context}
        """ + f"""
        GitHub Context:
        {self.github_client.context}
        """


    def _get_tool_capabilities(self) -> str:
        """
        Get comprehensive information about available tools and their capabilities.
        """
        return """
        AVAILABLE TOOLS FOR EXECUTION PLANNING:

        JIRA Tools:
        1. search_jira_issues - Search JIRA issues with flexible filtering
           Parameters: project_key, assignee, status, issue_type, max_results
           Use for: Finding issues, tracking work, getting project status

        2. get_jira_projects - Get list of all JIRA projects
           Parameters: None
           Use for: Understanding available projects, project discovery

        3. get_jira_project_users - Get assignable users for a project
           Parameters: project_key, max_results
           Use for: Finding team members, user validation

        4. search_jira_users - Search users by name or email
           Parameters: query, max_results
           Use for: User discovery, name-to-username mapping

        5. get_jira_issue_details - Get detailed issue information
           Parameters: issue_key
           Use for: Deep dive into specific issues

        6. test_jira_connection - Test JIRA connectivity
           Parameters: None
           Use for: Troubleshooting, health checks

        GitHub Tools:
        1. get_github_commits - Get commits with filtering
           Parameters: repositories, author, since_days, branch, limit
           Use for: Code activity tracking, author contributions

        2. get_github_pull_requests - Get pull requests with filtering
           Parameters: repositories, author, since_days, state, limit
           Use for: PR tracking, review activity, merge activity

        3. get_github_repositories - Get all repositories with contributors
           Parameters: None
           Use for: Repository discovery, contributor information

        4. get_github_repository_details - Get detailed repository info
           Parameters: repository
           Use for: Single repository deep dive, metadata

        5. get_github_recent_activities - Get comprehensive user activities
           Parameters: usernames, days, include_commits, include_prs, repositories
           Use for: Team activity analysis, productivity tracking


        Combined Tools:
        1. get_recent_activity - Get combined JIRA and GitHub activity
           Parameters: team_members, days, repositories, projects
           Use for: Comprehensive team activity overview

        Utility Tools:
        1. get_current_time - Get current date/time in various formats
           Parameters: format_type ("time", "date", "datetime", "timestamp", "iso")
           Use for: Date calculations, time-based filtering, current context

        OPERATION PLANNING GUIDELINES:

        1. Date/Time Operations:
           - Always use get_current_time first when dealing with relative dates
           - Convert relative terms ("last week", "yesterday", "this month") to specific dates
           - Use appropriate date formats for different tools

        2. User Matching:
           - Match user names across JIRA and GitHub (e.g., "joe.doe" ↔ "joe doe")
           - Consider partial matches and common variations
           - Use search tools to validate user existence

        3. Repository/Project Context:
           - Map project names to repository names when possible
           - Consider organizational structure and naming conventions
           - Use discovery tools when specific names aren't clear

        4. Multi-step Operations:
           - Break complex queries into logical steps
           - Plan data gathering before analysis
           - Consider dependencies between operations

        5. Error Handling:
           - Plan for connection testing when issues arise
           - Include fallback operations for missing data
           - Validate user/project existence before detailed queries
        """

    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """
        Create the agent prompt template for intent parsing and operation planning.
        """
        system_prompt = f"""
        You are an intelligent Technical Program Manager Agent specializing in development workflow analysis.
        Your role is to understand user queries about JIRA and GitHub activities, then create comprehensive 
        execution plans for the downstream basic agent.

        CORE RESPONSIBILITIES:
        1. Determine if the user query is relevant to development/project management
        2. Based on the query try to find the matching user, project and repository information from the context information.
        3. Create detailed operation plan for the relevant query using tools and context information.
    

        CONTEXT INFORMATION:
        The agent has access to context information about JIRA projects and GitHub repositories.
        Use the available tools to discover and match users, projects, and repositories dynamically.

        AVAILABLE TOOLS AND CAPABILITIES:
        {self._get_tool_capabilities()}

        OPERATION PLANNING PROCESS:
        1. First, assess query relevance to JIRA/GitHub development activities
        2. If relevant, use get_current_time tool when dealing with relative dates
        3. Plan a sequence of operations to fully answer the user's question
        4. Consider user name variations and matching across platforms
        5. Structure the response according to IntentParserResponse schema

        OPERATION PLANNING EXAMPLES WITH CROSS-PLATFORM MATCHING:

        Example 1: "What did John work on last week?"
        Strategy:
        1. Use get_current_time to calculate "last week" date range
        2. Use search_jira_users with MULTIPLE searches: "john", "john doe", "j.doe" to find variations
        3. Use search_jira_issues with assignee filter for John's JIRA work
        4. Use get_github_recent_activities with usernames like ["john-doe", "johnsmith", "j-doe"] for GitHub activity
        5. Cross-reference by timeframe and project context
        
        IMPORTANT: For better matching, use PARTIAL NAME SEARCHES:
        - Instead of "abhiyan timilsina", try "abhiyan" AND "timilsina" separately
        - Search both first name and last name individually
        - This increases chances of finding the user even with different name formats

        Example 2: "Show me activity in the authentication service"
        Strategy:
        1. Use get_jira_projects to identify auth-related projects (AUTH, USER-SERVICE)
        2. Use get_github_repositories to find auth-related repos (user-auth-service, authentication-api)
        3. Use search_jira_issues with project_key filter for JIRA activity
        4. Use get_github_commits and get_github_pull_requests for GitHub activity
        5. Map projects to repositories in context

        Example 3: "What has Sarah worked on in frontend?"
        Strategy:
        1. Use search_jira_users to find Sarah's JIRA identity (sarah.smith@company.com)
        2. Identify frontend projects (FRONTEND, UI-COMPONENTS) and repos (frontend-app, ui-components)
        3. Use search_jira_issues with assignee and project filters
        4. Use get_github_recent_activities with usernames ["sarah-smith", "sarahj"] and repository filters
        5. Include user matching confidence in context

        COMPREHENSIVE MATCHING PATTERNS:
        
        CRITICAL USER NAME EXTRACTION AND MATCHING RULES:

        1. EXTRACT USERS FROM QUERY: Always identify and list users mentioned in the query
           - "abhiyan timilsina" → members: ["abhiyan timilsina", "abhiyan.timilsina", "abhiyantimilsina"]
           - "john doe" → members: ["john doe", "john.doe", "johndoe", "j.doe"]
           - "sarah" → members: ["sarah", "sarah.smith", "sarahsmith", "s.smith"]

        2. JIRA USERNAME PATTERNS:
           - Full name: "abhiyan timilsina" → "abhiyan.timilsina@company.com"
           - Email format: "firstname.lastname@domain.com"
           - Display name: "Abhiyan Timilsina" (exact case)
           - Username: "abhiyan.timilsina", "atimilsina"

        3. GITHUB USERNAME PATTERNS:
           - Hyphenated: "abhiyan-timilsina"
           - Concatenated: "abhiyantimilsina"  
           - Abbreviated: "atimilsina", "abhiyan52"
           - Underscored: "abhiyan_timilsina"

        4. MATCHING STRATEGY:
           - ALWAYS populate members field with all possible username variations
           - Use search_jira_users with partial names: "abhiyan", "timilsina"
           - Include common variations in GitHub usernames list
           - Cross-reference found users between platforms

        REPOSITORY/PROJECT MATCHING PATTERNS:
        - "frontend" → JIRA: "FRONTEND", "UI-COMPONENTS" → GitHub: "frontend-app", "ui-components"
        - "backend" → JIRA: "BACKEND-API", "SERVICES" → GitHub: "backend-api", "microservices"  
        - "authentication" → JIRA: "AUTH", "USER-SERVICE" → GitHub: "user-auth-service", "auth-api"
        - "database" → JIRA: "DATABASE", "DATA" → GitHub: "database-service", "data-layer"
        - "mobile" → JIRA: "MOBILE-APP", "IOS", "ANDROID" → GitHub: "mobile-app", "ios-client", "android-app"

        IMPORTANT: You have access to the get_current_time tool. Use it whenever you need to:
        - Convert relative dates ("last week", "yesterday", "this month")
        - Calculate date ranges for filtering
        - Understand current context for time-based queries

        Respond with a structured IntentParserResponse that includes:
        - is_relevant: boolean indicating if query is development-related
        - agent_intent: detailed operation plan if relevant
        - error: error information if query is irrelevant or problematic
        """

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
            Chat History: {chat_history}
            
            User Query: {input}
            
            Please analyze this query and create a comprehensive execution plan. Use the get_current_time tool 
            if you need current date/time context for relative date references.
            
            IMPORTANT: Respond with a valid JSON object following the IntentParserResponse schema.
            
            For relevant queries, use this EXACT structure:
            {{
                "is_relevant": true,
                "agent_intent": {{
                    "intent": "Clear description of what user wants",
                    "operations": [
                        {{
                            "tool": "tool_name",
                            "action": "Specific action description",
                            "filters": {{"param1": "value1", "param2": "value2"}},
                            "output_keys": ["key1", "key2"]
                        }}
                    ],
                    "members": ["list_all_identified_users_from_query"],
                    "projects": ["jira_project_keys"],
                    "repositories": ["github_repo_names"],
                    "time_range": {{"start": null, "end": null, "label": "description"}},
                    "context": {{
                        "user_matching": "strategy used",
                        "project_mapping": "how projects were mapped",
                        "notes": "additional context"
                    }}
                }},
                "error": null
            }}
            
            For irrelevant queries:
            {{
                "is_relevant": false,
                "agent_intent": null,
                "error": {{"error": "reason", "reasoning": "detailed explanation"}}
            }}
            """),
            ("placeholder", "{agent_scratchpad}")
        ])

    async def parse_intent(
        self, query: str, chat_history: List[Dict[str, str]]
    ) -> Union[AgentIntent, IrrelevantQueryError]:
        """
        Parse user query using the agent to create comprehensive execution plans.
        """
        try:
            # Use the agent to process the query with access to datetime tool
            response = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": str(chat_history)
            })
            
            # Extract the agent's output
            agent_output = response.get("output", "")
            
            # Try to parse the agent's response as JSON
            try:
                # Look for JSON in the agent's response
                if "{" in agent_output and "}" in agent_output:
                    start_idx = agent_output.find("{")
                    end_idx = agent_output.rfind("}") + 1
                    json_str = agent_output[start_idx:end_idx]
                    
                    parsed_response = json.loads(json_str)
                    
                    # Convert to IntentParserResponse
                    intent_response = IntentParserResponse(**parsed_response)
                    
                    # Return appropriate response
                    if intent_response.is_relevant and intent_response.agent_intent:
                        return intent_response.agent_intent
                    elif intent_response.error:
                        return intent_response.error
                    else:
                        return IrrelevantQueryError(
                            error="Query is not relevant to JIRA or GitHub activity.",
                            reasoning="Agent determined query is not development-related."
                        )
                        
            except (json.JSONDecodeError, Exception) as parse_error:
                print(f"Failed to parse agent response: {parse_error}")
                print(f"Agent output: {agent_output}")
                
                # Fallback: analyze if query seems relevant
                query_lower = query.lower()
                relevant_keywords = [
                    'jira', 'github', 'issue', 'ticket', 'commit', 'pull request', 'pr',
                    'bug', 'story', 'task', 'repository', 'repo', 'project', 'assigned',
                    'worked on', 'activity', 'progress', 'merge', 'branch', 'code',
                    'development', 'dev', 'feature', 'fix', 'implementation'
                ]
                
                is_relevant = any(keyword in query_lower for keyword in relevant_keywords)
                
                if not is_relevant:
                    return IrrelevantQueryError(
                        error="Query is not relevant to JIRA or GitHub activity.",
                        reasoning="Query does not contain development-related keywords."
                    )
                else:
                    # Create a basic intent if we can't parse the agent response
                    return AgentIntent(
                        intent=f"Process query: {query}",
                        operations=[],
                        context=f"Agent response parsing failed. Raw output: {agent_output[:200]}..."
                    )
                    
        except Exception as e:
            print(f"Error in agent execution: {e}")
            return IrrelevantQueryError(
                error="Failed to process query.",
                reasoning=f"Agent execution error: {str(e)}"
            )
