from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.core.tools import tools
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory


class BasicAgent:

    _llm: ChatGoogleGenerativeAI | ChatOpenAI | None = None

    SYSTEM_PROMPT="""
    You are Team Activity Monitor, a helpful assistant that summarizes team member activities by combining JIRA and GitHub data.

    — You receive user questions about what teammates are working on or have done (issues, tickets, PRs, commits, etc).
    — For each query, you should:
    1. Parse the agent intent: who/what/time range; what action/result is expected.
    2. Use the available tools (search_jira_issues, get_github_commits, etc). Only use what is described in the tool descriptions.
    3. Combine and synthesize the tool results into a clear and user-friendly answer.
    4. If a query cannot be answered by the available tools, politely clarify or explain the limitation.

    Available tools:
    - search_jira_issues: Look up JIRA issues (filters: project_key, assignee, status, etc)
    - get_github_commits: Fetch commit history from GitHub repos (filters: repository, author)
    (Refer to tool descriptions for more details.)

    ALWAYS:
    - Identify the intent (member(s), activity type, time range, status, etc)
    - Call the minimum needed tools (do NOT repeat or hallucinate tool calls)
    - Compose results as a concise, readable summary
    - If no relevant activity is found, explain with context (e.g. "No recent activity for John this week.")
    - Remember previous conversation context and answer follow-ups naturally.
    """

    def __init__(self, memory_key: str = "chat_history", llm_model: str = "google/gemini-1.5-flash"):
        self.memory_key = memory_key
        self.llm_model = llm_model
        self._llm = None

    async def _initialize_llm(self):
        if self.llm_model == "google/gemini-1.5-flash":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.google_api_key,
                model_kwargs={"system_instruction": self.SYSTEM_PROMPT}  
            )
        else:
            raise ValueError(f"Unsupported LLM model: {self.llm_model}")

    async def _initialize_agent(self):
        memory = ConversationBufferMemory(memory_key=self.memory_key, return_messages=True)

        return initialize_agent(
            tools=tools,
            llm=self._llm,
            agent=AgentType.OPENAI_FUNCTIONS,  # This agent type works with Gemini and all major modern models
            memory=memory,
            verbose=True,
        )

    async def run(self, query: str):
        if self._llm is None:
            self._llm = await self._initialize_llm()
        agent = await self._initialize_agent()
        return agent.run(query)
        