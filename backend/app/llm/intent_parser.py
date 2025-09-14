import inspect
from typing import Any, Dict, List, Union

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from app.clients.github_client import GitHubClient
from app.clients.jira_client import JiraClient
from app.models.schemas import AgentIntent, IrrelevantQueryError, ToolCall


class LLMIntentParser:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.tool_schemas = self._get_tool_schemas()
        self.prompt_template = self._create_prompt_template()

    def _get_tool_schemas(self) -> str:
        """
        Generates a string representation of the available tools and their schemas.
        """
        return """
JIRA Tools:
- search_issues: Search for JIRA issues based on filters
  Parameters: filters (JiraIssueFilter), max_results (int)
- get_recent_activity: Get recent JIRA activity for team members
  Parameters: days (int), team_members (List[str])
- get_projects: Get list of all JIRA projects
  Parameters: None
- get_project_users: Get list of assignable users for a specific project
  Parameters: project_key (str), max_results (int)
- search_users: Search for users by name or email
  Parameters: query (str), max_results (int)
- get_issue_details: Get detailed information about a specific issue
  Parameters: issue_key (str)

GitHub Tools:
- get_repositories: Get list of repositories for the organization or user
  Parameters: None
- get_repository_details: Get detailed information about repositories
  Parameters: None
- get_commits: Get commits from specified repositories
  Parameters: repositories (List[str]), filters (GitHubFilter)
- get_pull_requests: Get pull requests from specified repositories
  Parameters: repositories (List[str]), filters (GitHubFilter)
- get_recent_activity: Get recent GitHub activity
  Parameters: days (int), team_members (List[str]), repositories (List[str])
- get_user_info: Get information about a GitHub user
  Parameters: username (str)
- get_user_organizations: Get organizations for a user
  Parameters: username (str)
- get_repository_contributors: Get contributors for a repository
  Parameters: repository (str)
- get_repository_issues: Get issues for a repository
  Parameters: repository (str), creator (str), state (str)
"""

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        Creates the prompt template for the intent parsing LLM.
        """
        system_prompt = f"""
You are an expert at parsing user queries and determining the correct tool to call.
Your goal is to convert a user's request into a structured response.

Based on the user query and chat history, determine if the query is relevant to
JIRA or GitHub.

If the query is relevant, identify the appropriate tool(s) and action(s) to take from
the list of available tools below.

Available Tools:
{self.tool_schemas}

You must respond with ONLY a valid JSON object. Choose one of these two formats:

For RELEVANT queries (JIRA or GitHub related):
Return a JSON object with a "tool_calls" array containing tool call objects.
Each tool call should have: "tool" (jira or github), "action" (method name), and "parameters" (dict).

For IRRELEVANT queries (not related to JIRA or GitHub):
Return a JSON object with "error" and "reasoning" fields.

IMPORTANT: Respond with ONLY the JSON object, no additional text or explanation.
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
        # Use a simpler approach that works with newer LangChain versions
        chain = self.prompt_template | self.llm
        
        response = await chain.ainvoke({
            "query": query,
            "chat_history": str(chat_history)
        })
        
        # Parse the response manually
        return self._parse_response(response.content)
    
    def _parse_response(self, response_text: str) -> Union[AgentIntent, IrrelevantQueryError]:
        """
        Parse the LLM response text into the appropriate schema.
        """
        import json
        import re
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # Check if it's an IrrelevantQueryError
                if "error" in data and "reasoning" in data:
                    return IrrelevantQueryError(
                        error=data.get("error", "Query is not relevant to JIRA or GitHub activity."),
                        reasoning=data.get("reasoning", "")
                    )
                
                # Check if it's an AgentIntent
                if "tool_calls" in data:
                    tool_calls = []
                    for tool_call_data in data["tool_calls"]:
                        tool_calls.append(ToolCall(
                            tool=tool_call_data.get("tool", ""),
                            action=tool_call_data.get("action", ""),
                            parameters=tool_call_data.get("parameters", {})
                        ))
                    return AgentIntent(tool_calls=tool_calls)
            
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
