from langchain_core.tools import tool
import json
from typing import Dict, Any

def get_current_user_id():
    """Helper function to get current user ID from context"""
    return getattr(get_current_user_id, 'user_id', 'unknown')

def set_user_context(user_id: str):
    """Set user context for preference operations"""
    get_current_user_id.user_id = user_id

def extract_user_preferences_silently(text: str, async_mode: bool = False) -> dict:
    """Internal function to silently extract user preferences without agent awareness."""
    try:
        from document_manager import DocumentManager
        from preference_detector import should_extract_preferences
        
        # Check if text contains preferences
        if not should_extract_preferences(text):
            return {"success": False, "reason": "No preference indicators found in text"}
        
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        result = doc_manager.extract_and_save_preferences(user_id, text, async_mode)
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Error extracting preferences: {str(e)}"}

@tool
def analyze_and_extract_preferences(text: str) -> dict:
    """Silently extract user preferences in background. Returns immediately to maintain conversation flow."""
    try:
        from preference_detector import PreferenceDetector
        from document_manager import DocumentManager
        
        detector = PreferenceDetector()
        analysis = detector.should_extract_preferences(text)
        
        if analysis["should_extract"]:
            user_id = get_current_user_id()
            doc_manager = DocumentManager()
            
            # Start background processing (async invocation)
            doc_manager.extract_and_save_preferences_async(user_id, text)
            
            return {
                "success": True,
                "message": "Preference extraction started in background",
                "silent": True
            }
        else:
            return {
                "success": True,
                "message": "No preferences detected",
                "silent": True
            }
        
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}", "silent": True}

@tool
def get_user_preferences() -> dict:
    """Get user's saved preferences for plan generation."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        result = doc_manager.get_user_preferences(user_id)
        if result['success']:
            return {
                "success": True,
                "preferences": result['data'],
                "user_id": user_id
            }
        else:
            return {"success": False, "error": "No preferences found"}
            
    except Exception as e:
        return {"success": False, "error": f"Error getting preferences: {str(e)}"}

@tool
def update_user_preferences(category: str, activity: str, preference_type: str) -> dict:
    """Update user preferences. category: physical/mental/diet/medical, preference_type: like/dislike"""
    try:
        from document_manager import DocumentManager
        from schemas import UserPreferences
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        # Get existing preferences
        existing = doc_manager.get_user_preferences(user_id)
        if existing['success']:
            prefs_data = existing['data']
        else:
            prefs_data = {
                "physical_activities_like": [],
                "physical_activities_dislike": [],
                "mental_activities_like": [],
                "mental_activities_dislike": [],
                "diet_activities_like": [],
                "diet_activities_dislike": [],
                "medical_activities_like": [],
                "medical_activities_dislike": []
            }
        
        # Update specific preference
        key = f"{category}_activities_{preference_type}"
        if key in prefs_data and activity not in prefs_data[key]:
            prefs_data[key].append(activity)
        
        # Save updated preferences
        preferences = UserPreferences(**prefs_data)
        result = doc_manager.save_user_preferences(user_id, preferences)
        
        return {
            "success": True,
            "updated_key": key,
            "activity": activity,
            "save_result": result
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error updating preferences: {str(e)}"}

def get_preference_tools():
    """Get preference management tools available to the agent"""
    return [
        analyze_and_extract_preferences,
        get_user_preferences,
        update_user_preferences
    ]