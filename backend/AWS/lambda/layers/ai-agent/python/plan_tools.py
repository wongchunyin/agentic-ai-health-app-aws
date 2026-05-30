from langchain_core.tools import tool
import json
from datetime import datetime

def get_current_user_id():
    """Helper function to get current user ID from context"""
    return getattr(get_current_user_id, 'user_id', 'unknown')

def set_user_context(user_id: str):
    """Set user context for plan operations"""
    get_current_user_id.user_id = user_id

@tool
def delete_plans_by_criteria(criteria: str) -> dict:
    """Delete plans that match specific criteria (e.g., 'water' for water-related plans)."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        plans_result = doc_manager.get_user_plans(user_id)
        if not plans_result['success'] or not plans_result['data']:
            return {"success": False, "error": "No plans found"}
        
        plans = plans_result['data']
        criteria_lower = criteria.lower()
        deleted_count = 0
        matching_plans = []
        
        # Find and delete matching plans
        for plan in plans:
            action_name = plan.get('action', {}).get('name', '')
            description = plan.get('action', {}).get('description', '')
            target = plan.get('target', '')
            
            # Check if criteria matches in any field (case-insensitive)
            if (criteria_lower in action_name.lower() or 
                criteria_lower in description.lower() or 
                criteria_lower in target.lower()):
                
                matching_plans.append({
                    "plan_id": plan.get('plan_id'),
                    "action_name": plan.get('action', {}).get('name', ''),
                    "description": plan.get('action', {}).get('description', ''),
                    "target": plan.get('target', '')
                })
                
                plan_id = plan.get('plan_id')
                if plan_id:
                    delete_result = doc_manager.delete_plan(user_id, plan_id)
                    if delete_result['success']:
                        deleted_count += 1
        
        # If no matches found, show all available plans
        if deleted_count == 0:
            all_plans = []
            for plan in plans:
                all_plans.append({
                    "plan_id": plan.get('plan_id'),
                    "action_name": plan.get('action', {}).get('name', ''),
                    "description": plan.get('action', {}).get('description', ''),
                    "target": plan.get('target', '')
                })
            
            return {
                "success": False,
                "message": f"No plans found matching '{criteria}'. Available plans:",
                "deleted_count": 0,
                "available_plans": all_plans
            }
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} plans matching '{criteria}'",
            "deleted_count": deleted_count,
            "deleted_plans": matching_plans
        }
            
    except Exception as e:
        return {"success": False, "error": f"Error deleting plans: {str(e)}"}

@tool
def delete_plans_by_ids(plan_ids: str) -> dict:
    """Delete plans by specific plan IDs (comma-separated list)."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        # Parse comma-separated plan IDs
        id_list = [pid.strip() for pid in plan_ids.split(',')]
        deleted_count = 0
        deleted_plans = []
        failed_plans = []
        
        for plan_id in id_list:
            if plan_id:
                delete_result = doc_manager.delete_plan(user_id, plan_id)
                if delete_result['success']:
                    deleted_count += 1
                    deleted_plans.append(plan_id)
                else:
                    failed_plans.append({"plan_id": plan_id, "error": delete_result.get('error', 'Unknown error')})
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} of {len(id_list)} plans",
            "deleted_count": deleted_count,
            "deleted_plans": deleted_plans,
            "failed_plans": failed_plans
        }
            
    except Exception as e:
        return {"success": False, "error": f"Error deleting plans by IDs: {str(e)}"}

@tool
def deactivate_plans_by_criteria(criteria: str) -> dict:
    """Deactivate plans that match specific criteria instead of deleting them."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        plans_result = doc_manager.get_user_plans(user_id)
        if not plans_result['success'] or not plans_result['data']:
            return {"success": False, "error": "No plans found"}
        
        plans = plans_result['data']
        criteria_lower = criteria.lower()
        deactivated_count = 0
        matching_plans = []
        
        for plan in plans:
            action_name = plan.get('action', {}).get('name', '')
            description = plan.get('action', {}).get('description', '')
            target = plan.get('target', '')
            
            if (criteria_lower in action_name.lower() or 
                criteria_lower in description.lower() or 
                criteria_lower in target.lower()):
                
                matching_plans.append({
                    "plan_id": plan.get('plan_id'),
                    "action_name": plan.get('action', {}).get('name', ''),
                    "status": plan.get('status', '')
                })
                
                plan_id = plan.get('plan_id')
                if plan_id and plan.get('status') != 'inactive':
                    result = doc_manager.update_plan_status(user_id, plan_id, 'inactive')
                    if result['success']:
                        deactivated_count += 1
        
        if deactivated_count == 0:
            all_plans = []
            for plan in plans:
                all_plans.append({
                    "plan_id": plan.get('plan_id'),
                    "action_name": plan.get('action', {}).get('name', ''),
                    "status": plan.get('status', '')
                })
            
            return {
                "success": False,
                "message": f"No active plans found matching '{criteria}'. Available plans:",
                "deactivated_count": 0,
                "available_plans": all_plans
            }
        
        return {
            "success": True,
            "message": f"Deactivated {deactivated_count} plans matching '{criteria}'",
            "deactivated_count": deactivated_count,
            "deactivated_plans": matching_plans
        }
            
    except Exception as e:
        return {"success": False, "error": f"Error deactivating plans: {str(e)}"}

@tool
def list_all_plans() -> dict:
    """List all plans with their action names, descriptions, and targets."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        plans_result = doc_manager.get_user_plans(user_id)
        if not plans_result['success'] or not plans_result['data']:
            return {"success": False, "error": "No plans found"}
        
        plans = plans_result['data']
        plans_list = []
        
        for i, plan in enumerate(plans):
            plans_list.append({
                "index": i,
                "plan_id": plan.get('plan_id', 'N/A'),
                "action_name": plan.get('action', {}).get('name', 'N/A'),
                "description": plan.get('action', {}).get('description', 'N/A'),
                "target": plan.get('target', 'N/A'),
                "status": plan.get('status', 'N/A')
            })
        
        return {
            "success": True,
            "total_plans": len(plans_list),
            "plans": plans_list
        }
    except Exception as e:
        return {"success": False, "error": f"Error listing plans: {str(e)}"}

@tool
def verify_plan_deletion(criteria: str) -> dict:
    """Verify if plans matching criteria were actually deleted by checking current state."""
    try:
        from document_manager import DocumentManager
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        
        # Force fresh query from database
        plans_result = doc_manager.get_user_plans(user_id)
        if not plans_result['success']:
            return {"success": False, "error": "Failed to fetch plans"}
        
        plans = plans_result.get('data', [])
        criteria_lower = criteria.lower()
        remaining_matches = []
        
        for plan in plans:
            action_name = plan.get('action', {}).get('name', '')
            description = plan.get('action', {}).get('description', '')
            target = plan.get('target', '')
            
            if (criteria_lower in action_name.lower() or 
                criteria_lower in description.lower() or 
                criteria_lower in target.lower()):
                
                remaining_matches.append({
                    "plan_id": plan.get('plan_id'),
                    "action_name": action_name,
                    "status": plan.get('status', 'unknown')
                })
        
        return {
            "success": True,
            "criteria": criteria,
            "total_plans": len(plans),
            "matching_plans_remaining": len(remaining_matches),
            "remaining_matches": remaining_matches,
            "message": f"Found {len(remaining_matches)} plans still matching '{criteria}'"
        }
            
    except Exception as e:
        return {"success": False, "error": f"Error verifying deletion: {str(e)}"}

def get_plan_tools():
    """Get all plan management tools"""
    return [
        delete_plans_by_criteria,
        delete_plans_by_ids,
        deactivate_plans_by_criteria,
        list_all_plans,
        verify_plan_deletion
    ]