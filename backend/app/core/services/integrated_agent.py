"""
Integrated Agent Service that combines AgentIntentParser and BasicAgent.
First parses intent, then executes with enhanced context.
"""
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from app.core.config import settings
from app.core.tools import tools
from app.core.services.intent_parser import AgentIntentParser
from app.models.schemas import AgentIntent, IrrelevantQueryError


class IntegratedAgent:
    """
    Enhanced agent that combines intent parsing with execution.
    
    Workflow:
    1. Parse intent using AgentIntentParser
    2. Extract user/project/repository information
    3. Pass structured context to BasicAgent
    4. Execute with enhanced context awareness
    """
    
    def __init__(self, memory_key: str = "chat_history", llm_model: str = "google/gemini-1.5-flash"):
        self.memory_key = memory_key
        self.llm_model = llm_model
        self._llm = None
        self._intent_parser = None
        
    async def _initialize_llm(self):
        """Initialize the LLM based on model type."""
        if self.llm_model == "google/gemini-1.5-flash":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.google_api_key,
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported LLM model: {self.llm_model}")
    
    async def _initialize_intent_parser(self):
        """Initialize the AgentIntentParser."""
        if self._llm is None:
            self._llm = await self._initialize_llm()
        return AgentIntentParser(self._llm)
    
    def _create_enhanced_system_prompt(self, intent: AgentIntent) -> str:
        """
        Create an enhanced system prompt with intent information.
        """
        base_prompt = """
You are Team Activity Monitor, a helpful assistant that summarizes team member activities by combining JIRA and GitHub data.

ENHANCED CONTEXT FROM INTENT ANALYSIS:
"""
        
        # Add parsed intent information
        if intent.intent:
            base_prompt += f"\n🎯 USER'S INTENT: {intent.intent}\n"
        
        if intent.members:
            base_prompt += f"\n👥 IDENTIFIED MEMBERS: {', '.join(intent.members)}"
            base_prompt += f"\n   → Use these name variations when searching for users"
        
        if intent.projects:
            base_prompt += f"\n📁 TARGET PROJECTS: {', '.join(intent.projects)}"
            base_prompt += f"\n   → Focus on these JIRA project keys"
        
        if intent.repositories:
            base_prompt += f"\n📂 TARGET REPOSITORIES: {', '.join(intent.repositories)}"
            base_prompt += f"\n   → Focus on these GitHub repositories"
        
        if intent.time_range:
            base_prompt += f"\n⏰ TIME CONTEXT: {intent.time_range.label}"
            if intent.time_range.start:
                base_prompt += f"\n   → Start: {intent.time_range.start}"
            if intent.time_range.end:
                base_prompt += f"\n   → End: {intent.time_range.end}"
        
        if intent.operations:
            base_prompt += f"\n\n🔧 RECOMMENDED OPERATIONS ({len(intent.operations)} steps):"
            for i, op in enumerate(intent.operations, 1):
                base_prompt += f"\n   {i}. {op.tool} - {op.action}"
                if op.filters:
                    key_filters = {k: v for k, v in op.filters.items() if k in ['query', 'assignee', 'project_key', 'usernames', 'repositories', 'status']}
                    if key_filters:
                        base_prompt += f"\n      Suggested filters: {key_filters}"
        
        if intent.context:
            base_prompt += f"\n\n📝 MATCHING STRATEGY:"
            for key, value in intent.context.items():
                if isinstance(value, str) and len(value) < 200:
                    base_prompt += f"\n   • {key}: {value}"
        
        base_prompt += """

EXECUTION INSTRUCTIONS:
1. Use the identified members, projects, and repositories from the intent analysis
2. Follow the recommended operations sequence when possible
3. Apply the suggested filters for more accurate results
4. Cross-reference JIRA and GitHub data using the member name variations
5. Provide a comprehensive, well-formatted response

IMPORTANT GUIDELINES:
- Use the exact member name variations provided above for better matching
- Focus on the identified projects and repositories
- Respect the time context when filtering data
- Combine results from multiple sources for complete answers
- If no data is found, explain using the context provided

Available tools: search_jira_issues, get_github_commits, search_jira_users, get_github_recent_activities, and more.
(Refer to individual tool descriptions for detailed parameters)
"""
        
        return base_prompt
    
    async def _initialize_enhanced_agent(self, intent: AgentIntent):
        """Initialize the execution agent with enhanced context."""
        if self._llm is None:
            self._llm = await self._initialize_llm()
        
        # Create enhanced system prompt with intent information
        enhanced_prompt = self._create_enhanced_system_prompt(intent)
        
        # Initialize LLM with enhanced system instruction
        enhanced_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.google_api_key,
            model_kwargs={"system_instruction": enhanced_prompt}
        )
        
        memory = ConversationBufferMemory(memory_key=self.memory_key, return_messages=True)
        
        return initialize_agent(
            tools=tools,
            llm=enhanced_llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=memory,
            verbose=True,
        )
    
    async def run(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Run the integrated workflow: Intent Parsing → Enhanced Execution
        
        Args:
            query: User's natural language query
            chat_history: Optional chat history for context
            
        Returns:
            Comprehensive response string
        """
        
        if chat_history is None:
            chat_history = []
        
        print(f"🔍 Processing query: '{query}'")
        print("=" * 60)
        
        try:
            # Step 1: Parse Intent
            print("📋 Step 1: Analyzing intent...")
            if self._intent_parser is None:
                self._intent_parser = await self._initialize_intent_parser()
            
            intent_result = await self._intent_parser.parse_intent(query, chat_history)
            
            # Handle irrelevant queries
            if isinstance(intent_result, IrrelevantQueryError):
                return f"❌ Query not relevant to JIRA or GitHub activities.\nReason: {intent_result.reasoning}"
            
            if not isinstance(intent_result, AgentIntent):
                return f"❌ Unexpected intent parsing result: {type(intent_result)}"
            
            # Display parsed intent
            print(f"✅ Intent parsed successfully!")
            print(f"   🎯 Intent: {intent_result.intent}")
            print(f"   👥 Members: {intent_result.members}")
            print(f"   📁 Projects: {intent_result.projects}")
            print(f"   📂 Repositories: {intent_result.repositories}")
            print(f"   ⏰ Time Range: {intent_result.time_range.label if intent_result.time_range else 'Not specified'}")
            print(f"   🔧 Operations: {len(intent_result.operations)} planned")
            print()
            
            # Step 2: Execute with Enhanced Context
            print("🚀 Step 2: Executing with enhanced context...")
            enhanced_agent = await self._initialize_enhanced_agent(intent_result)
            
            # Create enhanced query with context
            enhanced_query = f"""
Original Query: {query}

Context from Intent Analysis:
- Target Members: {', '.join(intent_result.members) if intent_result.members else 'None specified'}
- Target Projects: {', '.join(intent_result.projects) if intent_result.projects else 'None specified'}
- Target Repositories: {', '.join(intent_result.repositories) if intent_result.repositories else 'None specified'}
- Time Context: {intent_result.time_range.label if intent_result.time_range else 'Not specified'}

Please execute this query using the enhanced context provided in your system prompt.
"""
            
            final_response = enhanced_agent.run(enhanced_query)
            
            print("✅ Execution completed!")
            print()
            
            return final_response
            
        except Exception as e:
            error_msg = f"❌ Error in integrated workflow: {str(e)}"
            print(error_msg)
            return error_msg


# Convenience function for easy usage
async def get_enhanced_response(query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Convenience function to get enhanced response using the integrated workflow.
    
    Args:
        query: User's natural language query
        chat_history: Optional chat history for context
        
    Returns:
        Enhanced response with intent-aware execution
    """
    integrated_agent = IntegratedAgent()
    return await integrated_agent.run(query, chat_history)
