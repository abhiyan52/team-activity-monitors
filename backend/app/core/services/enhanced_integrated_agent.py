"""
Enhanced Integrated Agent with improved memory management.
Maintains conversation history across intent parsing and execution phases.
"""
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.core.tools import tools
from app.core.services.intent_parser import AgentIntentParser
from app.models.schemas import AgentIntent, IrrelevantQueryError


class EnhancedIntegratedAgent:
    """
    Enhanced integrated agent with persistent memory across intent parsing and execution.
    
    Features:
    - Persistent conversation memory
    - Intent-aware execution with memory context
    - Chat history preservation between phases
    - Memory-aware intent parsing
    """
    
    def __init__(self, memory_key: str = "chat_history", llm_model: str = "google/gemini-1.5-flash"):
        self.memory_key = memory_key
        self.llm_model = llm_model
        self._llm = None
        self._intent_parser = None
        self._memory = ConversationBufferMemory(memory_key=memory_key, return_messages=True)
        
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
    
    def _get_memory_context(self) -> List[Dict[str, str]]:
        """
        Extract memory context for intent parsing.
        
        Returns:
            List of message dictionaries for intent parser
        """
        try:
            # Get memory variables
            memory_vars = self._memory.load_memory_variables({})
            chat_history = memory_vars.get(self.memory_key, [])
            
            # Convert to simple dict format for intent parser
            context = []
            for message in chat_history:
                if hasattr(message, 'content'):
                    if isinstance(message, HumanMessage):
                        context.append({"role": "user", "content": message.content})
                    elif isinstance(message, AIMessage):
                        context.append({"role": "assistant", "content": message.content})
            
            return context
            
        except Exception as e:
            print(f"Warning: Could not extract memory context: {e}")
            return []
    
    def _create_enhanced_system_prompt(self, intent: AgentIntent) -> str:
        """
        Create an enhanced system prompt with intent information and memory context.
        """
        base_prompt = """
You are Team Activity Monitor, a helpful assistant that summarizes team member activities by combining JIRA and GitHub data.

CONVERSATION MEMORY CONTEXT:
You have access to previous conversation history through your memory system. Use this context to:
- Understand follow-up questions and references
- Maintain conversation continuity
- Avoid repeating information already provided
- Build upon previous queries and responses

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
1. Consider previous conversation context from memory
2. Use the identified members, projects, and repositories from the intent analysis
3. Follow the recommended operations sequence when possible
4. Apply the suggested filters for more accurate results
5. Cross-reference JIRA and GitHub data using the member name variations
6. Provide responses that build upon previous conversation context
7. Avoid repeating information already shared in the conversation

MEMORY-AWARE GUIDELINES:
- Reference previous queries and responses when relevant
- Use pronouns and context appropriately ("as I mentioned before", "continuing from our previous discussion")
- Build upon previous results rather than starting from scratch
- If asked for updates, compare with previously shared information

Available tools: search_jira_issues, get_github_commits, search_jira_users, get_github_recent_activities, and more.
(Refer to individual tool descriptions for detailed parameters)
"""
        
        return base_prompt
    
    async def _initialize_enhanced_agent(self, intent: AgentIntent):
        """Initialize the execution agent with enhanced context and persistent memory."""
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
        
        # Use the persistent memory instance
        return initialize_agent(
            tools=tools,
            llm=enhanced_llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self._memory,  # Use persistent memory
            verbose=True,
        )
    
    def add_to_memory(self, user_message: str, ai_response: str):
        """
        Manually add messages to memory.
        
        Args:
            user_message: User's message
            ai_response: AI's response
        """
        self._memory.chat_memory.add_user_message(user_message)
        self._memory.chat_memory.add_ai_message(ai_response)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current memory state.
        
        Returns:
            Dictionary with memory information
        """
        try:
            memory_vars = self._memory.load_memory_variables({})
            chat_history = memory_vars.get(self.memory_key, [])
            
            return {
                "message_count": len(chat_history),
                "recent_messages": [
                    {
                        "type": type(msg).__name__,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    }
                    for msg in chat_history[-4:]  # Last 4 messages
                ],
                "memory_key": self.memory_key
            }
        except Exception as e:
            return {"error": str(e)}
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self._memory.clear()
    
    async def run(self, query: str) -> str:
        """
        Run the integrated workflow with persistent memory.
        
        Args:
            query: User's natural language query
            
        Returns:
            Comprehensive response string with memory context
        """
        
        print(f"🔍 Processing query: '{query}'")
        print("=" * 60)
        
        try:
            # Get current memory context
            memory_context = self._get_memory_context()
            print(f"💭 Memory context: {len(memory_context)} previous messages")
            
            # Step 1: Parse Intent with Memory Context
            print("📋 Step 1: Analyzing intent with memory context...")
            if self._intent_parser is None:
                self._intent_parser = await self._initialize_intent_parser()
            
            intent_result = await self._intent_parser.parse_intent(query, memory_context)
            
            # Handle irrelevant queries
            if isinstance(intent_result, IrrelevantQueryError):
                error_response = f"❌ Query not relevant to JIRA or GitHub activities.\nReason: {intent_result.reasoning}"
                # Still add to memory for context
                self.add_to_memory(query, error_response)
                return error_response
            
            if not isinstance(intent_result, AgentIntent):
                error_response = f"❌ Unexpected intent parsing result: {type(intent_result)}"
                self.add_to_memory(query, error_response)
                return error_response
            
            # Display parsed intent
            print(f"✅ Intent parsed with memory context!")
            print(f"   🎯 Intent: {intent_result.intent}")
            print(f"   👥 Members: {intent_result.members}")
            print(f"   📁 Projects: {intent_result.projects}")
            print(f"   📂 Repositories: {intent_result.repositories}")
            print(f"   ⏰ Time Range: {intent_result.time_range.label if intent_result.time_range else 'Not specified'}")
            print(f"   🔧 Operations: {len(intent_result.operations)} planned")
            print()
            
            # Step 2: Execute with Enhanced Context and Persistent Memory
            print("🚀 Step 2: Executing with enhanced context and memory...")
            enhanced_agent = await self._initialize_enhanced_agent(intent_result)
            
            # The agent will automatically use the persistent memory
            final_response = enhanced_agent.run(query)
            
            print("✅ Execution completed with memory preserved!")
            print()
            
            return final_response
            
        except Exception as e:
            error_msg = f"❌ Error in integrated workflow: {str(e)}"
            print(error_msg)
            # Add error to memory for context
            self.add_to_memory(query, error_msg)
            return error_msg


# Convenience functions with memory support
_global_agent = None

async def get_enhanced_response_with_memory(query: str, use_persistent_agent: bool = True) -> str:
    """
    Get enhanced response with persistent memory across calls.
    
    Args:
        query: User's natural language query
        use_persistent_agent: If True, reuse the same agent instance for memory persistence
        
    Returns:
        Enhanced response with memory context
    """
    global _global_agent
    
    if use_persistent_agent:
        if _global_agent is None:
            _global_agent = EnhancedIntegratedAgent()
        return await _global_agent.run(query)
    else:
        # Create new agent instance (no memory persistence)
        agent = EnhancedIntegratedAgent()
        return await agent.run(query)

def get_memory_summary() -> Dict[str, Any]:
    """Get memory summary from the persistent agent."""
    global _global_agent
    if _global_agent is None:
        return {"message_count": 0, "status": "No active conversation"}
    return _global_agent.get_memory_summary()

def clear_conversation_memory():
    """Clear the conversation memory from the persistent agent."""
    global _global_agent
    if _global_agent is not None:
        _global_agent.clear_memory()
        print("✅ Conversation memory cleared")
