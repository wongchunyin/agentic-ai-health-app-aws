import os
import sys
import json
import uuid
import logging
from datetime import datetime
from langchain_core.tools import tool

# Import dependencies
from aactt_utils import generate_aactt_plan
from weather_utils import get_weather_forecast, check_outdoor_weather

try:
    from document_manager import DocumentManager
    from assessment_manager import AssessmentManager
    from cognito_helper import CognitoHelper
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../livewell-core/python'))
    from document_manager import DocumentManager
    from assessment_manager import AssessmentManager
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../aws/python'))
    from cognito_helper import CognitoHelper

# Import profile tools
try:
    from profile_tools import get_profile_tools, set_user_context as set_profile_context
except ImportError:
    def get_profile_tools():
        return []
    def set_profile_context(user_id):
        pass

# Import preference tools
try:
    from preference_tools import get_preference_tools, set_user_context as set_preference_context
except ImportError:
    def get_preference_tools():
        return []
    def set_preference_context(user_id):
        pass

def get_current_user_id():
    """Helper function to get current user ID from context"""
    return getattr(get_current_user_id, 'user_id', 'unknown')





@tool
def search_medical_info(query: str) -> dict:
    """Search medical database for health information, symptoms, diseases, and treatments."""
    try:
        from medical_search_manager import MedicalSearchManager
        search_manager = MedicalSearchManager()
        results = search_manager.search(query, 3)
        
        if not results:
            return {
                "success": False,
                "results": [],
                "query": query,
                "error": f"No medical information found for '{query}'"
            }
        
        medical_results = []
        for result in results[:3]:
            question = result.get('question', 'Unknown question')
            answer = result.get('answer', 'No answer available')
            if len(answer) > 300:
                answer = answer[:300] + "..."
            medical_results.append({
                "question": question,
                "answer": answer
            })
        
        return {
            "success": True,
            "results": medical_results,
            "query": query,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "query": query,
            "error": str(e)
        }





# Import assessment, weather, and plan tools
try:
    from assessment_tools import get_assessment_tools
except ImportError:
    def get_assessment_tools():
        return []

try:
    from weather_tools import get_weather_tools
except ImportError:
    def get_weather_tools():
        return []

try:
    from plan_tools import get_plan_tools
except ImportError:
    def get_plan_tools():
        return []

try:
    from additional_tools import get_additional_tools
except ImportError:
    def get_additional_tools():
        return []

def get_langchain_tools(user_id: str, chat_session_id: str, token: str = None):
    """Get LangChain tools for proper function calling"""
    get_current_user_id.user_id = user_id
    set_profile_context(user_id)
    set_preference_context(user_id)
    
    # Get all tool categories
    profile_tools = get_profile_tools()
    assessment_tools = get_assessment_tools()
    weather_tools = get_weather_tools()
    plan_tools = get_plan_tools()
    additional_tools = get_additional_tools()
    preference_tools = get_preference_tools()
    
    # Set user_id for tools that need it
    for tool_list in [profile_tools, assessment_tools, plan_tools, additional_tools, preference_tools]:
        for tool in tool_list:
            if hasattr(tool, 'func') and hasattr(tool.func, '__globals__'):
                if 'get_current_user_id' in tool.func.__globals__:
                    tool.func.__globals__['get_current_user_id'].user_id = user_id
    
    tools = [
        search_medical_info
    ] + profile_tools + plan_tools + weather_tools + assessment_tools + additional_tools + preference_tools
    
    return tools