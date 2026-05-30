from langchain_core.tools import tool
import json
from datetime import datetime

def get_current_user_id():
    """Helper function to get current user ID from context"""
    return getattr(get_current_user_id, 'user_id', 'unknown')

def set_user_context(user_id: str):
    """Set user context for profile operations"""
    get_current_user_id.user_id = user_id

@tool
def get_user_profile() -> dict:
    """Get user's complete profile information including demographics, health data, and preferences."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        profile = doc_manager.get_user_profile(user_id)
        if not profile:
            return {"success": False, "error": "User profile not found"}
        
        return {
            "success": True,
            "profile": profile,
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": f"Error retrieving profile: {str(e)}"}

@tool
def update_user_profile(field: str, value: str) -> dict:
    """Update a specific field in the user's profile."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        # Get current profile
        profile = doc_manager.get_user_profile(user_id)
        if not profile:
            profile = {}
        
        # Update the field
        profile[field] = value
        profile['last_updated'] = datetime.now().isoformat()
        
        # Save updated profile
        success = doc_manager.save_user_profile(user_id, profile)
        
        if success:
            return {
                "success": True,
                "message": f"Updated {field} to: {value}",
                "field": field,
                "value": value
            }
        else:
            return {"success": False, "error": "Failed to save profile update"}
            
    except Exception as e:
        return {"success": False, "error": f"Error updating profile: {str(e)}"}



@tool
def get_profile_summary() -> dict:
    """Get a concise summary of user's key profile information."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        profile = doc_manager.get_user_profile(user_id)
        if not profile:
            return {"success": False, "error": "User profile not found"}
        
        profile_data = profile['data'] if profile['success'] else {}
        
        # Extract key information
        summary = {
            "age": profile_data.get('age', 'Not specified'),
            "health_goals": profile_data.get('health_goals', 'Not set'),
            "medical_conditions": profile_data.get('medical_conditions', 'None specified'),
            "preferences": profile_data.get('preferences', 'Not set'),
            "last_updated": profile_data.get('last_updated', 'Never')
        }
        
        return {
            "success": True,
            "summary": summary,
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": f"Error getting profile summary: {str(e)}"}

def get_profile_tools():
    """Get all profile management tools"""
    return [
        get_user_profile,
        update_user_profile,
        get_profile_summary
    ]