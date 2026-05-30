import json
import logging
from typing import Dict, Any

# Import from layers
try:
    from document_manager import DocumentManager
    from schemas import Profile
    from message_helper import MsgHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/livewell-core/python'))
    from document_manager import DocumentManager
    from schemas import Profile

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to create user profile (POST method)
    """
    msg_helper = MsgHelper()
    
    try:
        # Get user_id from Cognito authorizer claims
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return msg_helper.error_response('User not authenticated', 401, methods='POST,OPTIONS')
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Add user_id from Cognito claims
        body['user_id'] = user_id
        
        # Create Profile object with validation
        profile = Profile(**body)
        
        # Initialize DocumentManager
        doc_manager = DocumentManager()
        
        # Create profile
        result = doc_manager.create_profile(profile)
        
        if result['success']:
            return msg_helper.success_response(data={
                'message': "Profile created successfully",
                'profile': result.get('profile', {})
            }, methods='POST,OPTIONS')
        else:
            return msg_helper.error_response(result.get('error', 'Failed to create profile'), 400, methods='POST,OPTIONS')
            
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return msg_helper.error_response(f'Validation error: {str(e)}', 400, methods='POST,OPTIONS')
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500, methods='POST,OPTIONS')