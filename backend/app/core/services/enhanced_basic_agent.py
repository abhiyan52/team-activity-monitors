"""
Enhanced BasicAgent that can receive and use intent information from AgentIntentParser.
"""
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from app.core.config import settings
from app.core.tools import tools
from app.models.schemas import AgentIntent


class EnhancedBasicAgent:
    """
    Enhanced version of BasicAgent that can receive intent information
    from AgentIntentParser and use it for better execution.
    """
    
    _llm: ChatGoogleGenerativeAI | ChatOpenAI | None = None

    def __init__(self, memory_key: str = "chat_history", llm_model: str = "google/gemini-1.5-flash"):
        self.memory_key = memory_key
        self.llm_model = llm_model
        self._llm = None

    def _create_system_prompt(self, intent: Optional[AgentIntent] = None) -> str:
        """
        Create system prompt with optional intent information.
        
        Args:
            intent: Parsed intent from AgentIntentParser
            
        Returns:
            Enhanced system prompt string
        """
        
        base_prompt = """
You are Team Activity Monitor, a helpful assistant that summarizes team member activities by combining JIRA and GitHub data.

— You receive user questions about what teammates are working on or have done (issues, tickets, PRs, commits, etc).
— For each query, you should:
1. Use the available tools (search_jira_issues, get_github_commits, etc). Only use what is described in the tool descriptions.
2. Combine and synthesize the tool results into a clear and user-friendly answer.
3. If a query cannot be answered by the available tools, politely clarify or explain the limitation.
"""

        # Add intent-specific information if provided
        if intent:
            base_prompt += "\n\n🧠 ENHANCED CONTEXT FROM INTENT ANALYSIS:\n"
            
            if intent.intent:
                base_prompt += f"🎯 User's Intent: {intent.intent}\n"
            
            if intent.members:
                base_prompt += f"👥 Target Members: {', '.join(intent.members)}\n"
                base_prompt += "   → Use these exact name variations when searching\n"
            
            if intent.projects:
                base_prompt += f"📁 Target Projects: {', '.join(intent.projects)}\n"
                base_prompt += "   → Focus searches on these JIRA project keys\n"
            
            if intent.repositories:
                base_prompt += f"📂 Target Repositories: {', '.join(intent.repositories)}\n"
                base_prompt += "   → Focus searches on these GitHub repositories\n"
            
            if intent.time_range:
                base_prompt += f"⏰ Time Context: {intent.time_range.label}\n"
                if intent.time_range.start:
                    base_prompt += f"   → Start: {intent.time_range.start}\n"
                if intent.time_range.end:
                    base_prompt += f"   → End: {intent.time_range.end}\n"
            
            if intent.operations:
                base_prompt += f"\n🔧 RECOMMENDED OPERATION SEQUENCE ({len(intent.operations)} steps):\n"
                for i, op in enumerate(intent.operations, 1):
                    base_prompt += f"   {i}. {op.tool} - {op.action}\n"
                    if op.filters:
                        important_filters = {k: v for k, v in op.filters.items() 
                                           if k in ['query', 'assignee', 'project_key', 'usernames', 'repositories', 'status', 'days']}
                        if important_filters:
                            base_prompt += f"      Suggested filters: {important_filters}\n"
            
            if intent.context:
                base_prompt += f"\n📝 MATCHING STRATEGIES:\n"
                for key, value in intent.context.items():
                    if isinstance(value, str) and len(value) < 150:
                        base_prompt += f"   • {key}: {value}\n"
            
            base_prompt += "\n🎯 EXECUTION GUIDELINES WITH INTENT:\n"
            base_prompt += "- Use the provided member name variations for accurate user matching\n"
            base_prompt += "- Follow the recommended operation sequence when applicable\n"
            base_prompt += "- Apply suggested filters for more precise results\n"
            base_prompt += "- Cross-reference data between JIRA and GitHub using member variations\n"

        base_prompt += """

Available tools:
- search_jira_issues: Look up JIRA issues (filters: project_key, assignee, status, etc)
- get_github_commits: Fetch commit history from GitHub repos (filters: repository, author)
- search_jira_users: Find JIRA users by name or email
- get_github_recent_activities: Get recent GitHub activities for users
(Refer to tool descriptions for more details.)

ALWAYS:
- Identify the intent (member(s), activity type, time range, status, etc)
- Call the minimum needed tools (do NOT repeat or hallucinate tool calls)
- Compose results as a concise, readable summary
- If no relevant activity is found, explain with context
- Remember previous conversation context and answer follow-ups naturally.
"""
        
        return base_prompt

    async def _initialize_llm(self, intent: Optional[AgentIntent] = None):
        """Initialize LLM with optional intent-enhanced system prompt."""
        system_prompt = self._create_system_prompt(intent)
        
        if self.llm_model == "google/gemini-1.5-flash":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.google_api_key,
                model_kwargs={"system_instruction": system_prompt}  
            )
        else:
            raise ValueError(f"Unsupported LLM model: {self.llm_model}")

    async def _initialize_agent(self, intent: Optional[AgentIntent] = None):
        """Initialize agent with optional intent information."""
        if self._llm is None or intent is not None:
            # Reinitialize LLM with intent-enhanced prompt
            self._llm = await self._initialize_llm(intent)
        
        memory = ConversationBufferMemory(memory_key=self.memory_key, return_messages=True)

        return initialize_agent(
            tools=tools,
            llm=self._llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=memory,
            verbose=True,
        )

    async def run(self, query: str, intent: Optional[AgentIntent] = None):
        """
        Run the agent with optional intent information.
        
        Args:
            query: User's natural language query
            intent: Optional parsed intent from AgentIntentParser
            
        Returns:
            Agent's response
        """
        agent = await self._initialize_agent(intent)
        
        if intent:
            # Create enhanced query with intent context
            enhanced_query = f"""
Original Query: {query}

Enhanced Context:
- Target Members: {', '.join(intent.members) if intent.members else 'None specified'}
- Target Projects: {', '.join(intent.projects) if intent.projects else 'None specified'}  
- Target Repositories: {', '.join(intent.repositories) if intent.repositories else 'None specified'}
- Time Context: {intent.time_range.label if intent.time_range else 'Not specified'}

Execute this query using the enhanced context and recommendations provided in your system prompt.
"""
            return agent.run(enhanced_query)
        else:
            return agent.run(query)
