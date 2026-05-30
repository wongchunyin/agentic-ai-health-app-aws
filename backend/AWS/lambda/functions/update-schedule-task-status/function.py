import json
import logging
from document_manager import DocumentManager
from message_helper import MsgHelper, handle_cors

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@handle_cors
def lambda_handler(event, context):
    """Update schedule task status to ACTIVE or INACTIVE"""
    msg_helper = MsgHelper()
    
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Extract user_id from id_token
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return msg_helper.error_response('User not authenticated', 401)
        
        # Extract required parameters
        plan_id = body.get('plan_id')
        status = body.get('status')
        
        # Validate required parameters
        
        if not plan_id:
            return msg_helper.error_response('plan_id is required', 400)
        
        if not status:
            return msg_helper.error_response('status is required', 400)
        
        # Initialize document manager
        doc_manager = DocumentManager()
        
        # Update schedule task status
        result = doc_manager.update_schedule_task_status(user_id, plan_id, status)
        
        if result['success']:
            return msg_helper.success_response({
                'message': 'Schedule task status updated successfully',
                'data': result
            })
        else:
            return msg_helper.error_response(result['error'], 400)
    
    except Exception as e:
        logger.error(f"Error updating schedule task status: {str(e)}")
        return msg_helper.error_response('Internal server error', 500)