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

        # Get plan_id from query parameters
        query_params = event.get('queryStringParameters') or {}
        plan_id = query_params.get('plan_id')
        
        if not plan_id:
            return msg_helper.error_response('plan_id is required', 400)

        # Initialize DocumentManager
        doc_manager = DocumentManager()
        
        # Increment activity count
        result = doc_manager.increment_activity_done(user_id, plan_id)
        if result['success']:
            return msg_helper.success_response({
                'message': "Activity count incremented successfully",
                'plan_id': plan_id
            })
        else:
            return msg_helper.error_response(result.get('error', 'Failed to increment activity count'), 500)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)