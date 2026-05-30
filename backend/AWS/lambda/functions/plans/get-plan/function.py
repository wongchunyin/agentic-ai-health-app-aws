import json
import logging
from typing import Dict, Any

# Import from layers
try:
    from message_helper import MsgHelper
    from document_manager import DocumentManager
    from config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from document_manager import DocumentManager
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from config import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        logger.info(f"Event received: {json.dumps(event)}")
        msg_helper = MsgHelper()
       
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)

        # Get plan_id from path parameters (optional)
        path_params = event.get('pathParameters')
        plan_id = path_params.get('plan_id') if path_params else None
        
        # Check for query parameter to get all plans
        query_params = event.get('queryStringParameters') or {}
        get_all = query_params.get('all') == 'true'
        
        logger.info(f"Path parameters: {path_params}, plan_id: {plan_id}, get_all: {get_all}")

        # Initialize DocumentManager
        doc_manager = DocumentManager()
        
        if plan_id:
            # Get specific plan
            result = doc_manager.get_plan(user_id, plan_id)
            if result['success']:
                return msg_helper.success_response({
                    'message': "Plan retrieved successfully",
                    'plan': result['data']
                })
            else:
                return msg_helper.error_response(result.get('error', 'Plan not found'), 404)
        elif get_all:
            # Get all plans for user (via query parameter)
            result = doc_manager.get_multiple_plans(user_id)
            if result['success']:
                return msg_helper.success_response({
                    'message': "Plans retrieved successfully",
                    'plans': result['data']
                })
            else:
                return msg_helper.error_response(result.get('error', 'Failed to retrieve plans'), 500)
        else:
            # Default to getting all plans if no plan_id and no query param
            result = doc_manager.get_multiple_plans(user_id)
            if result['success']:
                return msg_helper.success_response({
                    'message': "Plans retrieved successfully",
                    'plans': result['data']
                })
            else:
                return msg_helper.error_response(result.get('error', 'Failed to retrieve plans'), 500)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)