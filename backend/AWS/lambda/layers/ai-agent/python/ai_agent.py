import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging

try:
    from chat_history_manager import ChatHistoryManager
except ImportError:
    import sys
    sys.path.append('../../livewell-core/python')
    from chat_history_manager import ChatHistoryManager

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class GeminiAIAgent:
    def __init__(self, user_id: str = "system", chat_session_id: str = "agent", chat_session_name: str = "LiveWell Chat", token: str = None):
        self.user_id = user_id
        self.chat_session_id = chat_session_id
        self.chat_session_name = chat_session_name
        self.token = token
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.chat_history = ChatHistoryManager()
        self.tools_used = []
        self.function_responses = {}

        if not self.gemini_api_key:
            raise ValueError("Gemini API key is required")
        
        # Initialize Gemini LLM with tools
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            google_api_key=self.gemini_api_key,
            temperature=0.2
        )
        
        # Get all available tools
        from agent_tools import get_langchain_tools
        self.all_tools = get_langchain_tools(user_id, chat_session_id, token)
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.all_tools)
        
        # Load chat history
        self.conversation_history = self._load_chat_history()
        
        logger.info(f"Initialized with {len(self.all_tools)} tools")
        for tool in self.all_tools:
            logger.info(f"Available tool: {tool.name} - {tool.description}")
    

    

    
    def _load_chat_history(self) -> list:
        try:
            result = self.chat_history.get_conversation(self.user_id, self.chat_session_id)
            if result['success']:
                messages = result['data']['messages'][-10:]  # Last 10 messages for context
                # Convert to simple format
                formatted_messages = []
                for msg in messages:
                    if msg.get('role') in ['user', 'assistant']:
                        formatted_messages.append({
                            "role": msg.get('role'),
                            "content": msg.get('content', '')
                        })
                return formatted_messages
            return []
        except Exception as e:
            logger.warning(f"Failed to load chat history: {str(e)}")
            return []
    

    
    def run(self, query: str, reload_history: bool = False) -> dict:
        self.tools_used = []
        self.function_responses = {}
        
        try:
            logger.info(f"Query: {query}")
            
            # Build messages
            messages = [
                SystemMessage(content="You are LiveWell AI Assistant. Use tools when users ask about weather, time, preferences, plans, or medical info. When users say 'I love/hate/like/dislike' something, use analyze_and_extract_preferences.")
            ]
            
            # Add chat history
            for msg in self.conversation_history[-6:]:
                if msg.get('role') == 'user':
                    messages.append(HumanMessage(content=msg.get('content', '')))
                elif msg.get('role') == 'assistant':
                    messages.append(AIMessage(content=msg.get('content', '')))
            
            # Add current query
            messages.append(HumanMessage(content=query))
            
            # Let LangChain handle tool calls automatically
            response = self.llm_with_tools.invoke(messages)
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response content: {getattr(response, 'content', 'NO_CONTENT')}")
            logger.info(f"Response tool_calls: {getattr(response, 'tool_calls', 'NO_TOOL_CALLS')}")
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract tool usage from response for logging
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    self.tools_used.append(tool_call.get('name', 'unknown_tool'))
                    self.function_responses[tool_call.get('name', 'unknown_tool')] = "executed"
            
            # Ensure we have a response
            if not response_text or response_text.strip() == "":
                logger.warning("Empty response detected, generating fallback")
                response_text = "I understand. How can I help you with your health and wellness today?"
            
            return {
                "response": response_text,
                "tools_used": self.tools_used,
                "function_responses": self.function_responses,
                "steps_count": len(self.tools_used)
            }
            
        except Exception as e:
            logger.error(f"Agent error: {str(e)}")
            return {
                "response": f"I'm experiencing technical difficulties. Error: {str(e)}",
                "tools_used": self.tools_used,
                "function_responses": self.function_responses,
                "steps_count": len(self.tools_used),
                "error": str(e)
            }
            
        finally:
            # Save chat history
            try:
                agent_steps = []
                for tool_name in self.tools_used:
                    if tool_name in self.function_responses:
                        agent_steps.append({
                            "action": tool_name,
                            "observation": str(self.function_responses[tool_name])
                        })
                
                self.chat_history.add_agent_interaction(
                    user_id=self.user_id,
                    conversation_id=self.chat_session_id,
                    user_input=query,
                    agent_response=response_text,
                    agent_steps=agent_steps if agent_steps else None,
                    chat_session_name=self.chat_session_name,
                    hidden_user_message=query.startswith('[SYSTEM]')
                )
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": response_text})
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
                    
            except Exception as e:
                logger.error(f"Failed to save chat history: {str(e)}")
