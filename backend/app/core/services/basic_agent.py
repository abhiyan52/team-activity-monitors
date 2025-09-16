from typing import Optional, Dict, Any, List
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings
from app.core.tools import tools
from app.core.services.intent_parser import AgentIntentParser


def clean_json_response(response_str: str) -> str:
    """
    Clean JSON response by removing markdown code blocks and extra formatting.
    
    Args:
        response_str: Raw response string that might contain markdown
        
    Returns:
        Clean JSON string
    """
    # Remove markdown code blocks
    cleaned = response_str.strip()
    
    # Remove ```json and ``` markers
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]  # Remove ```json
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]   # Remove ```
        
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]  # Remove ending ```
        
    return cleaned.strip()


def check_query_relevance(intent_json_str: str) -> bool:
    """
    Check if the query is relevant by parsing the JSON.
    
    Args:
        intent_json_str: Raw JSON string from intent parser
        
    Returns:
        True if query is relevant, False otherwise
    """
    try:
        cleaned_json = clean_json_response(intent_json_str)
        intent_data = json.loads(cleaned_json)
        return intent_data.get("is_relevant", False)
    except:
        return False


class BasicAgent:
    """
    Simple agent with persistent memory support.
    Uses database-backed conversation memory for persistence across sessions.
    """
    
    def __init__(self, thread_id: Optional[str] = None):
        self.thread_id = thread_id
        self.llm = None
        self.agent = None
        self._memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.intent_parser = None
        
    def _get_simple_prompt(self) -> str:
        """Simple system prompt for the agent."""
        return """
          You are responsible for answering question related to project management and team activities.
          You are a part of bigger system where the intent of the user is parsed and then you are given a JSON with the steps to answer the question.
          You are a part of project management team and you will get question on what indivual team members are working on
          or have worked on. You have access to JIRA and Github with various tools to get the information.

          JIRA is a project management tool and Github is a version control platform. The data will be stored in JIRA and Github.
          We already have a intent parser which will give you a JSON consisting of how to answer the question.
          You should take the intent parser's JSON and use the tools to answer the question.

          You need to do the things step by step:

          1. Understand the intent of the user using the intent key in the intent parser's JSON.
          2. For each operation in the operations key, you need to use the tool to get the information.
          3. After each iteration, you might need to use the output of the previous iteration to get the information for the next iteration.
          4. After all the iterations, you need to combine the information to answer the question.
          5. If the question cannot be answered by the tools, you need to say that you cannot answer the question.
          6. You need to remember the previous conversation context and answer the question accordingly.
        """

    def add_to_memory(self, user_message: str, ai_response: str):
        """
        Add messages to agent memory.
        
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
            chat_history = memory_vars.get("chat_history", [])
            
            return {
                "message_count": len(chat_history),
                "thread_id": self.thread_id,
                "recent_messages": [
                    {
                        "type": type(msg).__name__,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    }
                    for msg in chat_history[-4:]  # Last 4 messages
                ]
            }
        except Exception as e:
            return {"error": str(e), "thread_id": self.thread_id}
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self._memory.clear()
    
    def load_conversation_history(self, messages: List[Dict[str, str]]):
        """
        Load conversation history into memory.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
        """
        self.clear_memory()
        
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i]
                ai_msg = messages[i + 1]
                
                if user_msg.get('role') == 'user' and ai_msg.get('role') == 'assistant':
                    self.add_to_memory(user_msg['content'], ai_msg['content'])

    async def _initialize(self):
        """Initialize LLM and agent."""
        if self.llm is None:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.google_api_key,
                model_kwargs={"system_instruction": self._get_simple_prompt()},
                temperature=0
            )
        
        # Initialize intent parser with the same LLM if not already done
        if self.intent_parser is None:
            self.intent_parser = AgentIntentParser(self.llm)
        
        if self.agent is None:
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                memory=self._memory,
                verbose=True
            )
    
    async def run(self, query: str) -> str:
        """
        Run the agent with intent parsing integration.
        
        Args:
            query: User's natural language query
            
        Returns:
            Agent's response or static string for irrelevant queries
        """
        try:
            # Step 1: Initialize agent and intent parser
            await self._initialize()
            
            # Step 2: Get memory context for intent parsing
            memory_context = []
            try:
                memory_vars = self._memory.load_memory_variables({})
                chat_history = memory_vars.get("chat_history", [])
                
                for message in chat_history:
                    if hasattr(message, 'content'):
                        if isinstance(message, HumanMessage):
                            memory_context.append({"role": "user", "content": message.content})
                        elif isinstance(message, AIMessage):
                            memory_context.append({"role": "assistant", "content": message.content})
            except Exception as e:
                print(f"Warning: Could not extract memory context: {e}")
                memory_context = []
            
            # Step 3: Parse intent and get raw JSON
            intent_json_str = await self.intent_parser.parse_intent(query, memory_context)


            
            # Step 4: Check if query is relevant
            if not check_query_relevance(intent_json_str):
                return "I can only help with questions related to JIRA and GitHub team activities. Please ask about team member activities, project status, commits, or similar work-related topics."
            
            # Step 5: Clean the JSON and pass to agent
            cleaned_json = clean_json_response(intent_json_str)
            
            enhanced_query = f"""
                User Query: {query}

                Intent Analysis (JSON):
                {cleaned_json}

                Please use the intent analysis above to guide your tool selection and execution. Focus on what the user is asking for based on the parsed intent.
            """
            
            return self.agent.run(enhanced_query)
            
        except Exception as e:
            print(f"Error in agent execution: {e}")
            # Fallback to basic agent without intent
            try:
                await self._initialize()
                return self.agent.run(query)
            except Exception as fallback_error:
                return f"Error processing your request: {str(e)}"


# Global agent instances for persistence
_global_agents: Dict[str, BasicAgent] = {}

def get_agent_for_thread(thread_id: str) -> BasicAgent:
    """
    Get or create a BasicAgent instance for a specific thread.
    This ensures memory persistence across requests.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        BasicAgent instance
    """
    if thread_id not in _global_agents:
        _global_agents[thread_id] = BasicAgent(thread_id=thread_id)
    
    return _global_agents[thread_id]

def clear_thread_memory(thread_id: str):
    """Clear memory for a specific thread."""
    if thread_id in _global_agents:
        _global_agents[thread_id].clear_memory()

def get_all_thread_summaries() -> Dict[str, Dict[str, Any]]:
    """Get memory summaries for all active threads."""
    return {
        thread_id: agent.get_memory_summary() 
        for thread_id, agent in _global_agents.items()
    }
        