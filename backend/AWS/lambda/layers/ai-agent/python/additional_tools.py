from langchain_core.tools import tool
from datetime import datetime

def get_current_user_id():
    """Helper function to get current user ID from context"""
    return getattr(get_current_user_id, 'user_id', 'unknown')

@tool
def get_current_time() -> str:
    """Get current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def explain_aactt_framework() -> str:
    """Explain the AACTT framework structure and components."""
    return """
AACTT Framework Explanation:

AACTT is a structured approach for creating wellness plans with 5 key components:

• A = ACTION: What specific activity or intervention to perform
• A = ACTOR: Who will perform the activity (usually the user/patient)
• C = CONTEXT: Where and under what conditions the activity takes place
• T = TARGET: The specific goal or objective to achieve
• T = TIME: When and how often to perform (frequency and duration)

Example AACTT Plan:
- Action: 30-minute walk
- Actor: You (the user)
- Context: In the neighborhood park, preferably in the morning
- Target: Improve cardiovascular health and maintain mobility
- Time: 3 times per week, 30 minutes each session

This framework ensures comprehensive, actionable wellness plans tailored to individual needs.
"""

@tool
def calculate_bmi(height_cm: float, weight_kg: float) -> dict:
    """Calculate BMI from height (cm) and weight (kg)."""
    try:
        if height_cm <= 0 or weight_kg <= 0:
            return {"success": False, "error": "Height and weight must be positive numbers"}
        
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        
        # BMI categories
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"
        
        return {
            "success": True,
            "bmi": round(bmi, 1),
            "category": category,
            "height_cm": height_cm,
            "weight_kg": weight_kg
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def internet_search(query: str) -> dict:
    """Search the internet for current information."""
    try:
        from search_engine import searchEngine
        
        if not query or not query.strip():
            return {"success": False, "error": "Search query is required"}
        
        results = searchEngine.search(query.strip())
        
        return {
            "success": True,
            "query": query.strip(),
            "results": results,
            "total_results": len(results),
            "note": "Limited to top 3 results for performance"
        }
    except Exception as e:
        return {"success": False, "error": f"Internet search error: {str(e)}"}

@tool
def get_user_login_info() -> dict:
    """Get user's login information and engagement status."""
    try:
        from cognito_helper import CognitoHelper
        user_id = get_current_user_id()
        cognito = CognitoHelper()
        return cognito.get_user_login_info(user_id)
    except Exception as e:
        return {"success": False, "error": f"Error getting login info: {str(e)}"}

@tool
def set_reminder(reminder_text: str, reminder_time: str) -> dict:
    """Set a health reminder for the user."""
    try:
        user_id = get_current_user_id()
        # This would integrate with a reminder/notification system
        return {
            "success": True,
            "message": f"Reminder set: '{reminder_text}' for {reminder_time}",
            "reminder_id": f"reminder_{user_id}_{datetime.now().timestamp()}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}











@tool
def find_nearby_healthcare(service_type: str, location: str = "") -> dict:
    """Find nearby healthcare services (hospitals, clinics, pharmacies)."""
    try:
        if not location:
            # Could get from user profile
            location = "user location"
        
        valid_services = ['hospital', 'clinic', 'pharmacy', 'urgent_care', 'specialist']
        if service_type.lower() not in valid_services:
            return {"success": False, "error": f"Invalid service type. Supported: {valid_services}"}
        
        # This would integrate with maps/location services
        return {
            "success": True,
            "message": f"Found {service_type} services near {location}",
            "service_type": service_type,
            "location": location,
            "note": "This would return actual nearby healthcare facilities"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_additional_tools():
    """Get all additional utility tools"""
    return [
        get_current_time,
        explain_aactt_framework,
        calculate_bmi,
        internet_search,
        get_user_login_info,
        set_reminder,
        find_nearby_healthcare
    ]