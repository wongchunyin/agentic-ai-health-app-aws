import json
from datetime import datetime
from message_helper import MsgHelper
from document_manager import DocumentManager
from config import config

def lambda_handler(event, context):
    try:
        msgHelper = MsgHelper()
        # Extract user ID from JWT token
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Get plan_id from path parameters
        plan_id = event['pathParameters']['plan_id']
        
        # Parse request body
        body = json.loads(event['body'])
        
        # Initialize document manager
        doc_manager = DocumentManager()
        
        plan_data = None
        
        # Handle status update if present
        if 'status' in body:
            result = doc_manager.update_plan_status(user_id, plan_id, body['status'])
            if not result['success']:
                return msgHelper.error_response(result['error'], 400)
        
        # Handle content updates if present
        content_fields = ['action', 'target', 'context', 'time']
        has_content_updates = any(field in body for field in content_fields)
        
        if has_content_updates:
            # Use the new update_plan method that returns plan_data
            update_data = {}
            for field in content_fields:
                if field in body:
                    update_data[field] = body[field]
            
            result = doc_manager.update_plan(user_id, plan_id, update_data)
            if not result['success']:
                return msgHelper.error_response(result['error'], 400)
            
            plan_data = result['plan_data']
            
            # Update schedule task if time data changed
            if 'time' in body:
                doc_manager._update_schedule_task_from_plan(user_id, plan_id, body['time'])
        
        # Return success only after all updates are completed
        response_data = {
            "message": "Plan updated successfully",
            "plan_id": plan_id
        }
        
        if plan_data:
            response_data["plan_data"] = plan_data
            
        return msgHelper.success_response(response_data)
        
    except Exception as e:
        print(f"Error updating plan: {str(e)}")
        return msgHelper.error_response(f"Internal server error: {str(e)}", 500)