import json
import logging
from typing import Dict, Any

# Import from layers
try:
    from document_manager import DocumentManager
    from message_helper import MsgHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/livewell-core/python'))
    from document_manager import DocumentManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to retrieve user profile from S3
    """
    msg_helper = MsgHelper()
     
    try:
        # Get user_id from Cognito authorizer claims
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return msg_helper.error_response('User not authenticated', 401, methods='GET,POST,PUT,OPTIONS')

        # Initialize DocumentManager
        doc_manager = DocumentManager()
        
        # Get profile document  
        result = doc_manager.get_user_profile(user_id)
        
        if result['success']:
            return msg_helper.success_response(data={
                'message': "Profile retrieved successfully",
                'profile': result['data']
            }, methods='GET,POST,PUT,OPTIONS')
        else:
            return msg_helper.error_response(result.get('error', 'Profile not found'), 404, methods='GET,POST,PUT,OPTIONS')
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500, methods='GET,POST,PUT,OPTIONS')